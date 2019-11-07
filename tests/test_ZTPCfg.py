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
import shutil
import pytest

from ztp.ZTPCfg import ZTPCfg
from ztp.ZTPLib import validateZtpCfg

class TestClass(object):

    '''!
    \brief This class allow to define unit tests for class ZTPCfg

    Examples of class usage:

    \code
    pytest-2.7 -v -x test_ZTPCfg.py
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
        ztpcfg = ZTPCfg('')
        assert(ztpcfg != None)
        with pytest.raises(TypeError):
            ztpcfg = ZTPCfg(123)
            assert(ztpcfg != None)

    def test_json_file_not_exist(self):
        '''!
        Test when we call the constructor function with a non existent json file
        '''
        ztpcfg = ZTPCfg('/tmp/a/b/c/d/e')
        assert(ztpcfg != None)
        assert(ztpcfg.get('abc') == None)

    def test_json_file_not_valid(self, tmpdir, capsys):
        '''!
        Test when we call the constructor function with a non valid json file
        '''
        d = tmpdir.mkdir("nvalid")
        fh = d.join("config.ini")
        fh.write("""
        [application]
        user  =  foo
        password = secret
        """)
        ztpcfg = ZTPCfg(str(fh))
        assert(ztpcfg != None)
        assert(ztpcfg.get('abc') == None)

    def test_json_file_validate_config1(self, tmpdir):
        '''!
        Test reading a valid json file and validate the configuration
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
                "reboot-on-success": "red"
        }
        """)
        ztpcfg = ZTPCfg(str(fh))
        assert(ztpcfg != None)
        assert(ztpcfg.get('reboot-on-success') == 'red')
        with pytest.raises(TypeError):
            validateZtpCfg(ztpcfg)

    def test_json_file_validate_config3(self, tmpdir):
        '''!
        Test reading a non valid json file and validate the configuration
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
            {
              "admin-mode"           : true,
              "plugins-dir"          : "/usr/lib/ztp/plugins",
              "ztp-json-local"       : "/usr/lib/ztp/ztp_data_local.json",
              "ztp-json-opt67"       : "/var/run/ztp/ztp_data_opt67.json",
              "ztp-json"             : "/var/lib/ztp/ztp_data.json",
              "provisioning-script"  : "/var/lib/ztp/provisioning-script",
              "opt67-url"            : "/var/run/ztp/dhcp_67-ztp_data_url",
              "opt59-v6-url"         : "/var/run/ztp/dhcp6_59-ztp_data_url",
              "opt239-url"           : "/var/run/ztp/dhcp_239-provisioning-script_url",
              "opt239-v6-url"        : "/var/run/ztp/dhcp6_239-provisioning-script_url",
              "curl-retries"         : 3,
              "curl-timeout"         : 'abc',
              "ignore-result"        : false,
              "reboot-on-success"    : false,
              "reboot-on-failure"    : false,
              "halt-on-failure"      : false,
              "include-http-headers" : true,
              "https-secure"         : true,
              "http-user-agent"      : "SONiC-ZTP/0.1",
              "ztp-tmp-persistent"   : "/var/lib/ztp/sections",
              "ztp-tmp"              : "/var/lib/ztp/tmp",
              "section-input-file"   : "input.json",
              "log-file"             : "/var/log/ztp.log",
              "log-level-stdout"     : "DEBUG",
              "log-level-file"       : "DEBUG",
              "discovery-interval"   : 10
            }
        """)
        ztpcfg = ZTPCfg(str(fh))
        assert(ztpcfg != None)
        assert(ztpcfg.get('curl-timeout') == None)
        with pytest.raises(ValueError):
            validateZtpCfg(ztpcfg)

    def test_json_file_validate_config4(self, tmpdir):
        '''!
        Test reading a valid json file and validate the configuration
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
            {
              "admin-mode"           : true,
              "plugins-dir"          : "/usr/lib/ztp/plugins",
              "ztp-json-local"       : "/usr/lib/ztp/ztp_data_local.json",
              "ztp-json-opt67"       : "/var/run/ztp/ztp_data_opt67.json",
              "ztp-json"             : "/var/lib/ztp/ztp_data.json",
              "provisioning-script"  : "/var/lib/ztp/provisioning-script",
              "opt67-url"            : "/var/run/ztp/dhcp_67-ztp_data_url",
              "opt59-v6-url"         : "/var/run/ztp/dhcp6_59-ztp_data_url",
              "opt239-url"           : "/var/run/ztp/dhcp_239-provisioning-script_url",
              "opt239-v6-url"        : "/var/run/ztp/dhcp6_239-provisioning-script_url",
              "curl-retries"         : 3,
              "curl-timeout"         : 30,
              "ignore-result"        : false,
              "reboot-on-success"    : false,
              "reboot-on-failure"    : false,
              "halt-on-failure"      : false,
              "include-http-headers" : true,
              "https-secure"         : true,
              "http-user-agent"      : 10,
              "ztp-tmp-persistent"   : "/var/lib/ztp/sections",
              "ztp-tmp"              : "/var/lib/ztp/tmp",
              "section-input-file"   : "input.json",
              "log-file"             : "/var/log/ztp.log",
              "log-level-stdout"     : "DEBUG",
              "log-level-file"       : "DEBUG",
              "discovery-interval"   : 10
            }
        """)
        ztpcfg = ZTPCfg(str(fh))
        assert(ztpcfg != None)
        assert(ztpcfg.get('http-user-agent') == 10)
        with pytest.raises(TypeError):
            validateZtpCfg(ztpcfg)

    def test_json_file_validate_config5(self, tmpdir):
        '''!
        Test reading a valid json file and validate the configuration
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
            {
              "admin-mode"           : true,
              "plugins-dir"          : "/usr/lib/ztp/plugins",
              "ztp-json-local"       : "/usr/lib/ztp/ztp_data_local.json",
              "ztp-json-opt67"       : "/var/run/ztp/ztp_data_opt67.json",
              "ztp-json"             : "/var/lib/ztp/ztp_data.json",
              "provisioning-script"  : "/var/lib/ztp/provisioning-script",
              "opt67-url"            : "/var/run/ztp/dhcp_67-ztp_data_url",
              "opt59-v6-url"         : "/var/run/ztp/dhcp6_59-ztp_data_url",
              "opt239-url"           : "/var/run/ztp/dhcp_239-provisioning-script_url",
              "opt239-v6-url"        : "/var/run/ztp/dhcp6_239-provisioning-script_url",
              "curl-retries"         : 3,
              "curl-timeout"         : 30,
              "ignore-result"        : false,
              "reboot-on-success"    : false,
              "reboot-on-failure"    : false,
              "halt-on-failure"      : false,
              "include-http-headers" : true,
              "https-secure"         : true,
              "http-user-agent"      : "SONiC-ZTP/0.1",
              "ztp-tmp-persistent"   : "/var/lib/ztp/sections",
              "ztp-tmp"              : "/var/lib/ztp/tmp2",
              "section-input-file"   : "input.json",
              "log-file"             : "/var/log/ztp.log",
              "log-level-stdout"     : "DEBUG",
              "log-level-file"       : "DEBUG",
              "discovery-interval"   : 10
            }
        """)
        ztpcfg = ZTPCfg(str(fh))
        assert(ztpcfg != None)
        assert(ztpcfg.get('ztp-tmp') == '/var/lib/ztp/tmp2')
        try:
            shutil.rmtree('/var/lib/ztp/tmp2')
        except OSError:
            pass
        validateZtpCfg(ztpcfg)

    def test_json_file_validate_config6(self, tmpdir):
        '''!
        Test reading a valid json file and validate the configuration
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
              "admin-mode"           : None,
              "discovery-interval"   : 10
        """)
        ztpcfg = ZTPCfg(str(fh))
        assert(ztpcfg != None)
        assert(ztpcfg.get('admin-mode') == None)

#    def test_json_file_validate_config7(self, tmpdir):
        '''!
        Test reading a valid json file and validate the configuration
        '''
#        ztpcfg = ZTPCfg()
#        assert(ztpcfg != None)
#        ztpcfg.validateConfig()

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
        ztpcfg = ZTPCfg(str(fh))
        assert(ztpcfg != None)
        assert(ztpcfg.get('color') == 'red')
        assert(ztpcfg.get('value') == '#f00')

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
        ztpcfg = ZTPCfg(str(fh), indent=2)
        assert(ztpcfg != None)
        assert(ztpcfg.get('reboot-on-success') == True)
        assert(ztpcfg.get('http-user-agent') == 'SONiC-ZTP/0.1')
        assert(ztpcfg.set('http-user-agent', 'sonic', save=True) == None)
        f = self.__read_file(str(fh))
        assert(f == '{\n  "http-user-agent": "sonic",\n  "reboot-on-success": true\n}')
        assert(ztpcfg.__setitem__('http-user-agent', 'sonic') == None)
        assert(ztpcfg.__getitem__('foo1') == None)

    def test_json_file_valid_set_key2(self, tmpdir):
        '''!
        Test writing into jason file
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("test3.json")
        fh.write("""
        {
            "reboot-on-success"    : false,
            "http-user-agent"      : "SONiC-ZTP/0.2"
        }
        """)
        ztpcfg = ZTPCfg(str(fh))
        assert(ztpcfg != None)
        assert(ztpcfg.get('reboot-on-success') == False)
        assert(ztpcfg.get('http-user-agent') == 'SONiC-ZTP/0.2')
        assert(ztpcfg.set('http-user-agent', 'SONiC', save=True) == None)
        f = self.__read_file(str(fh))
        assert(f == """{
    "http-user-agent": "SONiC",
    "reboot-on-success": false
}""")

    def test_json_file_valid_set_key3(self, tmpdir):
        '''!
        Test writing into jason file
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("test4.json")
        fh.write("""
        {
            "admin-mode"    : true,
            "ztp-json"      : "ztp_data.json",
            "curl-retries"  : 1
        }
        """)
        ztpcfg = ZTPCfg(str(fh))
        assert(ztpcfg != None)
        assert(ztpcfg.get('admin-mode') == True)
        assert(ztpcfg.get('ztp-json') == 'ztp_data.json')
        assert(ztpcfg.get('curl-retries') == 1)
        ztpcfg.set('admin-mode', 123)
        with pytest.raises(TypeError):
            validateZtpCfg(ztpcfg)
        ztpcfg.set('admin-mode', False)
        ztpcfg.set('ztp-json', 123)
        with pytest.raises(TypeError):
            validateZtpCfg(ztpcfg)
        ztpcfg.set('ztp-json', 'ztp_data2.json')
        ztpcfg.set('curl-retries', 'abc')
        with pytest.raises(TypeError):
            validateZtpCfg(ztpcfg)
        ztpcfg.set('curl-retries', 3)
        ztpcfg.set('http-user-agent', 'sonic', save=True)
        f = self.__read_file(str(fh))
        assert(f == """{
    "admin-mode": false,
    "curl-retries": 3,
    "http-user-agent": "sonic",
    "ztp-json": "ztp_data2.json"
}""")

    def test_json_key_error(self, tmpdir):
        '''!
        Test writing into json file
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("test4.json")
        fh.write("""
        {
            "admin-mode"    : true,
            "ztp-json"      : "ztp_data.json",
            "curl-retries"  : 1
        }
        """)
        ztpcfg = ZTPCfg(str(fh))
        assert(ztpcfg != None)
        assert(ztpcfg.get('foo') == None)
        assert(ztpcfg.get('foo', 'foo') == 'foo')
