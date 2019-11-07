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
import json
from functools import partial

class JsonReader(object):

    '''!
    \brief This class allow to download a json file, and convert it into a Python dict object.

    When the data change in the dict variable, it can be automatically rewritten either in the original file,
    or optionaly in a different file.

    Examples of class usage:
    \code
    objJson, json_dict = JsonReader("example.json", "saved.json", indent=4)
    url_dict = json_dict.get('url')
    data_dict = url_dict.get('data')
    objJson.set(data_dict, 'first_name', "William", save=True)
    \endcode
    '''

    def __init__(self, src_json_file=None, dst_json_file=None, create_dst_file_parent_dirs=True, indent=None):
        '''!
        Constructor: load the given json file, convert it as a dict object, and return both the class instance object and the
        dict object (as a tuple).

        Each time a change is made into the dict object, the file will be written back.

        @param src_json_file (str) Filename where to read the json data.
        @param dst_json_file (str, optional) Filename where to store the modified json data
        @param create_dst_file_parent_dirs (bool, optional) Allow to create the directy hierarchy of the destination file, in case
                                                            some directoris would not exist.
        @param indent (int, optional) Indentation level which is used when the watcher function will write back the json file.

        @return tuple (object, dict)
        '''
        ## Destination json file
        if dst_json_file is None:
            self.__dst_json_file = src_json_file
        else:
            self.__dst_json_file = dst_json_file

        ## Create or not the whole destination file parent directory structure
        self.__create_dst_file_parent_dirs = create_dst_file_parent_dirs

        ## Store the indentation level which will is used when the watcher function will write back the json file
        self.__indent = indent

    def __new__(cls, src_json_file=None, dst_json_file=None, create_dst_file_parent_dirs=True, indent=None):
        '''!
        Since we return a tuple when the class object is instanciated, we needed to override this method which create
        the object.

        @param src_json_file (str, optional) Filename where to read the json
        @param dst_json_file (str, optional) Filename where to store the json
        @param create_dst_file_parent_dirs (bool, optional) Create or not the whole destination file parent directory structure
        @param indent (int, optional) Indentation level which is used when the watcher function will write back the json file

        '''
        obj = super(JsonReader, cls).__new__(cls)
        obj.__init__(src_json_file, dst_json_file, create_dst_file_parent_dirs, indent)
        return obj, obj.__load(src_json_file, dst_json_file, create_dst_file_parent_dirs, indent)

    def __load(self, src_json_file, dst_json_file=None, create_dst_file_parent_dirs=True, indent=None):
        '''!
        Load the given json file, and return a dict object.
        Each time a change is made into the dict object, the file will be written back.

        @param src_json_file (str) Filename where to read the json
        @param dst_json_file (str, optional) Filename where to store the json
        @param create_dst_file_parent_dirs (bool, optional) Create or not the whole destination file parent directory structure
        @param indent (int, optional) Indentation level which is used when the watcher function will write back the json file

        @exception Raise an exception in case of an error
        '''
        try:
            with open(src_json_file) as json_file:
                ## dict object read from the input json file
                self.__json_dict = json.load(json_file)
                json_file.close()
        except IOError as e:
            raise Exception(e)
        except ValueError as e:
            raise Exception('Error in file %s: %s' % (src_json_file, e))

        return self.__json_dict

    def writeJson(self, file=None, dict=None, indent=None, create_dirs=None):
        '''!
        Write the current dictionary as a Json file

        @param file (str, optional) Filename where to store the json
        @param dict (dict, optional) dic object (read from json source file)
        @param indent (int, optional) Indentation level which is used when the watcher function will write back the json file
        @param create_dirs (bool, optional) Allow to create the directy hierarchy of the destination file, in case
                                            some directoris would not exist.

        @exception Raise an exception if an error happen when writing the file
        '''
        if dict is None:
            dict = self.__json_dict
        if file is None:
            file=self.__dst_json_file
        if indent is None:
            indent=self.__indent
        if create_dirs is None:
            create_dirs = self.__create_dst_file_parent_dirs

        if create_dirs:
            if os.path.dirname(file) != '':
                if os.path.isdir(os.path.dirname(file)) is False:
                    os.makedirs(os.path.dirname(file))
        try:
            with open(file, 'w') as outfile:
                if indent is not None:
                    json.dump(dict, outfile, indent=indent, sort_keys=True)
                else:
                    json.dump(dict, outfile, sort_keys=True)
                outfile.flush()
                outfile.close()
        except (IOError, ValueError) as e:
            raise Exception(e)

    def set(self, obj, key, value, save=False):
        '''!
        Change the content (key, value) of the specified dictionary object

        @param obj (dict) dict object which contain the json data
        @param key (str) key name
        @param value key value. Can be a string, a boolean or an integer
        @param save (boolean) Save modified key, value to JSON file.
                              Default value is False

        @exception Raise an exception if the first parameter is not a dict object
        '''
        if not isinstance(obj, dict):
            raise Exception('Object is not a dict object')
        obj.__setitem__(key, value)
        if save is True:
            self.writeJson()

    def get(self, obj, key):
        '''!
        Fetch the content of the specified dictionary object using its key

        @param obj (dict) dict object which contain the json data
        @param key (str) key name

        @return Return either None (key not found), or a string, a boolean, or an integer

        '''
        if not isinstance(obj, dict):
            return None
        return obj.__getitem__(key)
