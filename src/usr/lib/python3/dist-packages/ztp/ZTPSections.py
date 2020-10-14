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

import os
import re
import shutil
from ztp.ZTPLib import isString, getTimestamp, getField, getCfg, updateActivity
from ztp.ZTPObjects import URL, DynamicURL
from ztp.JsonReader import JsonReader
from ztp.Logger import logger

class ConfigSection:
    '''!
    \brief This class is use to store and access input JSON data provided to a configuration section.
    '''
    def updateStatus(self, obj, status):
        '''!
         Update status of configuration section. Also update the timestamp indicating date/time when it is updated. The changes
         are also saved to the JSON file on disk which corresponds to the configuration section.

         @param status (str) Value to be stored as status

        '''
        if isinstance(obj, dict) and isString(status):
            self.objJson.set(obj, 'status', status)
            self.objJson.set(obj, 'timestamp', getTimestamp(), True)
        else:
            logger.error('Invalid argument type.')
            raise TypeError('Invalid argument type')

    def __getitem__(self, key):
        '''!
         Get value of specified key in the configuration section data dictionary obtained from input JSON data.
         As JSON format can be nested, only top level key,values are accessible using this API.

         @param key (str) Key whose value needs to be searched for
         @return
              If key is found: \n
                Value object \n
              If key is not found: \n
                None

        '''
        return self.jsonDict.get(key)

    def __setitem__(self, key, val):
        '''!
         Set value of specified key in the configuration section data dictionary obtained from input JSON data.
         As JSON format can be nested, only top level key,values are accessible using this API. If the key is
         'status' it also updates the timestamp and saves the data to the corresponding JSON file.

         @param key (str) Key whose value needs to be set
         @param value (object) Value of key that needs to be set

        '''
        if key == 'status':
            self.updateStatus(self.jsonDict, val)
        else:
            self.jsonDict[key] = val

    def __buildDefaults(self, section):
        '''!
         Helper API to include missing objects in a configuration section and validate their values.
         Below are the objects that are validated and added if not present: \n
           - ignore-result\n
           - reboot-on-success\n
           - reboot-on-failure\n
           - halt-on-failure\n
           - timestamp\n

         Below are the objects whose value is validated:\n
           - status
           - suspend-exit-code

         If the specified value is invalid  of if the object is not specified, its value is read from ztp_cfg.json

         @param section (dict) Configuration Section input data read from JSON file.

        '''
        default_objs = ['ignore-result', 'reboot-on-success', 'reboot-on-failure', 'halt-on-failure']
        # Loop through objects and update them with default values
        for key in default_objs:
            _val = getField(section, key, bool, getCfg(key))
            section[key] = _val

        # set status
        if section.get('status') is None:
            section['status'] = 'BOOT'
            section['timestamp'] = getTimestamp()
        elif isString(section.get('status')) is False or \
            section.get('status') not in ['BOOT', 'IN-PROGRESS', 'SUSPEND', 'DISABLED', 'FAILED', 'SUCCESS']:
            logger.warning('Invalid value (%s) used for configuration section status. Setting it to DISABLED.' % section.get('status'))
            section['status'] = 'DISABLED'
            section['timestamp'] = getTimestamp()

        # Validate suspend-exit code
        if section.get('suspend-exit-code') is not None:
            suspend_exit_code = getField(section, 'suspend-exit-code', int, None)
            if suspend_exit_code is None or suspend_exit_code < 0:
                del section['suspend-exit-code']

        # Add timestamp if missing
        if section.get('timestamp') is None:
            section['timestamp'] = getTimestamp()

    def __init__(self, json_src_file=None, json_dst_file=None):
        '''!
         Constructor for ConfigurationSection class.

         @param json_src_file (str, optional) Configuration section input.json file to be prcoessed. If not specified,
                                              /etc/sonic/ztp_data.json file is used.
         @param json_dst_file (str, optional) Destination file to which processed JSON data is saved to. If not specified,
                                              json_src_file is used as destination file.

         @exception Raise ValueError if any error or exception encountered while processing the json_src_file

        '''
        if json_src_file is not None:
            self.json_src_file = json_src_file
        else:
            self.json_src_file = getCfg('ztp-json')
        if json_dst_file is None:
            self.json_dst_file = self.json_src_file
        else:
            self.json_dst_file = json_dst_file
        try:
            self.objJson, self.jsonDict = JsonReader(self.json_src_file, self.json_dst_file, indent=4)
        except:
            raise ValueError('ZTP JSON load failed')

class ZTPJson(ConfigSection):
    '''!
    \brief This class is use to store and access ZTP JSON data downloaded by ZTP service.
    '''

    def updateStatus(self, obj, status):
        super().updateStatus(obj, status)
        # Update the shadow ZTP JSON file with new information
        self.__writeShadowJSON()

    def __writeShadowJSON(self):
        '''!
          Save contents of ZTP JSON in a shadow file which includes data that provides
          just provisioning status information and filters out all other sensitive information.
        '''
        allowed_keys = ['ignore-result', 'reboot-on-success', \
                        'reboot-on-failure', 'halt-on-failure', \
                        'description', 'timestamp', 'status', \
                        'start-timestamp', 'error']
        section_names = list()
        shadowObj, shadowJsonDict  = JsonReader(self.json_dst_file, getCfg('ztp-json-shadow'), indent=getCfg('json-indent'))
        shadowDict = shadowJsonDict['ztp']
        for  k, v in shadowDict.items():
            # Identify configuration sections
            if isinstance(v, dict):
                section_names.append(k)

        for section in section_names:
            section_elements = list(shadowDict[section].keys())
            for sub_k in section_elements:
                # Remove sensitive data
                if sub_k not in allowed_keys:
                    del shadowDict[section][sub_k]

        shadowObj.writeJson()
        os.chmod(getCfg('ztp-json-shadow'), 0o644)

    def __getitem__(self, key):
        '''!
         Get value of specified key in the top level ztp section read from ZTP JSON file.
         As JSON format can be nested, only keys in ztp section are accessible using this API.

         @param key (str) Key whose value needs to be searched for.
         @return
             If key is found: \n
               Value object \n
             If key is not found: \n
               None

        '''
        return self.ztpDict.get(key)

    def __setitem__(self, key, val):
        '''!
         Set value of specified key in the top level ztp section read from ZTP JSON file.
         As JSON format can be nested, only keys in ztp section are accessible using this API.
         If the key is 'status' it also updates the timestamp and saves the data to ZTP JSON file.

         @param key (str) Key whose value needs to be set
         @param value (object) Value of key that needs to be set

        '''
        if key == 'status':
            self.updateStatus(self.ztpDict, val)
        else:
            self.ztpDict[key] = val
        # Update the shadow ZTP JSON file with new information
        self.__writeShadowJSON()

    def pluginArgs(self, section_name):
        '''!
         Resolve the plugin arguments used to be passed as command line arguments to
         the plugin used to process configuration section

         @param section_name (str) Configuration section name whose plugin arguments needs to be resolved.

         @return
              Concatenated string of all the argements defined \n
              If no arguments are defined or error encountered: \n
                None
        '''

        if isString(section_name) is False:
            raise TypeError('Invalid argument used as section name')
        elif self.ztpDict.get(section_name) is None:
            logger.error('Configuration Section %s not found.' % section_name)
            return None

        # Obtain plugin data
        plugin_data = self.ztpDict.get(section_name).get('plugin')

        # Get the location of this configuration section's input data parsed from the input ZTP JSON file
        plugin_input = getCfg('ztp-tmp-persistent') + '/' + section_name + '/' + getCfg('section-input-file')

        plugin_args = ''
        ignore_section_data_arg = getField(plugin_data, 'ignore-section-data', bool, False)
        _plugin_json_args = getField(plugin_data, 'args', str, None)

        if ignore_section_data_arg is False:
            plugin_args = plugin_input

        if _plugin_json_args is not None:
            plugin_args = plugin_args + ' ' + _plugin_json_args

        logger.debug('Plugin arguments for %s evaluated to be %s.' % (section_name, plugin_args))
        return  plugin_args

    def plugin(self, section_name):
        '''!
         Resolve the plugin used to process a configuration section. If the plugin is specified
         as a url object, the plugin is downloaded.

         @param section_name (str) Configuration section name whose plugin needs to be resolved.

         @return
              If plugin is resolved using configuration section data: \n
                Expanded file path to plugin file used to process configuration section. \n
              If plugin is not found or error encountered: \n
                None
        '''

        if isString(section_name) is False:
            raise TypeError('Invalid argument used as section name')
        elif self.ztpDict.get(section_name) is None:
            logger.error('Configuration Section %s not found.' % section_name)
            return None

        plugin_data = self.ztpDict.get(section_name).get('plugin')
        name = None
        if plugin_data is not None and isinstance(plugin_data, dict):
            logger.debug('User defined plugin detected for configuration section %s.' % section_name)
            plugin_file = getCfg('ztp-tmp-persistent') + '/' + section_name + '/' + 'plugin'
            try:
                # Re-use the plugin if already present
                if os.path.isfile(plugin_file) is True:
                    return plugin_file

                if plugin_data.get('dynamic-url'):
                    dyn_url_data = plugin_data.get('dynamic-url')
                    if isinstance(dyn_url_data, dict) and dyn_url_data.get('destination') is not None:
                        objDynUrl = DynamicURL(dyn_url_data)
                    else:
                        objDynUrl = DynamicURL(dyn_url_data, plugin_file)
                    rc, plugin_file = objDynUrl.download()
                    return plugin_file
                elif plugin_data.get('url'):
                    url_data = plugin_data.get('url')
                    if isinstance(url_data, dict) and url_data.get('destination') is not None:
                        objUrl = URL(url_data)
                    else:
                        objUrl = URL(url_data, plugin_file)
                    updateActivity('Downloading plugin \'%s\' for configuration section %s' % (objUrl.getSource(), section_name))
                    rc, plugin_file = objUrl.download()
                    if rc != 0:
                        logger.error('Failed to download plugin \'%s\' for configuration section %s.' % (objUrl.getSource(), section_name))
                    return plugin_file
                elif plugin_data.get('name') is not None:
                    name = plugin_data.get('name')
            except (TypeError, ValueError, OSError, IOError) as e:
                logger.error('Exception [%s] encountered while determining plugin for configuration section %s.'
                             % (str(e), section_name))
                return None
        elif plugin_data is not None and isString(plugin_data):
            name = plugin_data
        elif plugin_data is not None:
            logger.error('Invalid plugin data type used for configuration section %s.' % section_name)
            return None

        # plugin name is not provided in section data, use section name as plugin name
        if name is None:
            res = re.split("^[0-9]+-", section_name, maxsplit=1)
            if len(res) > 1:
                name = res[1]
            else:
                name = res[0]
        logger.debug('ZTP provided plugin %s is being used for configuration section %s.' % (name, section_name))
        if os.path.isfile(getCfg('plugins-dir') + '/' + name) is True:
            return getCfg('plugins-dir') + '/' + name
        return None

    def __cleanup(self):
        '''!
          Remove stale ZTP session data.
        '''
        dir_list = ['ztp-tmp', 'ztp-tmp-persistent']

        try:
            # Remove temporary files created by previous ZTP run
            for d in dir_list:
                if os.path.isdir(getCfg(d)):
                    shutil.rmtree(getCfg(d), ignore_errors=True)
            # Create them again
            for d in dir_list:
                os.makedirs(getCfg(d))
        except OSError as e:
            logger.error('Exception [%s] encountered while cleaning up temp directories.' % str(e))

    def __writeConfigSections(self, key, val):
        '''!
          Split ZTP JSON into individual configuration sections.

          @param key (str) Configuration section name
          @param value (object) Configuration section data
        '''
        section_dir = getCfg('ztp-tmp-persistent') + '/' + key
        section_file = section_dir + '/' + getCfg('section-input-file')
        try:
            if os.path.isdir(section_dir) is False:
                os.makedirs(section_dir)
                self.objJson.writeJson(section_file, {key:val}, getCfg('json-indent'))
        except:
            raise ValueError('Unable to write Configuration Section %s JSON data to file %s' % (key, section_file))

    def __buildDefaults(self):
        '''!
         Helper API to include missing objects in a configuration section and validate their values.
        '''
        # Call more abstract API to insert default values
        self._ConfigSection__buildDefaults(self.ztpDict)

        default_objs = ['restart-ztp-on-failure', 'restart-ztp-no-config', 'config-fallback']
        # Loop through objects and update them with default values
        for key in default_objs:
            _val = getField(self.ztpDict, key, bool, getCfg(key))
            self.ztpDict[key] = _val

    def __init__(self, json_src_file=None, json_dst_file=None):
        '''!
         Constructor for ZTPJson class.

         As part of the object instantiation, ZTP JSON file is read and split into individual configuration sections.
         The contents of ZTP JSON are saved as a dictionary to be used. Missing objects are added assuming default values. A list of
         configuration sections defined in the ZTP JSON is collected.

         @param json_src_file (str, optional) Configuration section input.json file to be prcoessed. If not specified,
                                              /etc/sonic/ztp_data.json file is used.
         @param json_dst_file (str, optional) Destination file to which processed JSON data is saved to. If not specified,
                                              json_src_file is used as destination file.


         @exception Raise ValueError if any error or exception encountered while processing the json_src_file

        '''
        # Call base class constructor
        ConfigSection.__init__(self, json_src_file, json_dst_file)

        # Raise exception if top level ztp section is not found
        self.ztpDict = self.jsonDict.get('ztp')
        if self.ztpDict is None or isinstance(self.ztpDict, dict) is False:
            raise ValueError('ztp section not found in JSON data')

        # Read ZTP JSON version
        if self.ztpDict.get('ztp-json-version') is None:
            self.ztpDict['ztp-json-version'] = getCfg('ztp-json-version', 'Not Available')

        # Check for presence of url or dynamic-url and download the actual json content
        reloadZTPJson = False
        try:
            if self.ztpDict.get('dynamic-url'):
                dyn_url_data = self.ztpDict.get('dynamic-url')
                if isinstance(dyn_url_data, dict):
                    dyn_url_data['destination'] = self.json_dst_file
                objDynamicURL = DynamicURL(dyn_url_data, self.json_dst_file)
                rc, filename = objDynamicURL.download()
                if rc == 0:
                    reloadZTPJson = True
                else:
                    raise ValueError('url section provided in ztp section could not be resolved')
            elif self.ztpDict.get('url'):
                url_data = self.ztpDict.get('url')
                if isinstance(url_data, dict):
                    url_data['destination'] = self.json_dst_file
                objURL = URL(url_data, self.json_dst_file)
                rc, filename = objURL.download()
                if rc == 0:
                    reloadZTPJson = True
                else:
                    raise ValueError('dynamic-url section provided in ztp section could not be resolved')
        except:
            raise ValueError('url/dynamic-url sections provided in ztp section could not be interpreted')

        if reloadZTPJson is True and os.path.isfile(self.json_dst_file):
            ConfigSection.__init__(self, self.json_dst_file, self.json_dst_file)
            self.ztpDict = self.jsonDict.get('ztp')
            if self.ztpDict is None or isinstance(self.ztpDict, dict) is False:
                raise ValueError('ztp section not found in JSON data')

            # Read ZTP JSON version
            if self.ztpDict.get('ztp-json-version') is None:
                self.ztpDict['ztp-json-version'] = getCfg('ztp-json-version', 'Not Available')

        # Insert default values
        self.__buildDefaults()

        # Cleanup previous ZTP run files
        if self.ztpDict['status'] == 'BOOT':
            self.__cleanup()

        # Identify valid configuration sections
        self.section_names = sorted(self.ztpDict.keys())

        for  k, v in self.ztpDict.items():
            # Remove leaf objects as they are not configuration sections
            if isinstance(v, dict) is False:
                self.section_names.remove(k)
                continue
            # Insert default values in configuration sections
            self._ConfigSection__buildDefaults(v)
            # Split confguration sections to individual files
            self.__writeConfigSections(k, v)

        # Write ZTP JSON data to file
        self.objJson.writeJson()
        # Update the shadow ZTP JSON file with new information
        self.__writeShadowJSON()
