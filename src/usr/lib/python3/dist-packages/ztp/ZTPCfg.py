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

from ztp.JsonReader import JsonReader
from ztp.defaults import *

try:        # pragma: no cover
    isinstance("", basestring)
    def isString(strVal):
        '''!
          Validate if provided atgument is of string datatype.

          @return
                 True  if strVal is if datatype string
                 False if strVal is not of datatype string

          Pyhon-2 compliant
        '''
        return isinstance(strVal, basestring)
except NameError:
    def isString(strVal):
        '''!
          Validate if provided atgument is of string datatype.

          @return
                 True  if strVal is if datatype string
                 False if strVal is not of datatype string

          Pyhon-3 compliant
        '''
        return isinstance(strVal, str)

class ZTPCfg:

    '''!
    \brief This class allow to load data from a configuration jason file.

    The .configuration jason file has only a single level, and contain configurations items structured as
    key = value

    Examples of class usage:

    \code
    ztpCfg = ZTPCfg()
    status = ztpCfg.get('status')
    \endcode
    '''

    ## Constructor for the class
    def __init__(self, cfg_json_file=None, indent=None):
        '''!
        Constructor for the class.

        @param cfg_json_file (str) Name of the json file used to read the configuration from.
                                            If the filename is not provided, the default "/host/ztp/ztp_cfg.json"
                                            filename is used.
        @exception Raise TypeError if the parameter is not a string

        @note if the json file can't be decoded, no exception is raised. Rather, the json dict object is set to None
        '''

        if cfg_json_file is not None and not isString(cfg_json_file):
            raise TypeError("Json file location name must be a string")

        if indent is None or isinstance(indent, int) is False:
            indent = 4

        ## Save configuration file location
        if cfg_json_file is not None and cfg_json_file.strip() != '':
            self.__cfg_json_file = cfg_json_file
        else:
            self.__cfg_json_file = cfg_file

        self.__objJson, self.json_dict = (None, None)

        try:
            if os.path.isfile(self.__cfg_json_file) is False:
                if os.path.isdir(os.path.dirname(self.__cfg_json_file)) is False:
                    os.makedirs(os.path.dirname(self.__cfg_json_file))
                with open(self.__cfg_json_file, "w") as f:
                    if defaultCfg['admin-mode']:
                        f.write("{\n\"admin-mode\" : true \n}\n")
                    else:
                        f.write("{\n\"admin-mode\" : false \n}\n")
                    f.close()
        except Exception as ex:
            pass
            print("Exception [%s] occurred accessing configuration file %s" % (str(ex), self.__cfg_json_file))
            return

        if os.path.isfile(self.__cfg_json_file) is True:
            try:
                self.__objJson, self.json_dict = JsonReader(self.__cfg_json_file, indent=indent)
            except Exception as ex:
                print(ex)
                print("Unexpected error reading json file %s" % (self.__cfg_json_file))
                self.__objJson, self.json_dict = (None, None)

    def __getitem__(self, key):
        '''!
        Return the value for a specific configuration item.

        @param key (str) Key for the particular configuration item.
                         If the key does not exists, the value returned is:
                           - None if a default value is not provided
        '''
        if self.__objJson is None:
            return None

        try:
            value = self.__objJson.get(self.json_dict, key)
            return value
        except (KeyError) as e:
            return None

    def get(self, key, default_value=None):
        '''!
        Return the value for a specific configuration item.

        @param key (str) Key for the particular configuration item.
                         If the key does not exists, the value returned is:
                           - None if a default value is not provided
                           - otherwise the default value is returned.
        @param default_value (str) Optional value which is returned in the case the key does not exist
                                   in the json configuration file
        '''
        if self.__objJson is None:
            return None
        try:
            value = self.__objJson.get(self.json_dict, key)
            return value
        except (KeyError) as e:
            if default_value is not None:
                return default_value
            return None

    def __setitem__(self, key, value):
        '''!
        Change the content (key, value) of the specified dictionary object and save it to
        the JSON file.

        @param obj (dict) dict object which contain the json data
        @param key (str) key name
        @param value key value. Can be a string, a boolean or an integer

        @exception Raise an exception if the first parameter is not a dict object
        '''
        return self.__objJson.set(self.json_dict, key, value, True)

    def set(self, key, value, save=False):
        '''!
        Change the content (key, value) of the specified dictionary object

        @param obj (dict) dict object which contain the json data
        @param key (str) key name
        @param value key value. Can be a string, a boolean or an integer
        @param save (boolean) Save modified key, value to JSON file.
                              Default value is False

        @exception Raise an exception if the first parameter is not a dict object
        '''
        if self.json_dict is not None:
            return self.__objJson.set(self.json_dict, key, value, save)

## Global instance of the class
ztpCfg = ZTPCfg()
