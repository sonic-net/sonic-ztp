#!/usr/bin/python3
'''
Copyright 2019 Broadcom. The term "Broadcom" refers to Broadcom Inc.
and/or its subsidiaries.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import sys
import os
import time
import signal
import subprocess
import errno
import argparse
import re
import json
import traceback
from natsort import natsorted
from urllib.parse import urlparse
from ztp.ZTPSections import ZTPJson
import ztp.ZTPCfg
from ztp.Downloader import Downloader
from ztp.Logger import logger
from ztp.ZTPLib import getTimestamp, runCommand, runcmd_pids 
from ztp.ZTPLib import getField, getCfg, validateZtpCfg, updateActivity, systemReboot
from swsscommon.swsscommon import ConfigDBConnector, SonicV2Connector

def check_pid(pid):
    ## Check For the existence of a unix pid
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True

def signal_handler(signum, frame):
    '''!
    This signal handler is called on SIGTERM or SIGINT
    '''
    logger.warning('Received terminate signal. Shutting down.')
    updateActivity('Received terminate signal. Shutting down.')
    # Wait for some time
    count = getCfg('sighandler-wait-interval')
    while count > 0:
        done = True
        for pid in runcmd_pids:
            if check_pid(pid):
                done = False
                try:
                    (wpid, status) = os.waitpid(pid, os.WNOHANG)
                    if wpid == pid:
                        print('Process pid %d returned with status %d.' % (pid, status))
                except OSError as v:
                    print('pid %d : %s' % (pid, str(v)))
        if done:
            break
        time.sleep(1)
        count -= 1

    # Kill any process which might still be running
    for pid in runcmd_pids:
        if check_pid(pid):
            print('Process %d still alive, send kill signal.' % (pid) )
            os.kill(pid, signal.SIGKILL)

    sys.exit(0)

class ZTPEngine():
    '''!
    \brief This class performs core functions of ZTP service.
    '''
    def __init__(self):
        ## Flag to indicate if configuration ztp restart is requested
        self.__ztp_restart = False

        ## start time of ZTP engine
        self.__ztp_engine_start_time = None

        ## Flag to indicate if ZTP configuration has been loaded
        self.__ztp_profile_loaded = False

        ## Run ZTP engine in unit test mode
        self.test_mode = False

        ## Flag to determine if interfaces link scan has to be enabled or not
        self.__link_scan_enabled = None

        ## Interface on which ZTP information has been discovered using DHCP
        self.__ztp_interface = None

        ## ZTP JSON object
        self.objztpJson = None

        ## Flag to indicate reboot
        self.reboot_on_completion = False

        ## Interfaces state table
        self.__intf_state = dict()

        ## Redis DB connectors
        self.configDB = None
        self.applDB   = None

    def __connect_to_redis(self):
        '''!
        Establishes connection to the redis DB
           @return  False - If connection to the redis DB failed
                    True  - If connection to the redis DB is successful
        '''
        # Connect to ConfigDB
        try:
            if self.configDB is None:
                self.configDB = ConfigDBConnector()
                self.configDB.connect()
        except:
            self.configDB = None
            return False

        # Connect to AppDB
        try:
            if self.applDB is None:
                self.applDB = SonicV2Connector()
                self.applDB.connect(self.applDB.APPL_DB)
        except:
            self.applDB = None
            return False
        return True

    def __detect_intf_state(self):
        '''!
        Identifies all the interfaces on which ZTP discovery needs to be performed.
        Link state of each identified interface is checked and stored in a dictionary
        for reference.

           @return  True   - If an interface moved from link down to link up state
                    False  - If no interface transitions have been observed
        '''
        link_up_detected = False
        intf_data = os.listdir('/sys/class/net')
        if getCfg('feat-inband'):
            r_intf = re.compile("Ethernet.*|eth.*")
        else:
            r_intf = re.compile("eth.*")
        intf_list = list(filter(r_intf.match, intf_data))
        for intf in natsorted(intf_list):
            try:
                if intf[0:3] == 'eth':
                    fh = open('/sys/class/net/{}/operstate'.format(intf), 'r')
                    operstate = fh.readline().strip().lower()
                    fh.close()
                else:
                    if self.applDB.exists(self.applDB.APPL_DB, 'PORT_TABLE:'+intf):
                        port_entry = self.applDB.get_all(self.applDB.APPL_DB, 'PORT_TABLE:'+intf)
                        operstate = port_entry.get('oper_status').lower()
                    else:
                        operstate = 'down'
            except:
                operstate = 'down'
            if ((self.__intf_state.get(intf) is None) or \
                (self.__intf_state.get(intf).get('operstate') != operstate)) and \
                operstate == 'up':
                link_up_detected = True
                logger.info('Link up detected for interface %s' % intf)
            if self.__intf_state.get(intf) is None:
                self.__intf_state[intf] = dict()
            self.__intf_state[intf]['operstate'] = operstate

        # Weed out any stale interfaces that may exist when an expanded port is joined back
        intf_snapshot = list(self.__intf_state.keys())
        for intf in intf_snapshot:
            if intf not in intf_list:
                del self.__intf_state[intf]

        return link_up_detected

    def __is_ztp_profile_active(self):
        '''!
        Checks if the ZTP configuration profile is loaded as the switch running
        configuration and is active

           @return  False - ZTP configuration profile is not active
                    True  - ZTP configuration profile is active
        '''
        profile_active = False
        if self.__connect_to_redis():
            # Check if ZTP configuration is active
            data = self.configDB.get_entry("ZTP", "mode")
            if data is not None and data.get("profile") is not None:
                if data.get("profile") == 'active':
                    profile_active = True
        return profile_active

    def __link_scan(self):
        '''!
        Scan all in-band interface's operational status to detect a link up event
           @return  False - If a link scan did not detect at least one switch port link up event
                    True  - If at least one switch port link up event has been detected
        '''

        # Do not attempt link scan when in test mode
        if self.test_mode:
            return False

        if self.__connect_to_redis() is False:
            self.__link_scan_enabled = None
            return False

        if self.__link_scan_enabled is None:
            # Check if ZTP configuration is active
            if self.__is_ztp_profile_active():
                self.__link_scan_enabled = 'True'
            else:
                self.__link_scan_enabled = 'False'

        if self.__link_scan_enabled == 'False':
            return False

        # Populate data of all ztp eligible interfaces
        link_scan_result = self.__detect_intf_state()
        return link_scan_result

    def __cleanup_dhcp_leases(self):

        # Use ZTP interface used to obtain provisioning information
        runCommand('rm -f /var/lib/dhcp/dhclient*.eth0.leases', capture_stdout=False)
        if getCfg('feat-inband'):
            runCommand('rm -f /var/lib/dhcp/dhclient*.Ethernet*.leases', capture_stdout=False)

    def __removeZTPProfile(self):
        '''!
         If ZTP configuration profile is operational, remove ZTP configuration profile and load
         startup configuration file. If there is no startup configuration file,
         load factory default configuration.
        '''

        # Do not attempt to remove ZTP configuration if working in unit test mode
        if self.test_mode:
            return

        # Remove ZTP configuration profile if loaded
        updateActivity('Verifying configuration')

        # Use a fallback default configuration if configured to
        _config_fallback = ''
        if (self.objztpJson is not None and (self.objztpJson['status'] == 'FAILED' or self.objztpJson['status'] == 'SUCCESS') \
            and self.objztpJson['config-fallback']) or \
           (self.objztpJson is None and getCfg('config-fallback') is True):
            _config_fallback = ' config-fallback'

        # Execute profile removal command with appropriate options
        rc = runCommand(getCfg('ztp-lib-dir')+'/ztp-profile.sh remove' + _config_fallback, capture_stdout=False)

        # Remove ZTP configuration startup-config
        if os.path.isfile(getCfg('config-db-json')) is True:
            try:
                config_db = None
                with open(getCfg('config-db-json')) as json_file:
                    config_db = json.load(json_file)
                    json_file.close()
                if config_db is not None and config_db.get('ZTP'):
                    logger.info("Deleting ZTP configuration saved in '%s'." %(getCfg('config-db-json')))
                    del config_db['ZTP']
                    with open(getCfg('config-db-json'), 'w') as json_file:
                        json.dump(config_db, json_file, indent=4)
                        json_file.close()
            except Exception as e:
                logger.error("Exception [%s] encountered while verifying '%s'." %(str(e), getCfg('config-db-json')))

        self.__ztp_profile_loaded = False

    def __loadZTPProfile(self, event):
        '''!
         Load ZTP configuration profile if there is no saved configuration file.
         This establishes connectivity to all interfaces and starts DHCP discovery.
           @return  False - If ZTP configuration profile is not loaded
                    True  - If ZTP configuration profile is loaded
        '''
        # Do not attempt to install ZTP configuration if working in unit test mode
        if self.test_mode:
            return False

        if self.__ztp_profile_loaded is False:
            updateActivity('Checking running configuration')
            logger.info('Checking running configuration to load ZTP configuration profile.')
            cmd = getCfg('ztp-lib-dir')+'/ztp-profile.sh install ' + event
            # When performing ZTP discovery, force load ZTP profile. When
            # ZTP is resuming previous session, use configuration already loaded during
            # config-setup
            rc = runCommand(cmd, capture_stdout=False)
            self.__ztp_profile_loaded = True
            return True
        return False

    def __createProvScriptJson(self):
        '''!
         Create ZTP JSON data to execute provisioning script specified by DHCP Option 239 URL.
        '''

        json_data='{"ztp": {"provisioning-script":{"plugin":{"url":"file://'+ getCfg('provisioning-script') +'","ignore-section-data":true}}\
                   ,"restart-ztp-no-config":false}}'
        f = open(getCfg('ztp-json'), 'w')
        f.write(json_data)
        f.close

    def __createGraphserviceJson(self):
        '''!
         Create ZTP JSON data to load graph file specified by DHCP Option 225 URL. Also
         includes ACL JSON file if specified by DHCP Option 226.
        '''

        # Verify that graph file can be downloaded
        if self.__downloadURL(getCfg('graph-url'), '/tmp/test_minigraph.xml') is False:
            return False
        else:
            # Clean up
            os.remove('/tmp/test_minigraph.xml')

        # Verify that acl json file can be downloaded
        if os.path.isfile(getCfg('acl-url')):
            if self.__downloadURL(getCfg('acl-url'), '/tmp/test_acl.json') is False:
                return False
            else:
                # Clean up
                os.remove('/tmp/test_acl.json')

        # Read the url file and identify the URL to be downloaded
        f = open(getCfg('graph-url'), 'r')
        graph_url_str = f.readline().strip()
        f.close()

        acl_url_str = None
        if os.path.isfile(getCfg('acl-url')):
            f = open(getCfg('acl-url'), 'r')
            acl_url_str = f.readline().strip()
            f.close()
        json_data='{"ztp":{"graphservice": { "minigraph-url" : { "url":"' + graph_url_str + '"}'
        if acl_url_str is not None and len(acl_url_str) != 0:
            json_data = json_data + ', "acl-url" : { "url":"' + acl_url_str + '"}'
        json_data = json_data + '}, "restart-ztp-no-config":false} }'
        f = open(getCfg('ztp-json'), 'w')
        f.write(json_data)
        f.close
        return True


    def __rebootAction(self, section, delayed_reboot=False):
        '''!
         Perform system reboot if reboot-on-success or reboot-on-failure is defined in the
         configuration section data.

         @param section (dict) Configuration section data containing status and reboot-on flags

        '''

        # Obtain section status
        status = section.get('status')

        # Check if flag is set to reboot on SUCCESS and status is SUCCESS as well
        if getField(section, 'reboot-on-success', bool, False) is True and status == 'SUCCESS':
            logger.warning('ZTP is rebooting the device as reboot-on-success flag is set.')
            updateActivity('System reboot requested on success')
            if self.test_mode and delayed_reboot == False:
                sys.exit(0)
            else:
                if delayed_reboot:
                    self.reboot_on_completion = True
                else:
                    systemReboot()

        # Check if flag is set to reboot on FAIL and status is FAILED as well
        if getField(section, 'reboot-on-failure', bool, False) is True and status == 'FAILED':
            logger.warning('ZTP is rebooting the device as reboot-on-failure flag is set.')
            updateActivity('System reboot requested on failure')
            if self.test_mode and delayed_reboot == False:
                sys.exit(0)
            else:
                if delayed_reboot:
                    self.reboot_on_completion = True
                else:
                    systemReboot()

    def __evalZTPResult(self):
        '''!
         Determines the final result of ZTP after processing all configuration sections and
         their results. Als performs system reboot if reboot-on flag is set

         ZTP result is determined as SUCCESS if - Configuration section(s) status is SUCCESS
                                                or (configuration section(s) status is FAILED and
                                                    configuration section(s) ignore-result is True)
                                                or ZTP ignore-result is True

         Disabled Configuration sections are ignored.
        '''

        updateActivity('Evaluating ZTP result')
        # Check if overall ZTP ignore-result flag is set
        if self.objztpJson['ignore-result']:
            self.objztpJson['status'] = 'SUCCESS'
            logger.info('ZTP result is marked as SUCCESS at %s. ZTP ignore-result flag is set.' % self.objztpJson['timestamp'])

        else:
            # Look through individual configuration sections
            for sec in self.objztpJson.section_names:
                # Retrieve section data
                section = self.objztpJson.ztpDict.get(sec)
                logger.info('Checking configuration section %s result: %s, ignore-result: %r.' % \
                              (sec, section.get('status'), section.get('ignore-result')))
                # Check if configuration section has failed and ignore-result flag is not set
                if section.get('status') == 'FAILED' and section.get('ignore-result') is False:
                    # Mark ZTP as failed and bail out
                    self.objztpJson['error'] = '%s FAILED' % sec
                    self.objztpJson['status'] = 'FAILED'
                    logger.info('ZTP failed at %s as configuration section %s FAILED.' % (self.objztpJson['timestamp'], sec))
                    return

        # Mark ZTP as SUCCESS
        self.objztpJson['status'] = 'SUCCESS'
        logger.info('ZTP successfully completed at %s.' % self.objztpJson['timestamp'])

        # Check reboot on result flags and take action
        self.__rebootAction(self.objztpJson.ztpDict, delayed_reboot=True)

    def __processConfigSections(self):
        '''!
         Process and execute individual configuration sections defined in ZTP JSON. Plugin for each
         configuration section is resolved and executed. Configuration section data is provided as
         command line argument to the plugin. Each and every section is processed before this function
         returns.

        '''

        # Obtain a copy of the list of configuration sections
        section_names = list(self.objztpJson.section_names)

        # set temporary flags
        abort = False
        sort = True

        logger.debug('Processing configuration sections: %s' % ', '.join(section_names))
        # Loop through each sections till all of them are processed
        while section_names and abort is False:
            # Take a fresh sorted list to begin with and if any changes happen to it while processing
            if sort:
                sorted_list = sorted(section_names)
                sort = False
            # Loop through configuration section in a sorted order
            for sec in sorted_list:
                # Retrieve configuration section data
                section = self.objztpJson.ztpDict.get(sec)
                try:
                    # Retrieve individual section's progress
                    sec_status = section.get('status')
                    if sec_status == 'BOOT' or sec_status == 'SUSPEND':
                        # Mark section status as in progress
                        self.objztpJson.updateStatus(section, 'IN-PROGRESS')
                        if section.get('start-timestamp') is None:
                            section['start-timestamp'] = section['timestamp']
                            self.objztpJson.objJson.writeJson()
                        logger.info('Processing configuration section %s at %s.' % (sec, section['timestamp']))
                    elif sec_status != 'IN-PROGRESS':
                        # Skip completed sections
                        logger.debug('Removing section %s from list. Status %s.' % (sec, sec_status))
                        section_names.remove(sec)
                        # set flag to sort the configuration sections list again
                        sort = True
                        # Ignore disabled configuration sections
                        if sec_status == 'DISABLED':
                            logger.info('Configuration section %s skipped as its status is set to DISABLED.' % sec)
                        continue
                    updateActivity('Processing configuration section %s' % sec)
                    # Get the appropriate plugin to be used for this configuration section
                    plugin = self.objztpJson.plugin(sec)
                    # Get the location of this configuration section's input data parsed from the input ZTP JSON file
                    plugin_input = getCfg('ztp-tmp-persistent') + '/' + sec + '/' + getCfg('section-input-file')
                    # Initialize result flag to FAILED
                    finalResult = 'FAILED'
                    rc = 1
                    # Check if plugin could not be resolved
                    if plugin is None:
                        logger.error('Unable to resolve plugin to be used for configuration section %s. Marking it as FAILED.' % sec)
                        section['error'] = 'Unable to find or download requested plugin'
                    elif os.path.isfile(plugin) and os.path.isfile(plugin_input):
                        plugin_args = self.objztpJson.pluginArgs(sec)
                        plugin_data = section.get('plugin')

                        # Determine if shell has to be used to execute plugin
                        _shell = getField(plugin_data, 'shell', bool, False)

                        # Determine if user specified umask has to be used to execute plugin
                        try:
                            _umask = int(getField(plugin_data, 'umask', str, getCfg("umask")), 8)
                        except Exception as e:
                            logger.error('Exception[%s] encountered while reading umask to execute the plugin for %s. Using default value -1.' % (str(e), sec))
                            _umask = -1

                        # Construct the full plugin command string along with arguments
                        plugin_cmd = plugin
                        if plugin_args is not None:
                            plugin_cmd = plugin_cmd + ' ' + plugin_args

                        # A plugin has been resolved and its input configuration section data as well
                        logger.debug('Executing plugin %s.' % (plugin_cmd))
                        # Execute identified plugin
                        rc = runCommand(plugin_cmd, capture_stdout=False, use_shell=_shell, umask=_umask)

                        logger.debug('Plugin %s exit code = %d.' % (plugin_cmd, rc))
                        # Compare plugin exit code
                        if rc == 0:
                            finalResult = 'SUCCESS'
                        elif section.get('suspend-exit-code') is not None and section.get('suspend-exit-code') == rc:
                            finalResult = 'SUSPEND'
                        else:
                            finalResult = 'FAILED'
                except Exception as e:
                    logger.debug('Exception [%s] encountered for configuration section %s.' % (str(e), sec))
                    logger.info('Exception encountered while processing configuration section %s. Marking it as FAILED.' %  sec)
                    section['error'] = 'Exception [%s] encountered while executing the plugin' % (str(e))
                    finalResult = 'FAILED'

                # Update this configuration section's result in ztp json file
                logger.info('Processed Configuration section %s with result %s, exit code (%d) at %s.' % (sec, finalResult, rc, section['timestamp']))
                if finalResult == 'FAILED' and section.get('error') is None:
                    section['error'] = 'Plugin failed'
                section['exit-code'] = rc
                self.objztpJson.updateStatus(section, finalResult)

                # Check if abort ZTP on failure flag is set
                if getField(section, 'halt-on-failure', bool, False) is True and finalResult == 'FAILED':
                    logger.info('Halting ZTP as Configuration section %s FAILED and halt-on-failure flag is set.' % sec)
                    abort = True
                    break

                # Check reboot on result flags
                self.__rebootAction(section)

    def __processZTPJson(self):
        '''!
         Process ZTP JSON file downloaded using URL provided by DHCP Option 67, DHCPv6 Option 59 or
         local ZTP JSON file.

        '''
        logger.debug('Starting to process ZTP JSON file %s.' % self.json_src)
        updateActivity('Processing ZTP JSON file %s' % self.json_src)
        try:
            # Read provided ZTP JSON file and load it
            self.objztpJson = ZTPJson(self.json_src, getCfg('ztp-json'))
        except ValueError as e:
            logger.error('Exception [%s] occured while processing ZTP JSON file %s.' % (str(e), self.json_src))
            logger.error('ZTP JSON file %s processing failed.' % (self.json_src))
            try:
                os.remove(getCfg('ztp-json'))
                if os.path.isfile(getCfg('ztp-json-shadow')):
                    os.remove(getCfg('ztp-json-shadow'))
            except OSError as v:
                if v.errno != errno.ENOENT:
                    logger.warning('Exception [%s] encountered while deleting ZTP JSON file %s.' % (str(v), getCfg('ztp-json')))
                    raise
            self.objztpJson = None
            # Restart networking after a wait time to discover new provisioning data
            if getCfg('restart-ztp-on-invalid-data'):
                return ("restart", "Invalid provisioning data processed")
            else:
                return ("stop", "Invalid provisioning data processed")

        if self.objztpJson['ztp-json-source'] is None:
            self.objztpJson['ztp-json-source'] = self.ztp_mode

        # Check if ZTP process has already completed. If not mark start of ZTP.
        if self.objztpJson['status'] == 'BOOT':
            self.objztpJson['status'] = 'IN-PROGRESS'
            if self.objztpJson['start-timestamp'] is None:
                self.objztpJson['start-timestamp'] = self.__ztp_engine_start_time
                self.objztpJson.objJson.writeJson()
        elif self.objztpJson['status'] != 'IN-PROGRESS':
            # Re-start ZTP if requested
            if getCfg('monitor-startup-config') is True and self.__ztp_restart:
                self.__ztp_restart = False
                # Discover new ZTP data after deleting historic ZTP data
                logger.info("ZTP restart requested. Deleting previous ZTP session JSON data.")
                os.remove(getCfg('ztp-json'))
                if os.path.isfile(getCfg('ztp-json-shadow')):
                    os.remove(getCfg('ztp-json-shadow'))
                self.objztpJson = None
                return ("retry", "ZTP restart requested")
            else:
                # ZTP was successfully completed in previous session. No need to proceed, return and exit service.
                logger.info("ZTP already completed with result %s at %s." % (self.objztpJson['status'], self.objztpJson['timestamp']))
                return ("stop", "ZTP completed")

        logger.info('Starting ZTP using JSON file %s at %s.' % (self.json_src, self.objztpJson['timestamp']))

        # Initialize connectivity if not done already
        self.__loadZTPProfile("resume")

        # Process available configuration sections in ZTP JSON
        self.__processConfigSections()

        # Determine ZTP result
        self.__evalZTPResult()

        # Check restart ZTP condition
        # ZTP result is failed and restart-ztp-on-failure is set  or
        _restart_ztp_on_failure = (self.objztpJson['status'] == 'FAILED' and \
                        self.objztpJson['restart-ztp-on-failure'] == True)

        # ZTP completed and no startup-config is found, restart-ztp-no-config and config-fallback is not set
        _restart_ztp_missing_config = ( (self.objztpJson['status'] == 'SUCCESS' or self.objztpJson['status'] == 'FAILED') and \
                           self.objztpJson['restart-ztp-no-config'] == True and \
                           self.objztpJson['config-fallback'] == False and
                           os.path.isfile(getCfg('config-db-json')) is False )

        # Mark ZTP for restart
        if _restart_ztp_missing_config or _restart_ztp_on_failure:
            os.remove(getCfg('ztp-json'))
            if os.path.isfile(getCfg('ztp-json-shadow')):
               os.remove(getCfg('ztp-json-shadow'))
            self.objztpJson = None
            # Remove startup-config file to obtain a new one through ZTP
            if getCfg('monitor-startup-config') is True and os.path.isfile(getCfg('config-db-json')):
                os.remove(getCfg('config-db-json'))
            if _restart_ztp_missing_config:
                return ("restart", "ZTP completed but startup configuration '%s' not found" % (getCfg('config-db-json')))
            elif _restart_ztp_on_failure:
                return ("restart", "ZTP completed with FAILED status")

        return ("stop", "ZTP completed")

    def __updateZTPMode(self, mode, src_file):
        '''!
         Identify source of ZTP JSON file. Store ZTP mode of operation.

         @param mode (str) Indicates how provisioning data has been provided to the switch
                               - Local file
                               - DHCP Option 67
                               - DHCPv6 Option 59
                               - DHCP Option 239
                               - DHCPv6 Option 239
                               - Minigraph URL Option 225, ACL URL Option 226

         @param src_file (str) File used as ZTP JSON file source

         @return          Always returns True

        '''
        logger.debug('Set ZTP mode as %s and provisioning data is %s.' %  (mode, src_file))
        dhcp_list = ['dhcp-opt67', 'dhcp6-opt59', 'dhcp-opt239', 'dhcp6-opt239', 'dhcp-opt225-graph-url']
        self.json_src = src_file
        self.ztp_mode = mode
        if self.ztp_mode == 'local-fs':
            self.ztp_mode = self.ztp_mode + ' (' + src_file +')'
        elif self.ztp_mode in dhcp_list and self.__ztp_interface is not None:
            self.ztp_mode = self.ztp_mode + ' (' + self.__ztp_interface +')'
        return True

    def __read_ztp_interface(self):
        intf_file = getCfg('ztp-run-dir') + '/ztp.lock/interface'
        if os.path.isfile(intf_file):
            f = open(intf_file, 'r')
            try:
                self.__ztp_interface = f.readline().strip().split(':')[1]
            except:
                self.__ztp_interface = None
                pass
            f.close()

    def __downloadURL(self, url_file, dst_file, url_prefix=None):
        '''!
         Helper API to read url information from a file, download the
         file using the url and store contents as a dst_file.

         @param url_file (str) File containing URL to be downloaded
         @param dst_file (str) Destination file to be used
         @param url_prefix (str) Optional string to be prepended to url

         @return   True - If url_file was successfully downloaded
                   False - Failed to download url_file

        '''

        logger.debug('Downloading provided URL %s and saving as %s.' % (url_file, dst_file))
        try:
            # Read the url file and identify the URL to be downloaded
            f = open(url_file, 'r')
            url_str = f.readline().strip()
            f.close()

            res = urlparse(url_str)
            if res is None or res.scheme == '':
                # Use passed url_prefix to construct final URL
                if url_prefix is not None:
                    url_str = url_prefix + url_str
                    if urlparse(url_str) is None:
                        logger.error('Failed to download provided URL %s, malformed url.' % (url_str))
                        return False
                else:
                    logger.error('Failed to download provided URL %s, malformed url.' % (url_str))
                    return False

            # Create a downloader object using source and destination information
            updateActivity('Downloading provisioning data from %s to %s' % (url_str, dst_file))
            logger.info('Downloading provisioning data from %s to %s' % (url_str, dst_file))
            objDownloader = Downloader(url_str, dst_file)
            # Initiate download
            rc, fname = objDownloader.getUrl()
            # Check download result
            if rc == 0 and fname is not None and os.path.isfile(dst_file):
                # Get the interface on which ZTP data was received
                self.__read_ztp_interface()
                return True
            else:
                logger.error('Failed to download provided URL %s returncode=%d.' % (url_str, rc))
                return False
        except (IOError, OSError) as e:
            logger.error('Exception [%s] encountered during download of provided URL %s.' % (str(e), url_str))
            return False

    def __discover(self):
        '''!
         ZTP data discover logic. Following is the order of precedence followed:

             Processed or under-process ZTP JSON file
           > ZTP JSON file specified in pre-defined location as part of the image
           > ZTP JSON URL specified via DHCP Option-67
           > ZTP JSON URL specified via DHCPv6 Option-59
           > Simple provisioning script URL specified via DHCP Option-239
           > Simple provisioning script URL specified via DHCPv6 Option-239
           > Minigraph URL and ACL URL specified via DHCP Option 225, 226

           @return  False - If no ZTP data is found or ZTP data could not be downloaded.
                    True  - ZTP data recoginized and ZTP JSON / provisioning script was
                            successfully downloaded. Startup configuration file detected.

        '''

        logger.debug('Start discovery.')
        if os.path.isfile(getCfg('ztp-json')):
            return self.__updateZTPMode('ztp-session', getCfg('ztp-json'))

        if os.path.isfile(getCfg('config-db-json')) and getCfg('monitor-startup-config'):
            self.ztp_mode = 'MANUAL_CONFIG'
            return True

        if os.path.isfile(getCfg('ztp-json-local')):
            return self.__updateZTPMode('local-fs', getCfg('ztp-json-local'))
        if os.path.isfile(getCfg('opt67-url')):
            _tftp_server = None
            _url_prefix = None
            # Check if tftp-server name has been passed
            if os.path.isfile(getCfg('opt66-tftp-server')):
                fh = open(getCfg('opt66-tftp-server'), 'r')
                _tftp_server = fh.readline().strip()
                fh.close()
                if _tftp_server is not None and _tftp_server != '':
                    _url_prefix = 'tftp://' + _tftp_server + '/'
            if self.__downloadURL(getCfg('opt67-url'), getCfg('ztp-json-opt67'), url_prefix=_url_prefix):
                return self.__updateZTPMode('dhcp-opt67', getCfg('ztp-json-opt67'))
        if os.path.isfile(getCfg('opt59-v6-url')):
            if self.__downloadURL(getCfg('opt59-v6-url'), getCfg('ztp-json-opt59')):
                return self.__updateZTPMode('dhcp6-opt59', getCfg('ztp-json-opt59'))
        if os.path.isfile(getCfg('opt239-url')):
            if self.__downloadURL(getCfg('opt239-url'), getCfg('provisioning-script')):
                self.__createProvScriptJson()
                return self.__updateZTPMode('dhcp-opt239', getCfg('ztp-json'))
        if os.path.isfile(getCfg('opt239-v6-url')):
            if self.__downloadURL(getCfg('opt239-v6-url'), getCfg('provisioning-script')):
                self.__createProvScriptJson()
                return self.__updateZTPMode('dhcp6-opt239', getCfg('ztp-json'))
        if os.path.isfile(getCfg('graph-url')):
            if self.__createGraphserviceJson():
                return self.__updateZTPMode('dhcp-opt225-graph-url', getCfg('ztp-json'))
        return False

    def __forceRestartDiscovery(self, msg):
        # Remove existing leases to source new provisioning data
        self.__cleanup_dhcp_leases()
        _msg = '%s. Waiting for %d seconds before restarting ZTP.' % (msg, getCfg('restart-ztp-interval'))
        logger.warning(_msg)
        updateActivity(_msg)
        time.sleep(getCfg('restart-ztp-interval'))
        self.ztp_mode = 'DISCOVERY'
        # Force install of ZTP configuration profile
        self.__ztp_profile_loaded = False
        # Restart link-scan
        self.__intf_state = dict()

    def executeLoop(self, test_mode=False):
        '''!
         ZTP service loop which peforms provisioning data discovery and initiates processing.
        '''

        updateActivity('Initializing')

        # Set testing mode
        self.test_mode = test_mode

        # Check if ZTP is disabled administratively, bail out if disabled
        if getCfg('admin-mode') is False:
            logger.info('ZTP is administratively disabled.')
            self.__removeZTPProfile()
            return

        # Check if ZTP data restart flag is set
        if os.path.isfile(getCfg('ztp-restart-flag')):
            self.__ztp_restart = True
            os.remove(getCfg('ztp-restart-flag'))

        if self.test_mode:
            logger.warning('ZTP service started in test mode with restricted functionality.')
        else:
            logger.info('ZTP service started.')

        self.__ztp_engine_start_time = getTimestamp()
        _start_time = None
        self.ztp_mode = 'DISCOVERY'
        # Main provisioning data discovery loop
        while self.ztp_mode == 'DISCOVERY':
            updateActivity('Discovering provisioning data', overwrite=False)
            try:
                result = self.__discover()
            except Exception as e:
                logger.error("Exception [%s] encountered while running the discovery logic." %(str(e)))
                _exc_type, _exc_value, _exc_traceback = sys.exc_info()
                __tb = traceback.extract_tb(_exc_traceback)
                for l in __tb:
                    logger.debug('  File ' + l[0] + ', line ' + str(l[1]) + ', in ' + str(l[2]))
                    logger.debug('    ' + str(l[3]))
                self.__forceRestartDiscovery("Invalid provisioning data received")
                continue
                                 
            if result:
                if self.ztp_mode == 'MANUAL_CONFIG':
                    logger.info("Configuration file '%s' detected. Shutting down ZTP service." % (getCfg('config-db-json')))
                    break
                elif self.ztp_mode != 'DISCOVERY':
                    (rv, msg) = self.__processZTPJson()
                    if rv == "retry":
                        self.ztp_mode = 'DISCOVERY'
                    elif rv == "restart":
                        self.__forceRestartDiscovery(msg)
                    else:
                        break

            # Initialize in-band interfaces to establish connectivity if not done already
            self.__loadZTPProfile("discovery")
            logger.debug('Provisioning data not found.')

            # Scan for inband interfaces to link up and restart interface connectivity
            if self.__link_scan():
                updateActivity('Restarting network discovery after link scan')
                logger.info('Restarting network discovery after link scan.')
                runCommand('systemctl restart interfaces-config', capture_stdout=False)
                logger.info('Restarted network discovery after link scan.')
                _start_time = time.time()
                continue

            # Start keeping time of last time restart networking was done
            if _start_time is None:
                _start_time = time.time()

            # Check if we have to restart networking
            if (time.time() - _start_time > getCfg('restart-ztp-interval')):
                updateActivity('Restarting network discovery')
                if self.test_mode is False:
                    # Remove existing leases to source new provisioning data
                    self.__cleanup_dhcp_leases()
                    logger.info('Restarting network discovery.')
                    runCommand('systemctl restart interfaces-config', capture_stdout=False)
                    logger.info('Restarted network discovery.')
                _start_time = time.time()
                continue

            # Try after sometime
            time.sleep(getCfg('discovery-interval'))


        # Cleanup installed ZTP configuration profile
        self.__removeZTPProfile()
        if self.reboot_on_completion and self.test_mode == False:
            updateActivity('System reboot requested')
            systemReboot()
        updateActivity('Exiting ZTP server')

def main():
    '''!
     Entry point for ZTP service
    '''
    # Only privileged users can execute this command
    if os.geteuid() != 0:
        sys.exit("Root privileges required for this operation")

    # Add supported arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="Turn on debug level logging")
    parser.add_argument("-t", "--test", action="store_true", default=False, help="Start service in test mode with restricted functionality")
    parser.add_argument("-C", "--config-json", metavar='FILE', default=None, help="ZTP service configuration file")

    # Parse provided arguments
    options = parser.parse_args()

    # Evaluate options
    if options.debug:
        _debug = True
    else:
        _debug = False

    if options.test:
        _test_mode = True
    else:
        _test_mode = False

    # Parse user provided configuration file
    cfg_json = options.config_json

    # Create directories if they do not exist
    dir_objs =  [ 'ztp-tmp-persistent', 'ztp-tmp', 'ztp-cfg-dir', 'ztp-run-dir' ]
    for d in dir_objs:
        loc = getCfg(d)
        if os.path.isdir(loc) is False:
            os.makedirs(loc)

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Read and validate configuration file
    try:

        ztp.ZTPCfg.ztpCfg = ztp.ZTPCfg.ZTPCfg(cfg_json_file=cfg_json)
        validateZtpCfg(ztp.ZTPCfg.ztpCfg)

        # Since we have now the configuration, update the variables in some classes which
        # use the configuration for their values, default or not.

        logger.setLevel(getCfg('log-level', 'INFO'))
        logger.setlogFile(getCfg('log-file'))

        if _debug:
            os.environ["DEBUG"] = "yes"
            logger.setLevel('DEBUG')

        # Read test-mode from configuration file
        if getCfg('test-mode') is True:
            _test_mode = True

    except Exception as e:
        print('Exception [%s] occured while reading ZTP configuration file.' % str(e))
        print('Exiting ZTP service.')
        sys.exit(1)

    # When running in test-mode enable console logging
    if _test_mode and getCfg('feat-console-logging', True):
        logger.setConsoleLogging(True)

    # Start ZTP service
    objEngine = ZTPEngine()

    # Run ZTP service to completion
    objEngine.executeLoop(_test_mode)

    sys.exit(0)

if __name__ == "__main__":
    main()
