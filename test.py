import sys
import os
import json
import fcntl
import select
import time
import stat
import traceback

from ztp.ZTPObjects import URL, DynamicURL
from ztp.ZTPSections import ConfigSection
from ztp.ZTPLib import runCommand, getField, updateActivity, getCfg, systemReboot
from ztp.Logger import logger

class Firmware:

    '''!
    This class handle the 'firmware' plugin
    '''
    # Downloaded file
    __dest_file = None

    def __init__(self, input_file):
        '''!
        Constructor. We only store the json data input file, all the logic is
        managed by the main() method
        @param input_file (str) json data input file to be used by the plugin
        '''
        self.__input_file = input_file

    ## Return the current SONiC image
    def __which_current_image(self):
        (rc, cmd_stdout, cmd_stderr) = runCommand('sonic-installer list')
        if rc != 0:
            return ''
        for l in cmd_stdout:
            if l.find('Current: ') == 0:
                return l[9:]
        return ''

    ## Return the next image which will be used at next boot
    def __which_next_image(self):
        (rc, cmd_stdout, cmd_stderr) = runCommand('sonic-installer list')
        if rc != 0:
            return ''
        for l in cmd_stdout:
            if l.find('Next: ') == 0:
                return l[6:]
        return ''

    ## Retrieve the binary version for a given image file
    def __binary_version(self, fname):
        (rc, cmd_stdout, cmd_stderr) = runCommand('sonic-installer binary-version %s' % (fname))
        if rc != 0 or len(cmd_stdout) != 1:
            return ''
        return cmd_stdout[0]

    ## Return a list of available images (installed)
    def __available_images(self):
        (rc, cmd_stdout, cmd_stderr) = runCommand('sonic-installer list')
        if rc != 0:
            return ''
        index = 0;
        for l in cmd_stdout:
            index += 1
            if l.find('Available:') == 0:
                return cmd_stdout[index:]
        return []

    def __set_default_image(self, image):
        '''!
        Set the default SONiC image.
        @param image (str) SONiC image filename
        '''
        cmd = 'sonic-installer set-default ' + image
        rc = runCommand(cmd, capture_stdout=False)
        if rc != 0:
            self.__bailout('Error (%d) on command \'%s\'' %(rc, cmd))

    def __set_next_boot_image(self, image):
        '''!
        Set the next boot SONiC image.
        @param image (str) SONiC image filename
        '''
        cmd = 'sonic-installer set-next-boot %s' % (image)
        rc = runCommand(cmd, capture_stdout=False)
        if rc != 0:
            self.__bailout('Error (%d) on command \'%s\'' %(rc, cmd))

    def __reboot_switch(self):
        '''!
        Reboot the switch
        '''
        # Do not reboot if reboot-on-success is set in ZTP section data
        # or if skip-reboot is set by user. This allows, user to reboot
        # the switch at a different time.
        if self.__reboot_on_success or self.__skip_reboot:
            logger.info('firmware: Skipped switch reboot as requested.')
            sys.exit(0)
        else:
            logger.info('firmware: Initiating device reboot.')
            # Mark install section as SUCCESS so that it is not executed again after reboot
            with open(getCfg('ztp-json')) as json_file:
                _ztp_dict = json.load(json_file)
                json_file.close()
                install_obj = _ztp_dict.get('ztp').get(self.__section_name).get('install')
                if install_obj is not None:
                    install_obj['status'] = 'SUCCESS'
                    with open(getCfg('ztp-json'), 'w') as outfile:
                         json.dump(_ztp_dict, outfile, indent=4, sort_keys=True)
                         outfile.flush()
                         outfile.close()
            systemReboot()

    def __download_file(self, objURL):
        '''!
        Download a file.
        
        @param objURL URL obj (either static, or dynamic URL)
        '''

        # Download the file using provided URL
        try:
            url_str = objURL.getSource()
            logger.info('firmware: Downloading file \'%s\'.' % url_str)
            updateActivity('firmware: Downloading file \'%s\'.' % url_str)
            (rc, dest_file) = objURL.download()
            if rc != 0 or dest_file is None:
                if dest_file is not None and os.path.isfile(dest_file):
                    os.remove(dest_file)
                self.__bailout('Error (%d) while downloading file \'%s\'' % (rc, url_str))
        except Exception as e:
            self.__bailout(str(e))

        # Check if the downloaded file has failed
        if os.path.isfile(dest_file) is False:
            self.__bailout('Destination file [%s] not found after downloading file \'%s\'' % (dest_file, url_str))
            
        return dest_file

    # Abort the plugin. Return a non zero return code.
    def __bailout(self, text):
        # Clean-up
        if self.__dest_file is not None and os.path.isfile(self.__dest_file):
            os.remove(self.__dest_file)
        logger.error('firmware: Error [%s] encountered while processing.' % (text))
        sys.exit(1)

    def __process_pre_check(self, app_data):
        '''!
        Handle a pre-check script.
        @param app_data (dict) Plugin application data
        @return (int) Exit code of the pre-check script
        '''
        try:
            if app_data.get('dynamic-url') is not None:
                objURL = DynamicURL(app_data.get('dynamic-url'))
            elif app_data.get('url') is not None:
                objURL = URL(app_data.get('url'))
            else:
                self.__bailout('pre-check script missing both "url" and "dynamic_url" source')
        except Exception as e:
            self.__bailout(str(e))

        # Download the file using the requested URL
        logger.info('firmware: Downloading pre-installation check script.')
        self.__dest_file = self.__download_file(objURL)

        # Execute this file
        os.chmod(self.__dest_file, os.stat(self.__dest_file).st_mode | stat.S_IXUSR | stat.S_IXGRP) # nosemgrep
        logger.info('firmware: Executing pre-installation check script.')
        updateActivity('firmware: Executing pre-installation check script')
        rc = runCommand(self.__dest_file, capture_stdout=False)

        # Clean-up
        os.remove(self.__dest_file)

        return rcm
