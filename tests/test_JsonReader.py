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
import pytest

from ztp.JsonReader import JsonReader
from ztp.defaults import *
ZTP_CFG_JSON=cfg_file

class TestClass(object):

    '''!
    \brief This class allow to define unit tests for class JsonReader

    Examples of class usage:

    \code
    pytest-2.7 -v -x test_Downloader.py
    \endcode
    '''

    def __read_file(self, fname):
        try:
            f = open(fname, 'r')
            return f.read()
        except:
            return None

    def test_constructor(self):
        '''!
        Test when we call the constructor function with incomplete or wrong parameters
        '''
        with pytest.raises(Exception):
            jsonrd = JsonReader('')
        jsonrd = JsonReader(ZTP_CFG_JSON, '/tmp/test.json')
        assert(jsonrd != None)

    def test_src_file_json_invalid(self, tmpdir, capsys):
        '''!
        Test when the json file is invalid
        '''
        d = tmpdir.mkdir("nvalid")
        fh = d.join("config.ini")
        fh.write("""
        [application]
        user  =  foo
        password = secret
        """)
        with pytest.raises(Exception):
            jsonrd, d = JsonReader(str(fh))
            assert(jsonrd != None)
            assert(d == None)

    def test_json_file_valid_get_key(self, tmpdir):
        '''!
        Test reading a valid json file
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("test1.json")
        fh.write("""
        {
                "color": "red",
                "value": "#f00"
        }
        """)
        jsonrd, d = JsonReader(str(fh))
        assert(jsonrd != None)
        assert(d != None)
        assert(jsonrd.get(d, 'color') == 'red')
        assert(jsonrd.get(d, 'value') == '#f00')

    def test_write_dict_in_json_file(self, tmpdir):
        '''!
        Test writing and reading a valid json file
        '''
        t = tmpdir.mkdir("valid")
        fh = t.join("test1.json")
        fh.write("""
        {
                "color": "red",
                "value": "#f00"
        }
        """)
        jsonrd, d = JsonReader(str(fh))
        assert(jsonrd != None)
        assert(d != None)
        assert(jsonrd.get(d, 'color') == 'red')
        assert(jsonrd.get(d, 'value') == '#f00')
        dst = t.join("/a/b/c/d/e/test1.json")
        with pytest.raises(Exception):
            jsonrd.writeJson(str(dst), d, create_dirs=False)
        jsonrd.set(d, 'value', 'rouge')
        jsonrd.writeJson(str(dst), d)
        f = self.__read_file(str(dst))
        assert(f == '{"color": "red", "value": "rouge"}')

    def test_set_dict_invalid(self):
        '''!
        Test when we call set() with an invalid dict object with set()
        '''
        jsonrd, json_dict = JsonReader(ZTP_CFG_JSON)
        assert(type(jsonrd) == JsonReader)
        assert(type(json_dict) == dict)
        assert(jsonrd != None)
        with pytest.raises(Exception):
            jsonrd.set('foo', 'key', 'value')

    def test_get_dict_invalid(self):
        '''!
        Test when we call set() with an invalid dict object with get()
        '''
        jsonrd, json_dict = JsonReader(ZTP_CFG_JSON)
        assert(type(jsonrd) == JsonReader)
        assert(type(json_dict) == dict)
        assert(jsonrd != None)
        assert(jsonrd.get('foo', 'key') == None)

    def test_json_file_valid_set_key1(self, tmpdir):
        '''!
        Test writing into jason file
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("test2.json")
        fh.write("""
        {
            "reboot-on-success"    : true,
            "http-user-agent"      : "SONiC-ZTP/0.1"
        }
        """)
        jsonrd, d = JsonReader(str(fh), indent=2)
        assert(jsonrd != None)
        assert(d != None)
        assert(jsonrd.get(d, 'reboot-on-success') == True)
        assert(jsonrd.get(d, 'http-user-agent') == 'SONiC-ZTP/0.1')
        assert(jsonrd.set(d, 'http-user-agent', 'sonic', save=True) == None)
        f = self.__read_file(str(fh))
        assert(f == '{\n  "http-user-agent": "sonic",\n  "reboot-on-success": true\n}')

    def test_json_file_valid_set_key2(self, tmpdir):
        '''!
        Test writing into jason file
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("test2.json")
        fh.write("""
        {
            "reboot-on-success"    : false,
            "http-user-agent"      : "SONiC-ZTP/0.2"
        }
        """)
        jsonrd, d = JsonReader(str(fh))
        assert(jsonrd != None)
        assert(d != None)
        assert(jsonrd.get(d, 'reboot-on-success') == False)
        assert(jsonrd.get(d, 'http-user-agent') == 'SONiC-ZTP/0.2')
        assert(jsonrd.set(d, 'http-user-agent', 'SONiC', save=True) == None)
        f = self.__read_file(str(fh))
        assert(f == '{"http-user-agent": "SONiC", "reboot-on-success": false}')
