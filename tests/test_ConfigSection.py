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
sys.path.append('/usr/lib/ztp')

import os
import shutil
import pytest

from ztp.ZTPSections import ConfigSection
from ztp.ZTPLib import getCfg
from ztp.JsonReader import JsonReader

class TestClass(object):

    '''!
    \brief This class allow to define unit tests for class ConfigSection

    Examples of class usage:

    \code
    pytest-2.7 -v -x test_ConfigSection.py
    \endcode
    '''

    def __init_json(self):

        content = """{
    "ztp": {
        "0002-test-plugin": {
           "message" : "0002-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : true,
           "ignore-result" : true,
           "halt-on-failure" : true
        },
        "0003-test-plugin": {
           "plugin" : {
             "name" : "test-plugin"
           },
           "message" : "0003-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : false
        },
        "0001-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : false,
           "ignore-result" : true
        }
    }
}"""
        f = open(getCfg('ztp-json'), "w")
        f.write(content)
        f.close()


    def test_load_config_file(self):
        '''!
        Assuming that the key [ztp-json] in ztp_cfg.json
        exist and is a valid json file, verify that the constructor is loading this file.
        '''
        self.__init_json()
        config_section = ConfigSection()
        assert(config_section != None)
        json_src_file = getCfg('ztp-json')
        ztpcfg = ConfigSection(json_src_file, json_src_file)
        assert(ztpcfg != None)

    def test_load_config_file_nexist(self):
        '''!
        Assuming that the key [ztp-json] in ztp_cfg.json
        exist and is a valid json file, verify that the constructor is loading this file.
        '''
        self.__init_json()
        json_src_file = getCfg('ztp-json')
        assert(json_src_file != None)
        shutil.move(json_src_file, json_src_file+'.saved')
        with pytest.raises(ValueError):
            config_section = ConfigSection()
        shutil.move(json_src_file+'.saved', json_src_file)

    def test_constructor(self):
        self.__init_json()
        json_src_file = getCfg('ztp-json')
        config_section = ConfigSection()
        assert(type(config_section.objJson) == JsonReader)
        assert(type(config_section.jsonDict) == dict)

    def test_getkey(self):
        self.__init_json()
        json_src_file = getCfg('ztp-json')
        config_section = ConfigSection()
        assert(config_section['ztp'] == config_section.jsonDict['ztp'])
#       config_section['ztp']['dynamic-url']['source']['foo'] = 'hello'

    def test_setkey(self):
        self.__init_json()
        config_section = ConfigSection()
        assert(config_section['ztp'] == config_section.jsonDict['ztp'])
        config_section['ztp']['halt-on-failure'] = True
        assert(config_section['ztp']['halt-on-failure'] == True)
#       config_section['ztp']['dynamic-url']['source']['foo'] = 'hello'
#       assert(config_section['ztp']['dynamic-url']['source']['foo'] == 'hello')
        config_section['foo'] = 'ok'
        assert(config_section['foo'] == 'ok')

    def test_setkey_status(self):
        self.__init_json()
        config_section = ConfigSection()
        assert(config_section['ztp'] == config_section.jsonDict['ztp'])
        config_section['status'] = 'ok'
        assert(config_section['status'] == 'ok')
        with pytest.raises(TypeError):
            config_section['status'] = 123
