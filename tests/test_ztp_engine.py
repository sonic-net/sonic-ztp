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
import subprocess
import time
import shutil
import json
import pytest
import socket
import datetime
from shutil import copyfile

from ztp.ZTPLib import runCommand, getCfg, setCfg, getFeatures
from ztp.defaults import *
from ztp.JsonReader import JsonReader
from .testlib import HttpServer, data

COVERAGE=""
ZTP_CFG_JSON=cfg_file
ZTP_ENGINE_CMD=getCfg('ztp-lib-dir')+"/ztp-engine.py -d -t"
ZTP_CMD="/usr/bin/ztp -C "+cfg_file + ' '
class TestClass(object):

    cfgJson, cfgDict = JsonReader(ZTP_CFG_JSON, indent=4)
    def __timestamp(self):
        return datetime.datetime.now().replace(microsecond=0).isoformat().replace(':','.')

    def __search_file(self, fname, msg, wait_time=1):
         res = False
         while res == False and wait_time > 0:
            try:
                subprocess.check_call(['grep', '-q', msg, fname])
                res = True
                break
            except:
                pass
                res = False
            time.sleep(1)
            wait_time = wait_time -1
         return res

    def __search_cmd_output(self, haystack, needle):
        for line in haystack:
            if needle in line:
                return True
        return False

    def __check_ztp_status(self, arg, msg, wait_time=0):
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + arg)
        res = self.__search_cmd_output(output, msg)
        while res == False and wait_time > 0:
            time.sleep(1)
            wait_time = wait_time -1
            (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' status')
            res = self.__search_cmd_output(output, msg)
        return res

    def __read_file(self, fname):
        try:
            f = open(fname, 'r')
            return f.read()
        except:
            return None

    def __write_file(self, fname, content):
        f = open(fname, 'w')
        f.write(content)
        f.close

    def __check_file(self, fname, wait_time=0):
        res = os.path.isfile(fname)
        while res == False and wait_time > 0:
            time.sleep(1)
            wait_time = wait_time - 1
            res = os.path.isfile(fname)
            if res == True:
                break
        return res

    def __ztp_is_active(self):
         try:
             rc = subprocess.check_call(['systemctl', 'is-active', '--quiet', 'ztp'])
         except subprocess.CalledProcessError as e:
             rc = e.returncode
             pass
         return rc

    def __check_ztp_is_active(self, wait_time=4):
         res = self.__ztp_is_active()
         while res != 0 and wait_time > 0:
             time.sleep(1)
             wait_time = wait_time -1
             res = self.__ztp_is_active()
         return res == 0

    def __check_ztp_is_not_active(self, wait_time=4):
         res = self.__ztp_is_active()
         while res == 0 and wait_time > 0:
             time.sleep(1)
             wait_time = wait_time -1
             res = self.__ztp_is_active()
         return res != 0

    def cfgGet(self, key):
        return getCfg(key)

    def cfgSet(self, key, value):
        return setCfg(key, value)

    def __init_ztp_data(self):

        self.cfgJson, self.cfgDict = JsonReader(ZTP_CFG_JSON, indent=4)
        runCommand("systemctl stop ztp")
        # Destroy current provisioning data
        file_list = ["ztp-json-local", "ztp-json-opt67", "ztp-json", "provisioning-script", "opt67-url", "opt59-v6-url", \
                     "opt239-url", "opt239-v6-url", "ztp-restart-flag", "opt66-tftp-server", "acl-url", "graph-url", "ztp-json-shadow"]

        for filename in file_list:
            if os.path.isfile(self.cfgGet(filename)):
                os.remove(self.cfgGet(filename))

        if os.path.isfile("/etc/ztp.results"):
            os.remove("/etc/ztp.results")

        if os.path.isfile(self.cfgGet("config-db-json")) is False:
           runCommand("config-setup factory")

        runCommand("mkdir -p /var/run/ztp")
        runCommand("systemctl reset-failed ztp.service")

    def test_ztp_json(self):
        '''!
          Simple ZTP test with 4-sections where one of them is disabled, default value, ZTP Success
        '''
        content = """{
    "ztp": {
        "0002-test-plugin": {
           "message" : "0002-test-plugin",
           "message-file" : "/etc/ztp.results",
           "plugin" : {
              "shell" : true
           },
           "fail" : false
        },
        "0004-test-plugin": {
           "plugin" : {
             "name" : "test-plugin"
           },
           "message" : "0004-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : false
        },
        "0001-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : false
        },
        "0003-test-plugin": {
           "plugin" : {
             "name" : "test-plugin",
             "shell" : false
           },
           "message" : "0003-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : false,
           "status" : "DISABLED"
        },
        "0005-test-plugin": {
           "plugin" : {
             "name" : "test-plugin",
             "umask" : "177"
           },
           "message" : "umask-check",
           "message-file" : "/tmp/test_plugin_umask_600"
        },
        "0006-test-plugin": {
           "plugin" : {
             "name" : "test-plugin",
             "umask" : "177"
           },
           "message" : "umask-check",
           "message-file" : "/tmp/test_plugin_umask_644"
        }
    }
}"""
        expected_result = """0001-test-plugin
0002-test-plugin
0004-test-plugin
"""
        self.__init_ztp_data()

        runCommand("systemctl stop ztp")
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status -v')
        result = self.__read_file("/etc/ztp.results")
        assert(result == expected_result)
        os.remove("/tmp/ztp_input.json")
        os.remove("/etc/ztp.results")
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('0001-test-plugin').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('0001-test-plugin').get('timestamp') != None)
        assert(jsonDict.get('ztp').get('0001-test-plugin').get('exit-code') == 0)

        assert(jsonDict.get('ztp').get('0002-test-plugin').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('0002-test-plugin').get('timestamp') != None)
        assert(jsonDict.get('ztp').get('0002-test-plugin').get('exit-code') == 0)

        assert(jsonDict.get('ztp').get('0003-test-plugin').get('status') == 'DISABLED')
        assert(jsonDict.get('ztp').get('0003-test-plugin').get('timestamp') != None)
        assert(jsonDict.get('ztp').get('0003-test-plugin').get('exit-code') == None)

        assert(jsonDict.get('ztp').get('0004-test-plugin').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('0004-test-plugin').get('timestamp') != None)
        assert(jsonDict.get('ztp').get('0004-test-plugin').get('exit-code') == 0)

        st = os.stat("/tmp/test_plugin_umask_600")
        assert(0o600, oct(st.st_mode))

        st = os.stat("/tmp/test_plugin_umask_644")
        assert(0o644, oct(st.st_mode))
        runCommand("rm -f /tmp/test_plugin_umask_600 /tmp/test_plugin_umask_644")

        old_timestamp = jsonDict.get('ztp').get('timestamp')
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status -v')
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(os.path.isfile('/etc/ztp.results') == False)
        assert(jsonDict.get('ztp').get('timestamp') == old_timestamp)
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)



    def test_ztp_json_with_suspend(self):
        '''!
          Simple ZTP test with 3-sections, suspend/resume 2 sections, ZTP Success
        '''
        content = """{
    "ztp": {
        "0002-test-plugin": {
           "message" : "0002-test-plugin",
           "suspend-exit-code" : 1,
           "attempts" : 2,
           "message-file" : "/etc/ztp.results",
           "fail" : false
        },
        "0003-test-plugin": {
           "plugin" : {
             "name" : "test-plugin"
           },
           "suspend-exit-code" : 1,
           "attempts" : 2,
           "message" : "0003-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : false
        },
        "0001-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : false
        },
        "reboot-on-success" : true
    }
}"""
        expected_result = """0001-test-plugin
0002-test-plugin
0003-test-plugin
0002-test-plugin
0003-test-plugin
0002-test-plugin
0003-test-plugin
"""
        self.__init_ztp_data()

        runCommand("systemctl stop ztp")
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status -v')
        result = self.__read_file("/etc/ztp.results")
        assert(result == expected_result)
        os.remove("/tmp/ztp_input.json")
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)


    def test_ztp_json_failed(self):
        '''!
          Simple ZTP test with 3-sections, Failure in 2 sections, ZTP Failed
        '''
        content = """{
    "ztp": {
        "0002-test-plugin": {
           "message" : "0002-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : true
        },
        "0003-test-plugin": {
           "plugin" : {
             "name" : "test-plugin",
             "shell" : true
           },
           "message" : "0003-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : false
        },
        "0001-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : true
        }
    }
}"""
        expected_result = """0001-test-plugin
0002-test-plugin
0003-test-plugin
"""
        self.__init_ztp_data()

        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        runCommand("systemctl stop ztp")
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status -v')
        result = self.__read_file("/etc/ztp.results")
        assert(result == expected_result)
        os.remove("/tmp/ztp_input.json")
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'FAILED')
        assert(jsonDict.get('ztp').get('timestamp') != None)

        assert(jsonDict.get('ztp').get('0001-test-plugin').get('status') == 'FAILED')
        assert(jsonDict.get('ztp').get('0001-test-plugin').get('timestamp') != None)
        assert(jsonDict.get('ztp').get('0001-test-plugin').get('exit-code') == 1)

        assert(jsonDict.get('ztp').get('0002-test-plugin').get('status') == 'FAILED')
        assert(jsonDict.get('ztp').get('0002-test-plugin').get('timestamp') != None)
        assert(jsonDict.get('ztp').get('0002-test-plugin').get('exit-code') == 1)

        assert(jsonDict.get('ztp').get('0003-test-plugin').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('0003-test-plugin').get('timestamp') != None)
        assert(jsonDict.get('ztp').get('0003-test-plugin').get('exit-code') == 0)
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)


    def test_ztp_json_ignore_success(self):
        '''!
          Simple ZTP test with 3-sections, Failure in 2 sections but ignore-result set, ZTP Success
        '''
        content = """{
    "ztp": {
        "0002-test-plugin": {
           "message" : "0002-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : true,
           "ignore-result" : true
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
           "fail" : true,
           "ignore-result" : true
        }
    }
}"""
        expected_result = """0001-test-plugin
0002-test-plugin
0003-test-plugin
"""
        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status -v')
        result = self.__read_file("/etc/ztp.results")
        assert(result == expected_result)
        os.remove("/tmp/ztp_input.json")
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)

    def test_ztp_json_ignore_fail(self):
        '''!
          Simple ZTP test with 3-sections, Failure in 3 sections but ignore-result set in 2 sections, ZTP Failed
        '''
        content = """{
    "ztp": {
        "0002-test-plugin": {
           "message" : "0002-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : true,
           "ignore-result" : true
        },
        "0003-test-plugin": {
           "plugin" : {
             "name" : "test-plugin"
           },
           "message" : "0003-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : true
        },
        "0001-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : true,
           "ignore-result" : true
        },
        "reboot-on-failure" : true
    }
}"""
        expected_result = """0001-test-plugin
0002-test-plugin
0003-test-plugin
"""
        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status -v')
        result = self.__read_file("/etc/ztp.results")
        assert(result == expected_result)
        os.remove("/tmp/ztp_input.json")
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'FAILED')
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)

    def test_ztp_json_ignore_ztp_success(self):
        '''!
          Simple ZTP test with 3-sections, Failure in 3 sections but ignore-result set in 2sections, ignore-result set in ztp, ZTP Success
        '''
        content = """{
    "ztp": {
        "0002-test-plugin": {
           "message" : "0002-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : true,
           "ignore-result" : true
        },
        "0003-test-plugin": {
           "plugin" : {
             "name" : "test-plugin"
           },
           "message" : "0003-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : true
        },
        "0001-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : true,
           "ignore-result" : true
        },
        "ignore-result" : true
    }
}"""
        expected_result = """0001-test-plugin
0002-test-plugin
0003-test-plugin
"""
        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status -v')
        result = self.__read_file("/etc/ztp.results")
        assert(result == expected_result)
        os.remove("/tmp/ztp_input.json")
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)

    def test_fail_ztp_halt_on_error_1(self):
        '''!
          Simple ZTP test with 3-sections; Failure in 2nd sections and halt-on-failure set, ZTP Failed
        '''
        content = """{
    "ztp": {
        "0002-test-plugin": {
           "message" : "0002-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : true,
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
           "fail" : false
        }
    }
}"""
        expected_result = """0001-test-plugin
0002-test-plugin
"""
        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        result = self.__read_file("/etc/ztp.results")
        assert(result == expected_result)
        os.remove("/tmp/ztp_input.json")
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'FAILED')

        assert(jsonDict.get('ztp').get('0003-test-plugin').get('status') == 'BOOT')
        assert(jsonDict.get('ztp').get('0003-test-plugin').get('timestamp') != None)
        assert(jsonDict.get('ztp').get('0003-test-plugin').get('exit-code') == None)
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)

    def test_fail_ztp_halt_on_error_2(self):
        '''!
          Simple ZTP test with 3-sections; Failure in 2nd sections ignore-result in failed sections and halt-on-failure set, ZTP Success
        '''
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
        expected_result = """0001-test-plugin
0002-test-plugin
"""
        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        result = self.__read_file("/etc/ztp.results")
        assert(result == expected_result)
        os.remove("/tmp/ztp_input.json")
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('0003-test-plugin').get('status') == 'BOOT')
        assert(jsonDict.get('ztp').get('0003-test-plugin').get('timestamp') != None)
        assert(jsonDict.get('ztp').get('0003-test-plugin').get('exit-code') == None)
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)

    def test_two_level_json_url(self):
        '''!
          Simple ZTP test with 3-sections, default value, ZTP Success
        '''

        outer_content = """{
    "ztp": {
       "url" : "file:///tmp/ztp_input.json"
    }
}"""

        self.__write_file("/tmp/ztp_input_outer.json", outer_content)

        content = """{
    "ztp": {
        "0002-test-plugin": {
           "message" : "0002-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : false
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
           "fail" : false
        }
    }
}"""
        expected_result = """0001-test-plugin
0002-test-plugin
0003-test-plugin
"""
        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input_outer.json")
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        result = self.__read_file("/etc/ztp.results")
        assert(result == expected_result)
        os.remove("/tmp/ztp_input.json")
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)

    def test_two_level_json_dynamic_url(self):
        '''!
          Simple ZTP test with 3-sections, default value, ZTP Success
        '''

        outer_content = """{
    "ztp": {
       "dynamic-url" : {
         "source" : {
           "prefix" : "file:///tmp/",
           "identifier" : "hostname",
           "suffix" : "_ztp_input.json"
         }
       }
    }
}"""

        self.__write_file("/tmp/ztp_input_outer.json", outer_content)

        content = """{
    "ztp": {
        "0002-test-plugin": {
           "message" : "0002-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : false
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
           "fail" : false
        }
    }
}"""
        expected_result = """0001-test-plugin
0002-test-plugin
0003-test-plugin
"""
        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.__write_file("/tmp/" + socket.gethostname() + "_ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input_outer.json")
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        result = self.__read_file("/etc/ztp.results")
        assert(result == expected_result)
        os.remove("/tmp/" + socket.gethostname() + "_ztp_input.json")
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)

    def test_empty_config_sections(self):
        '''!
          Simple ZTP test with 3-sections which don't have plugin defined, ZTP Failed
        '''

        outer_content = """{
    "ztp": {
       "dynamic-url" : {
         "source" : {
           "prefix" : "file:///tmp/",
           "identifier" : "hostname",
           "suffix" : "_ztp_input.json"
         }
       }
    }
}"""

        self.__write_file("/tmp/ztp_input_outer.json", outer_content)

        content = """{
    "ztp": {
        "0002-test-2": {
        },
        "0003-test-3": {
        },
        "0001-test-1": {
        }
    }
}"""
        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.__write_file("/tmp/" + socket.gethostname() + "_ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input_outer.json")
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        os.remove("/tmp/" + socket.gethostname() + "_ztp_input.json")
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'FAILED')
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)

    def test_empty_ztp_sections(self):
        '''!
          Simple ZTP test with no config sections defined, ZTP Success
        '''

        outer_content = """{
    "ztp": {
       "dynamic-url" : {
         "source" : {
           "prefix" : "file:///tmp/",
           "identifier" : "hostname",
           "suffix" : "_ztp_input.json"
         }
       }
    }
}"""

        self.__write_file("/tmp/ztp_input_outer.json", outer_content)

        content = """{
    "ztp": {
    }
}"""
        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.__write_file("/tmp/" + socket.gethostname() + "_ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input_outer.json")
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        os.remove("/tmp/" + socket.gethostname() + "_ztp_input.json")
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)


    def test_valid_opt239(self):
        '''!
          Simple ZTP with option-239 ,ZTP Success
        '''
        content = """#!/bin/sh
echo "OPT239-PROVISIONING-SCRIPT" > /etc/ztp.results
exit 0
"""
        expected_result = """OPT239-PROVISIONING-SCRIPT
"""
        self.__init_ztp_data()

        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.__write_file("/tmp/prov-script", content)
        self.__write_file(self.cfgGet("opt239-url"), "file:///tmp/prov-script")
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status -v')
        result = self.__read_file("/etc/ztp.results")
        assert(result == expected_result)
        assert(os.path.isfile(self.cfgGet("provisioning-script")) == True)
        os.remove("/tmp/prov-script")
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('provisioning-script').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('provisioning-script').get('timestamp') != None)
        assert(jsonDict.get('ztp').get('provisioning-script').get('exit-code') == 0)
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)




    def test_valid_opt239_fail(self):
        '''!
          Simple ZTP with option-239, ZTP Failed
        '''
        content = """#!/bin/sh
echo "OPT239-PROVISIONING-SCRIPT" > /etc/ztp.results
exit 10
"""
        expected_result = """OPT239-PROVISIONING-SCRIPT
"""
        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)

        if os.path.isfile("/etc/ztp.results"):
            os.remove("/etc/ztp.results")

        self.__write_file("/tmp/prov-script", content)
        self.__write_file(self.cfgGet("opt239-url"), "file:///tmp/prov-script")
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status -v')
        assert(os.path.isfile("/etc/ztp.results") == True)
        result = self.__read_file("/etc/ztp.results")
        assert(result == expected_result)
        assert(os.path.isfile(self.cfgGet("provisioning-script")) == True)
        os.remove("/tmp/prov-script")
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'FAILED')
        assert(jsonDict.get('ztp').get('provisioning-script').get('status') == 'FAILED')
        assert(jsonDict.get('ztp').get('provisioning-script').get('timestamp') != None)
        assert(jsonDict.get('ztp').get('provisioning-script').get('exit-code') == 10)
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)

    def test_valid_opt239_fail_2(self):
        '''!
          Simple ZTP with option-239, ZTP Fails, ZTP is executed again
        '''
        content = """#!/bin/sh
echo "OPT239-PROVISIONING-SCRIPT" > /etc/ztp.results
exit 10
"""
        expected_result = """OPT239-PROVISIONING-SCRIPT
"""
        self.__init_ztp_data()

        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        if os.path.isfile("/etc/ztp.results"):
            os.remove("/etc/ztp.results")

        self.__write_file("/tmp/prov-script", content)
        self.__write_file(self.cfgGet("opt239-url"), "file:///tmp/prov-script")
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status -v')
        result = self.__read_file("/etc/ztp.results")
        assert(result == expected_result)
        os.remove("/tmp/prov-script")
        os.remove('/etc/ztp.results')
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'FAILED')
        assert(jsonDict.get('ztp').get('provisioning-script').get('status') == 'FAILED')
        assert(jsonDict.get('ztp').get('provisioning-script').get('timestamp') != None)
        assert(jsonDict.get('ztp').get('provisioning-script').get('exit-code') == 10)
        old_timestamp = jsonDict.get('ztp').get('provisioning-script').get('timestamp')
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status -v')
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(os.path.isfile('/etc/ztp.results') == False)
        assert(jsonDict.get('ztp').get('status') == 'FAILED')
        assert(jsonDict.get('ztp').get('provisioning-script').get('status') == 'FAILED')
        assert(jsonDict.get('ztp').get('provisioning-script').get('timestamp') != None)
        assert(jsonDict.get('ztp').get('provisioning-script').get('exit-code') == 10)
        assert(jsonDict.get('ztp').get('provisioning-script').get('timestamp') == old_timestamp)
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)

    def test_valid_opt239_json(self):
        '''!
          Simple ZTP test with 1-section, Option-239 defined, JSON is picked up
        '''
        json_content = """{
    "ztp": {
        "0001-test-plugin": {
          "message" : "0001-test-plugin",
          "message-file" : "/etc/ztp.results"
        }
    }
}"""
        expected_json_result = """0001-test-plugin
"""

        script_content = """#!/bin/sh
echo "OPT239-PROVISIONING-SCRIPT" > /etc/ztp.results
exit 0
"""
        expected_script_result = """OPT239-PROVISIONING-SCRIPT
"""
        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)

        self.__write_file("/tmp/prov-script", script_content)
        self.__write_file(self.cfgGet("opt239-url"), "file:///tmp/prov-script")

        self.__write_file("/tmp/ztp_input.json", json_content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")

        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status -v')
        result = self.__read_file("/etc/ztp.results")
        assert(result == expected_json_result)
        assert(result != expected_script_result)
        os.remove("/tmp/ztp_input.json")
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)

    def test_valid_opt239_json_localjson(self):
        '''!
          Simple ZTP test with DHCP JSON, Option-239 defined, Local JSON file, Local JSON is picked up
        '''
        local_json_content = """{
    "ztp": {
        "0002-test-plugin": {
          "message" : "0002-test-plugin",
          "message-file" : "/etc/ztp.results"
        }
    }
}"""
        expected_local_json_result = """0002-test-plugin
"""

        json_content = """{
    "ztp": {
        "0001-test-plugin": {
          "message" : "0001-test-plugin",
          "message-file" : "/etc/ztp.results"
        }
    }
}"""
        expected_json_result = """0001-test-plugin
"""

        script_content = """#!/bin/sh
echo "OPT239-PROVISIONING-SCRIPT" > /etc/ztp.results
exit 0
"""
        expected_script_result = """OPT239-PROVISIONING-SCRIPT
"""
        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)

        self.__write_file("/tmp/prov-script", script_content)
        self.__write_file(self.cfgGet("opt239-url"), "file:///tmp/prov-script")

        self.__write_file("/tmp/ztp_input.json", json_content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")

        self.__write_file(self.cfgGet('ztp-json-local'), local_json_content)

        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status -v')
        result = self.__read_file("/etc/ztp.results")
        assert(result == expected_local_json_result)
        os.remove("/tmp/ztp_input.json")
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        os.remove("/etc/ztp.results")
        old_timestamp = jsonDict.get('ztp').get('timestamp')
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(os.path.isfile('/etc/ztp.results') == False)
        assert(jsonDict.get('ztp').get('timestamp') == old_timestamp)
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)


    def test_discovery_precedence(self):

        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        # local fs
        self.__write_file(self.cfgGet("ztp-json-local"), '{"ztp":{"0001-test-plugin":{"message" : "0001-test-plugin","message-file" : "/etc/ztp.results"}}}')
        # DHCP Option 67
        self.__write_file('/tmp/dhcp-opt67', '{"ztp":{"0002-test-plugin":{"message" : "0002-test-plugin","message-file" : "/etc/ztp.results"}}}')
        # DHCP6 Option 67
        self.__write_file('/tmp/dhcp6-opt59', '{"ztp":{"0003-test-plugin":{"message" : "0003-test-plugin","message-file" : "/etc/ztp.results"}}}')
        # DHCP Option 239
        opt239_script = """#!/bin/sh
echo "DHCP-OPTION-239-PROVISIONING-SCRIPT" > /etc/ztp.results
exit 0
"""
        self.__write_file('/tmp/dhcp-opt239', opt239_script)

        # DHCP6 Option 239
        v6_239_script = """#!/bin/sh
echo "DHCP6-OPTION-239-PROVISIONING-SCRIPT" > /etc/ztp.results
exit 0
"""
        self.__write_file('/tmp/dhcp6-opt239', v6_239_script)

        self.__write_file(self.cfgGet('opt67-url'), 'file:///tmp/dhcp-opt67')
        self.__write_file(self.cfgGet('opt59-v6-url'), 'file:///tmp/dhcp6-opt59')
        self.__write_file(self.cfgGet('opt239-url'), 'file:///tmp/dhcp-opt239')
        self.__write_file(self.cfgGet('opt239-v6-url'), 'file:///tmp/dhcp6-opt239')
        self.__write_file(self.cfgGet('graph-url'), 'file:///tmp/minigraph.xml')
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        result = self.__read_file("/etc/ztp.results")
        assert(result == "0001-test-plugin\n")

        self.__init_ztp_data()
        self.__write_file(self.cfgGet('opt67-url'), 'file:///tmp/dhcp-opt67')
        self.__write_file(self.cfgGet('opt59-v6-url'), 'file:///tmp/dhcp6-opt59')
        self.__write_file(self.cfgGet('opt239-url'), 'file:///tmp/dhcp-opt239')
        self.__write_file(self.cfgGet('opt239-v6-url'), 'file:///tmp/dhcp6-opt239')
        self.__write_file(self.cfgGet('graph-url'), 'file:///tmp/minigraph.xml')
        runCommand(ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        result = self.__read_file("/etc/ztp.results")
        assert(result == "0002-test-plugin\n")

        self.__init_ztp_data()
        self.__write_file(self.cfgGet('opt59-v6-url'), 'file:///tmp/dhcp6-opt59')
        self.__write_file(self.cfgGet('opt239-url'), 'file:///tmp/dhcp-opt239')
        self.__write_file(self.cfgGet('opt239-v6-url'), 'file:///tmp/dhcp6-opt239')
        self.__write_file(self.cfgGet('graph-url'), 'file:///tmp/minigraph.xml')
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        result = self.__read_file("/etc/ztp.results")
        assert(result == "0003-test-plugin\n")

        self.__init_ztp_data()
        self.__write_file(self.cfgGet('opt239-url'), 'file:///tmp/dhcp-opt239')
        self.__write_file(self.cfgGet('opt239-v6-url'), 'file:///tmp/dhcp6-opt239')
        self.__write_file(self.cfgGet('graph-url'), 'file:///tmp/minigraph.xml')
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        result = self.__read_file("/etc/ztp.results")
        assert(result == "DHCP-OPTION-239-PROVISIONING-SCRIPT\n")

        self.__init_ztp_data()
        self.__write_file(self.cfgGet('opt239-v6-url'), 'file:///tmp/dhcp6-opt239')
        self.__write_file(self.cfgGet('graph-url'), 'file:///tmp/minigraph.xml')
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        result = self.__read_file("/etc/ztp.results")
        assert(result == "DHCP6-OPTION-239-PROVISIONING-SCRIPT\n")

        runCommand("rm -f /tmp/dhcp6-opt239 /tmp/dhcp-opt67 /tmp/dhcp6-opt59 /tmp/dhcp-opt239")
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)


    ## Invalid input json
    def test_invalid_json(self):

        self.__init_ztp_data()

        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.cfgSet('restart-ztp-on-invalid-data', False)
        self.__write_file(self.cfgGet("ztp-json-local"), '{"ztp":{"0001-test-plugin":"message" : "0001-test-plugin","message-file" : "/etc/ztp.results"}}}')
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        assert(os.path.isfile("/etc/ztp.results") == False)
        assert(os.path.isfile(self.cfgGet("ztp-json")) == False)
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)
        self.cfgSet('restart-ztp-on-invalid-data', True)


    ## Admin mode is disabled
    def test_admin_mode_disabled(self):

        self.__init_ztp_data()
        self.cfgJson.set(self.cfgDict, 'admin-mode', False, True)

        self.__write_file(self.cfgGet("ztp-json-local"), '{"ztp":{"0001-test-plugin":{"message" : "0001-test-plugin","message-file" : "/etc/ztp.results"}}}')
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        assert(os.path.isfile("/etc/ztp.results") == False)
        assert(os.path.isfile(self.cfgGet("ztp-json")) == False)

        self.__init_ztp_data()
        self.__write_file(self.cfgGet('opt239-v6-url'), 'file:///tmp/dhcp6-opt239')
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        assert(os.path.isfile("/etc/ztp.results") == False)
        assert(os.path.isfile(self.cfgGet("provisioning-script")) == False)
        runCommand("rm -f /tmp/dhcp6-opt239")
        self.cfgJson.set(self.cfgDict, 'admin-mode', True, True)

    def test_restart_of_completed_ztp(self):

        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.__write_file(self.cfgGet("ztp-json-local"), '{"ztp":{"0001-test-plugin":{"message" : "0001-test-plugin","message-file" : "/etc/ztp.results"}}}')
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        result = self.__read_file("/etc/ztp.results")
        assert(result == "0001-test-plugin\n")
        os.remove("/etc/ztp.results")
        os.rename(getCfg('config-db-json'), getCfg('config-db-json')+'.orig')
        self.cfgSet('monitor-startup-config', True)
        self.__write_file(self.cfgGet("ztp-restart-flag"), "1")
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status -v')
        assert(os.path.isfile("/etc/ztp.results") == True)
        assert(os.path.isfile(self.cfgGet("ztp-restart-flag")) == False)
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)
        os.rename(getCfg('config-db-json')+'.orig', getCfg('config-db-json'))

    def test_restart_of_completed_ztp_opt239(self):

        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)

        # DHCP Option 239
        opt239_script = """#!/bin/sh
echo "DHCP-OPTION-239-PROVISIONING-SCRIPT" > /etc/ztp.results
exit 0
"""
        self.__write_file('/tmp/dhcp-opt239', opt239_script)
        self.__init_ztp_data()
        self.__write_file(self.cfgGet('opt239-url'), 'file:///tmp/dhcp-opt239')
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status -v')
        result = self.__read_file("/etc/ztp.results")
        assert(result == "DHCP-OPTION-239-PROVISIONING-SCRIPT\n")
        os.remove("/etc/ztp.results")
        os.rename(getCfg('config-db-json'), getCfg('config-db-json')+'.orig')
        self.cfgSet('monitor-startup-config', True)

        self.__write_file(self.cfgGet("ztp-restart-flag"), "1")
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status -v')
        assert(os.path.isfile("/etc/ztp.results") == True)
        assert(os.path.isfile(self.cfgGet("ztp-restart-flag")) == False)
        result = self.__read_file("/etc/ztp.results")
        assert(result == "DHCP-OPTION-239-PROVISIONING-SCRIPT\n")
        os.remove("/etc/ztp.results")
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)
        os.rename(getCfg('config-db-json')+'.orig', getCfg('config-db-json'))


    def test_discovery_interval_opt239(self):

        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.cfgSet('test-mode', True)

        os.system("systemctl start ztp")
        runCommand(COVERAGE + ZTP_CMD + ' status -v')
        time.sleep(self.cfgGet("discovery-interval"))
        assert(os.path.isfile("/etc/ztp.results") == False)
        assert(os.path.isfile(self.cfgGet("provisioning-script")) == False)
        time.sleep(self.cfgGet("discovery-interval"))
        # DHCP Option 239
        opt239_script = """#!/bin/sh
echo "DHCP-OPTION-239-PROVISIONING-SCRIPT" > /etc/ztp.results
exit 0
"""
        self.__write_file('/tmp/dhcp-opt239', opt239_script)
        self.__write_file(self.cfgGet('opt239-url'), 'file:///tmp/dhcp-opt239-invalid')

        time.sleep(self.cfgGet("discovery-interval"))
        assert(os.path.isfile("/etc/ztp.results") == False)
        assert(os.path.isfile(self.cfgGet("provisioning-script")) == False)
        self.__write_file(self.cfgGet('opt239-url'), 'file:///tmp/dhcp-opt239')
        time.sleep(self.cfgGet("discovery-interval"))

        # time to process url and script
        assert(self.__check_file(self.cfgGet("provisioning-script"), 4) == True)
        assert(self.__check_file("/etc/ztp.results", 4) == True)
        result = self.__read_file("/etc/ztp.results")
        assert(result == "DHCP-OPTION-239-PROVISIONING-SCRIPT\n")
        os.remove("/etc/ztp.results")
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)
        self.cfgSet('test-mode', False)

    def test_discovery_interval_json(self):

        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.cfgSet('test-mode', True)

        os.system("systemctl start ztp")
        runCommand(COVERAGE + ZTP_CMD + ' status')
        time.sleep(self.cfgGet("discovery-interval"))
        assert(os.path.isfile("/etc/ztp.results") == False)
        assert(os.path.isfile(self.cfgGet("ztp-json")) == False)
        time.sleep(self.cfgGet("discovery-interval"))

        # ZTP JSON file
        self.__write_file(self.cfgGet("ztp-json-local"), '{"ztp":{"0001-test-plugin":{"message" : "0001-test-plugin","message-file" : "/etc/ztp.results"}, "0002-test-plugin":{"message" : "0002-test-plugin","message-file" : "/etc/ztp.results", "status" : "DISABLED"}}}')
        time.sleep(self.cfgGet("discovery-interval"))
        # time to process JSON
        assert(self.__check_file(self.cfgGet("ztp-json"), 4) == True)
        assert(self.__check_file("/etc/ztp.results", 4) == True)
        result = self.__read_file("/etc/ztp.results")
        assert(result == "0001-test-plugin\n")
        os.remove("/etc/ztp.results")
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)
        self.cfgSet('test-mode', False)

    def test_ztp_command(self):

        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)

        runCommand("sed -i 's:DEBUG=\"\":DEBUG=\"yes\":g' /etc/default/ztp")
        runCommand("sed -i 's:TEST_MODE=\"\":TEST_MODE=\"yes\":g' /etc/default/ztp")
        runCommand("systemctl start ztp")
        assert(self.__check_ztp_is_active() == True)
        runCommand(COVERAGE + ZTP_CMD + ' disable -y')
        self.cfgJson, self.cfgDict = JsonReader(ZTP_CFG_JSON, indent=4)
        assert(self.cfgDict.get("admin-mode") == False)
        assert(self.__ztp_is_active() != 0)
        runCommand("systemctl reset-failed ztp.service")

        runCommand("systemctl start ztp")
        assert(self.__check_ztp_is_not_active() == True)
        runCommand("systemctl reset-failed ztp.service")

        runCommand(COVERAGE + ZTP_CMD + ' enable -y')
        self.cfgJson, self.cfgDict = JsonReader(ZTP_CFG_JSON, indent=4)
        assert(self.cfgDict.get("admin-mode") == True)
        runCommand("systemctl start ztp")
        assert(self.__check_ztp_is_active() == True)
        runCommand("systemctl stop ztp")
        runCommand("systemctl reset-failed ztp.service")

        self.__write_file(self.cfgGet('ztp-json'), '{"ztp": { "01-test-plugin":{"sleep" : 40} } }')
        runCommand(COVERAGE + ZTP_CMD + " erase -y")
        assert(os.path.isfile(self.cfgGet('ztp-json')) == False)
        assert(os.path.isfile(getCfg('config-db-json')) == True)

        self.__write_file(self.cfgGet('ztp-json'), '{"ztp": { "01-test-plugin":{"sleep" : 40} } }')
        runCommand(COVERAGE + ZTP_CMD + " run -y")
        assert(os.path.isfile(getCfg('config-db-json')) == True)
        assert(os.path.isfile(self.cfgGet('ztp-json')) == False)
        assert(self.__check_ztp_is_active() == True)

        runCommand("systemctl stop ztp")
        runCommand("systemctl reset-failed ztp.service")

        self.cfgSet('monitor-startup-config', True)
        copyfile(getCfg('config-db-json'), getCfg('config-db-json')+'.orig')
        runCommand(COVERAGE + ZTP_CMD + " erase -y")
        runCommand(COVERAGE + ZTP_CMD + " run -y")
        assert(os.path.isfile(getCfg('config-db-json')) == False)
        assert(self.__check_ztp_is_active() == True)
        runCommand("systemctl stop ztp")
        runCommand("systemctl reset-failed ztp.service")

        runCommand(COVERAGE + ZTP_CMD + " erase -y")
        runCommand(COVERAGE + ZTP_CMD + " run -y")
        assert(os.path.isfile(getCfg('config-db-json')) == False)
        assert(self.__check_ztp_is_active() == True)
        runCommand("systemctl stop ztp")
        runCommand("systemctl reset-failed ztp.service")

        os.rename(getCfg('config-db-json')+'.orig', getCfg('config-db-json'))

        runCommand("sed -i 's:DEBUG=\"yes\":DEBUG=\"\":g' /etc/default/ztp")
        runCommand("sed -i 's:TEST_MODE=\"yes\":TEST_MODE=\"\":g' /etc/default/ztp")
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)

    def test_ztp_arguments_test(self):
        '''!
          Simple ZTP test with 3-sections, Failure in 2 sections, ZTP Failed
        '''
        test_sh = """#!/bin/sh
        echo -n "$*" > /tmp/test_sh_args
        exit 0
"""
        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)

        section_data=self.cfgGet('ztp-tmp-persistent') + '/0001-arg-check/' + self.cfgGet('section-input-file')

        runCommand("systemctl stop ztp")
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")

        # section-file + args
        json_content = """{
    "ztp": {
        "0001-arg-check": {
           "plugin" : {
            "url" : "file:///tmp/test.sh",
            "args" : "-a -b"
          }
        }
    }
}"""
        self.__write_file("/tmp/ztp_input.json", json_content)
        self.__write_file("/tmp/test.sh", test_sh)
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        result = self.__read_file("/tmp/test_sh_args")
        os.remove(self.cfgGet('ztp-json'))
        os.remove('/tmp/test_sh_args')
        assert(result == section_data + " -a -b")
        os.remove("/tmp/ztp_input.json")

        # args
        json_content = """{
    "ztp": {
        "0001-arg-check": {
           "plugin" : {
            "url" : "file:///tmp/test.sh",
            "args" : "-a -b",
            "ignore-section-data" : true
          }
        }
    }
}"""
        self.__write_file("/tmp/ztp_input.json", json_content)
        self.__write_file("/tmp/test.sh", test_sh)
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        result = self.__read_file("/tmp/test_sh_args")
        os.remove(self.cfgGet('ztp-json'))
        os.remove('/tmp/test_sh_args')
        assert(result == "-a -b")
        os.remove("/tmp/ztp_input.json")


       # no_args
        json_content = """{
    "ztp": {
        "0001-arg-check": {
           "plugin" : {
            "url" : "file:///tmp/test.sh",
            "ignore-section-data" : true
          }
        }
    }
}"""
        self.__write_file("/tmp/ztp_input.json", json_content)
        self.__write_file("/tmp/test.sh", test_sh)
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        result = self.__read_file("/tmp/test_sh_args")
        os.remove(self.cfgGet('ztp-json'))
        os.remove('/tmp/test_sh_args')
        assert(result == "")
        os.remove("/tmp/ztp_input.json")

       # no_args
        json_content = """{
    "ztp": {
        "0001-arg-check": {
           "plugin" : {
            "url" : "file:///tmp/test.sh",
            "ignore-section-data" : false
          }
        }
    }
}"""
        self.__write_file("/tmp/ztp_input.json", json_content)
        self.__write_file("/tmp/test.sh", test_sh)
        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        runCommand(COVERAGE + ZTP_CMD + ' status')
        result = self.__read_file("/tmp/test_sh_args")
        os.remove(self.cfgGet('ztp-json'))
        os.remove('/tmp/test_sh_args')
        assert(result == section_data)
        os.remove("/tmp/ztp_input.json")
        os.remove("/tmp/test.sh")
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)

# New test cases
    def test_signal_handler(self):

        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)

        runCommand("systemctl stop ztp")
        runCommand("sed -i 's:TEST_MODE=\"\":TEST_MODE=\"yes\":g' /etc/default/ztp")

        # ZTP JSON file
        self.__write_file(self.cfgGet("ztp-json-local"), '{"ztp":{"0001-test-plugin":{"message" : "0001-test-plugin","message-file" : "/etc/ztp.results", "sleep": 100}}}')
        runCommand("systemctl start ztp")
        # time to process JSON
        assert(self.__check_file("/etc/ztp.results", 4) == True)
        runCommand("systemctl stop ztp")
        time.sleep(2)
        assert(os.path.isfile("/etc/ztp.results") == False)
        os.remove(self.cfgGet("ztp-json"))
        runCommand("sed -i 's:TEST_MODE=\"yes\":TEST_MODE=\"\":g' /etc/default/ztp")
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)

    def test_ztp_reboot_on_flag(self):
        '''!
          Simple ZTP test with reboot-on success
        '''
        content = """{
    "ztp": {
        "0001-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : false,
           "reboot-on-success" : "True"
        },
        "0002-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : true,
           "reboot-on-failure" : "True"
        }
    }
}"""
        self.__init_ztp_data()
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")

        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'IN-PROGRESS')
        assert(jsonDict.get('ztp').get('0001-test-plugin').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('0002-test-plugin').get('status') == 'BOOT')

        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'IN-PROGRESS')
        assert(jsonDict.get('ztp').get('0001-test-plugin').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('0002-test-plugin').get('status') == 'FAILED')

        runCommand(COVERAGE + ZTP_ENGINE_CMD)
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'FAILED')

        os.remove("/tmp/ztp_input.json")
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)

    def test_ztp_restart_ztp_on_invalid_data(self):
        '''!
          Simple ZTP test with reboot-on success
        '''
        content = """{
    "ztp2": {
        "0001-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results"
        }
    }
}"""
        self.__init_ztp_data()
        self.cfgSet('test-mode', True)
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.cfgSet('restart-ztp-interval', 5)
        _discover_interval = self.cfgGet('discovery-interval')
        self.cfgSet('discovery-interval', 2)
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")

        os.system("systemctl start ztp")
        # Give time to process JSON
        time.sleep(self.cfgGet('restart-ztp-interval'))
        assert(os.path.isfile(self.cfgGet('ztp-json')) == False)
        time.sleep(self.cfgGet('restart-ztp-interval'))
        assert(os.path.isfile(self.cfgGet('ztp-json')) == False)

        content = """{
    "ztp": {
        "0001-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results"
        }
    }
}"""
        self.__write_file("/tmp/ztp_input.json", content)
        time.sleep(self.cfgGet('restart-ztp-interval'))
        time.sleep(self.cfgGet('discovery-interval'))
        # Time to process ztp json
        assert(self.__check_file(self.cfgGet('ztp-json'), 4) == True)

        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('0001-test-plugin').get('status') == 'SUCCESS')

        os.remove("/tmp/ztp_input.json")
        self.cfgSet('restart-ztp-interval', 300)
        self.cfgSet('discovery-interval', _discover_interval)
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)
        self.cfgSet('test-mode', False)

    def test_ztp_restart_ztp_on_missing_config(self):
        '''!
          Simple ZTP test with reboot-on success
        '''
        content = """{
    "ztp": {
        "0001-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results"
        },
        "restart-ztp-no-config" : true
    }
}"""
        self.__init_ztp_data()
        self.cfgSet('test-mode', True)
        self.cfgSet('restart-ztp-interval', 5)
        _discover_interval = self.cfgGet('discovery-interval')
        self.cfgSet('discovery-interval', 2)
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")

        os.rename(getCfg('config-db-json'), getCfg('config-db-json')+'.orig')
        os.system("systemctl start ztp")
        # Give time to process JSON
        time.sleep(self.cfgGet('restart-ztp-interval'))
        if os.path.isfile(self.cfgGet('ztp-json')) == True:
            time.sleep(1)
        assert(os.path.isfile(self.cfgGet('ztp-json')) == False)
        time.sleep(self.cfgGet('restart-ztp-interval'))
        if os.path.isfile(self.cfgGet('ztp-json')) == True:
            time.sleep(1)
        assert(os.path.isfile(self.cfgGet('ztp-json')) == False)

        content = """{
    "ztp": {
        "0001-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/sonic/config_db.json"
        },
        "restart-ztp-no-config" : true
    }
}"""
        self.__write_file("/tmp/ztp_input.json", content)
        time.sleep(self.cfgGet('restart-ztp-interval'))
        time.sleep(self.cfgGet('discovery-interval'))
        # Time to process ztp json
        assert(self.__check_file(self.cfgGet('ztp-json'), 4) == True)

        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('0001-test-plugin').get('status') == 'SUCCESS')

        os.remove(getCfg('config-db-json'))
        os.rename(getCfg('config-db-json')+'.orig', getCfg('config-db-json'))
        os.remove("/tmp/ztp_input.json")
        self.cfgSet('restart-ztp-interval', 300)
        self.cfgSet('discovery-interval', _discover_interval)
        self.cfgSet('test-mode', False)

    def test_ztp_restart_ztp_on_failure(self):
        '''!
          Simple ZTP test with reboot-on success
        '''
        content = """{
    "ztp": {
        "0001-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : true
        },
       "restart-ztp-on-failure" : true,
        "restart-ztp-no-config" : false
    }
}"""
        self.__init_ztp_data()
        self.cfgSet('test-mode', True)
        self.cfgSet('restart-ztp-interval', 5)
        _discover_interval = self.cfgGet('discovery-interval')
        self.cfgSet('discovery-interval', 2)
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")
        os.system("mkdir -p "+self.cfgGet("ztp-run-dir") +"/ztp.lock")
        os.system("echo dhcp:Ethernet0 >" + self.cfgGet("ztp-run-dir")+"/ztp.lock/interface")

        os.rename(getCfg('config-db-json'), getCfg('config-db-json')+'.orig')
        os.system("systemctl start ztp")
        # Give time to process JSON
        time.sleep(self.cfgGet('restart-ztp-interval'))
        if os.path.isfile(self.cfgGet('ztp-json')) == True:
            time.sleep(1)
        assert(os.path.isfile(self.cfgGet('ztp-json')) == False)
        time.sleep(self.cfgGet('restart-ztp-interval'))
        if os.path.isfile(self.cfgGet('ztp-json')) == True:
            time.sleep(1)
        assert(os.path.isfile(self.cfgGet('ztp-json')) == False)

        content = """{
    "ztp": {
        "0001-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/sonic/config_db.json"
        },
        "restart-ztp-on-failure" : true,
        "restart-ztp-no-config" : false
    }
}"""
        self.__write_file("/tmp/ztp_input.json", content)
        time.sleep(self.cfgGet('restart-ztp-interval'))
        time.sleep(self.cfgGet('discovery-interval'))
        # Time to process ztp json
        assert(self.__check_file(self.cfgGet('ztp-json'), 4) == True)

        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('0001-test-plugin').get('status') == 'SUCCESS')
        runCommand(COVERAGE + ZTP_CMD + ' status -v')

        os.remove(getCfg('config-db-json'))
        os.rename(getCfg('config-db-json')+'.orig', getCfg('config-db-json'))
        os.remove("/tmp/ztp_input.json")
        os.system("rm -rf "+self.cfgGet("ztp-run-dir")+"/ztp.lock")
        self.cfgSet('restart-ztp-interval', 300)
        self.cfgSet('discovery-interval', _discover_interval)
        self.cfgSet('test-mode', False)

    def test_ztp_restart_ztp_on_malformed_url(self):
        content = """{
    "ztp": {
        "0001-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results"
        }
    }
}"""
        self.__init_ztp_data()
        self.cfgSet('test-mode', True)
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        _discover_interval = self.cfgGet('discovery-interval')
        self.cfgSet('discovery-interval', 2)
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file///tmp/ztp_input.json")

        os.system("systemctl start ztp")
        # Give time to process JSON
        time.sleep(self.cfgGet('discovery-interval'))
        time.sleep(self.cfgGet('discovery-interval'))
        assert(os.path.isfile(self.cfgGet('ztp-json')) == False)
        time.sleep(self.cfgGet('discovery-interval'))
        time.sleep(self.cfgGet('discovery-interval'))
        assert(os.path.isfile(self.cfgGet('ztp-json')) == False)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")

        time.sleep(self.cfgGet('discovery-interval'))
        # Time to process ztp json
        assert(self.__check_file(self.cfgGet('ztp-json'), 4) == True)

        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('0001-test-plugin').get('status') == 'SUCCESS')

        os.remove("/tmp/ztp_input.json")
        self.cfgSet('discovery-interval', _discover_interval)
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)
        self.cfgSet('test-mode', False)

    def test_ztp_restart_ztp_on_invalid_data_received(self):
        content = """{
    "ztp": {
        "0001-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results"
        }
    }
}"""
        self.__init_ztp_data()
        self.cfgSet('test-mode', True)
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        _restart_interval = self.cfgGet('restart-ztp-interval')
        self.cfgSet('restart-ztp-interval', 5)
        _discover_interval = self.cfgGet('discovery-interval')
        self.cfgSet('discovery-interval', 2)
        self.__write_file("/tmp/ztp_input.json", content)
        runCommand("cp /bin/ls /var/run/ztp/dhcp_67-ztp_data_url")

        os.system("systemctl start ztp")
        time.sleep(self.cfgGet('restart-ztp-interval'))
        assert(self.__check_ztp_status(' status', "Invalid provisioning data received", 10) == True)

        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")

        # Time to process ztp json
        time.sleep(self.cfgGet('discovery-interval'))
        assert(self.__check_ztp_is_not_active(10) == True)
        assert(self.__check_file("/etc/ztp.results", 5) == True)
        assert(self.__check_file(self.cfgGet('ztp-json'), 3) == True)

        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('0001-test-plugin').get('status') == 'SUCCESS')

        os.remove("/tmp/ztp_input.json")
        self.cfgSet('restart-ztp-interval', _restart_interval)
        self.cfgSet('discovery-interval', _discover_interval)
        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)
        self.cfgSet('test-mode', False)

    def test_ztp_no_start_if_startupconfig_exists(self):
        content = """{
    "ztp": {
        "0001-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results"
        },
        "restart-ztp-no-config" : false
    }
}"""
        self.__init_ztp_data()
        self.cfgSet('test-mode', True)
        os.system("touch "+self.cfgGet('config-db-json'))
        _discover_interval = self.cfgGet('discovery-interval')
        self.cfgSet('discovery-interval', 2)
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")

        os.system("systemctl start ztp")
        time.sleep(self.cfgGet('discovery-interval'))
        time.sleep(self.cfgGet('discovery-interval'))
        assert(os.path.isfile(self.cfgGet('ztp-json')) == False)
        assert(self.__check_ztp_is_not_active(4) == True)

        os.rename(getCfg('config-db-json'), getCfg('config-db-json')+'.orig')
        os.system("systemctl start ztp")
        time.sleep(self.cfgGet('discovery-interval'))
        # Time to process ztp json
        assert(self.__check_file(self.cfgGet('ztp-json'), 4) == True)
        assert(self.__check_ztp_is_not_active(4) == True)

        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('0001-test-plugin').get('status') == 'SUCCESS')

        os.remove("/tmp/ztp_input.json")
        os.rename(getCfg('config-db-json')+'.orig', getCfg('config-db-json'))
        self.cfgSet('discovery-interval', _discover_interval)
        self.cfgSet('test-mode', False)

    def test_ztp_opt66_67(self):
        self.__init_ztp_data()
        curl_retries = self.cfgGet('curl-retries')
        curl_timeout = self.cfgGet('curl-timeout')
        discovery_interval = self.cfgGet('discovery-interval')
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.cfgSet('test-mode', True)

        self.cfgSet('curl-retries', 2)
        self.cfgSet('curl-timeout', 2)
        self.cfgSet('discovery-interval', 2)

        os.system("systemctl start ztp")
        self.__write_file(self.cfgGet('opt66-tftp-server'), '10.2.1.1')
        filename = 'ztp.json.'+ self.__timestamp()
        self.__write_file(self.cfgGet('opt67-url'), filename)
        tftp_url = 'tftp://10.2.1.1/' + filename
        time.sleep(self.cfgGet('discovery-interval'))
        # Time to process request
        assert(self.__search_file('/var/log/syslog', tftp_url, 4) == True)
        os.remove(self.cfgGet('opt67-url'))
        os.remove(self.cfgGet('opt66-tftp-server'))

        content = """{
    "ztp": {
        "0001-test-plugin": {
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results"
        },
        "restart-ztp-no-config" : false
    }
}"""
        filename = "/tmp/ztp_input.json."+self.__timestamp()
        self.__write_file(filename, content)
        url = 'file://'+filename
        self.__write_file(self.cfgGet('opt66-tftp-server'), '10.2.1.1')
        self.__write_file(self.cfgGet("opt67-url"), url)
        time.sleep(2*self.cfgGet('discovery-interval'))
        # Time to process request
        assert(self.__check_file("/etc/ztp.results", 10) == True)
        assert(self.__check_file(self.cfgGet('ztp-json')) == True)
        assert(self.__check_ztp_is_not_active(4) == True)
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('0001-test-plugin').get('status') == 'SUCCESS')
        os.remove(filename)
        os.remove("/etc/ztp.results")

        self.cfgSet('monitor-startup-config', True)
        self.cfgSet('restart-ztp-no-config', True)
        self.cfgSet('curl-retries', curl_retries)
        self.cfgSet('curl-timeout', curl_timeout)
        self.cfgSet('discovery-interval', discovery_interval)
        self.cfgSet('test-mode', False)
        self.__init_ztp_data()

    def test_graphservice_dhcp_opt(self):
        self.__init_ztp_data()
        curl_retries = self.cfgGet('curl-retries')
        curl_timeout = self.cfgGet('curl-timeout')
        discovery_interval = self.cfgGet('discovery-interval')
        self.cfgSet('monitor-startup-config', False)
        self.cfgSet('restart-ztp-no-config', False)
        self.cfgSet('test-mode', True)

        self.cfgSet('curl-retries', 2)
        self.cfgSet('curl-timeout', 2)
        self.cfgSet('discovery-interval', 2)
        if os.path.isfile(self.cfgGet('plugins-dir')+'/graphservice'):
            os.rename(self.cfgGet('plugins-dir')+'/graphservice', self.cfgGet('plugins-dir')+'/graphservice.bak')

        graph_file = '/tmp/mini.xml' + '.' +self.__timestamp()
        graph_url = 'file://' + graph_file
        self.__write_file(self.cfgGet('graph-url'), graph_url)
        if os.path.isfile(self.cfgGet('ztp-json')):
            os.remove(self.cfgGet('ztp-json'))
        os.system("systemctl start ztp")
        time.sleep(self.cfgGet('discovery-interval'))
        # Time to process request
        assert(self.__search_file('/var/log/syslog', graph_url, 4) == True)
        os.system('touch '+ graph_file)
        time.sleep(self.cfgGet('discovery-interval'))
        assert(self.__check_file(self.cfgGet('ztp-json'), 4) == True)
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'FAILED')
        assert(jsonDict.get('ztp').get('graphservice').get('status') == 'FAILED')
        assert(jsonDict.get('ztp').get('graphservice').get('minigraph-url').get('url') == graph_url)
        os.remove(self.cfgGet('ztp-json'))

        acl_file = '/tmp/acl.json' + '.' +self.__timestamp()
        acl_url = 'file://' + acl_file
        self.__write_file(self.cfgGet('acl-url'), acl_url)
        os.system("systemctl start ztp")
        time.sleep(self.cfgGet('discovery-interval'))
        # Time to process request
        assert(self.__search_file('/var/log/syslog', acl_url, 4) == True)
        os.system('touch '+ acl_file)
        time.sleep(self.cfgGet('discovery-interval'))
        time.sleep(4)
        os.remove(acl_file)
        os.remove(graph_file)

        assert(os.path.isfile(self.cfgGet('ztp-json')) == True)
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'FAILED')
        assert(jsonDict.get('ztp').get('graphservice').get('status') == 'FAILED')
        assert(jsonDict.get('ztp').get('graphservice').get('minigraph-url').get('url') == graph_url)
        assert(jsonDict.get('ztp').get('graphservice').get('acl-url').get('url') == acl_url)

        self.cfgSet('monitor-startup-config', True)
        time.sleep(self.cfgGet('discovery-interval'))
        self.cfgSet('restart-ztp-no-config', True)
        self.cfgSet('curl-retries', curl_retries)
        self.cfgSet('curl-timeout', curl_timeout)
        self.cfgSet('discovery-interval', discovery_interval)
        if os.path.isfile(self.cfgGet('plugins-dir')+'/graphservice.bak'):
            os.rename(self.cfgGet('plugins-dir')+'/graphservice.bak', self.cfgGet('plugins-dir')+'/graphservice')
        self.cfgSet('test-mode', False)

        self.__init_ztp_data()

    def test_ztp_full_mode(self):
        self.__init_ztp_data()
        os.rename(getCfg('config-db-json'), getCfg('config-db-json')+'.orig')
        restart_ztp_interval = self.cfgGet('restart-ztp-interval')
        self.cfgSet('restart-ztp-interval', 30)

        os.system(COVERAGE + ZTP_CMD + ' enable')
        os.system(COVERAGE + ZTP_CMD + ' run -y')
        content = """{
    "ztp": {
        "0001-test-plugin": {
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results"
        },
        "restart-ztp-no-config" : false
    }
}"""
        # Give time to start discovery
        assert(self.__check_ztp_status(' status', "Restarting network discovery", 480) == True)
        assert(self.__check_ztp_status(' status', "Discovering provisioning data", 480) == True)
        assert(self.__check_ztp_status(' status', "Restarting network discovery", 30) == True)
        assert(self.__check_ztp_status(' status', "Discovering provisioning data", 480) == True)

        self.__write_file(self.cfgGet("ztp-json-local"), content)

        # Wait for ZTP service to exit
        assert(self.__check_ztp_is_not_active(480) == True)

        assert(os.path.isfile(self.cfgGet('ztp-json')) == True)
        objJson, jsonDict = JsonReader(self.cfgGet('ztp-json'), indent=4)
        assert(jsonDict.get('ztp').get('status') == 'SUCCESS')
        assert(jsonDict.get('ztp').get('0001-test-plugin').get('status') == 'SUCCESS')
        self.cfgSet('restart-ztp-interval', restart_ztp_interval)
        os.remove("/etc/ztp.results")
        os.remove(self.cfgGet("ztp-json-local"))
        os.rename(getCfg('config-db-json')+'.orig', getCfg('config-db-json'))
        self.__init_ztp_data()

    def test_ztp_config_save_undo(self):
        self.__init_ztp_data()
        os.rename(getCfg('config-db-json'), getCfg('config-db-json')+'.orig')
        roll_back_to_test_mode = False
        if self.cfgGet('test-mode') is True:
            self.cfgSet('test-mode', False)
            roll_back_to_test_mode = True

        os.system(getCfg('ztp-lib-dir')+'/ztp-profile.sh create ztp_config.json')
        os.rename('ztp_config.json', getCfg('config-db-json'))

        os.system(COVERAGE + ZTP_CMD + ' enable')

        content = """{
    "ztp": {
        "0001-test-plugin": {
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results"
        },
        "restart-ztp-no-config" : false
    }
}"""
        self.__write_file(self.cfgGet("ztp-json-local"), content)

        os.system('systemctl start ztp')
        assert(self.__check_ztp_is_active(4) == True)
        assert(os.path.isfile(self.cfgGet('ztp-json')) == False)
        assert(self.__check_ztp_is_not_active(120) == True)

        with open(getCfg('config-db-json')) as json_file:
            config_db = json.load(json_file)
            json_file.close()
        assert(config_db.get('ZTP') == None)

        os.remove(self.cfgGet("ztp-json-local"))
        os.rename(getCfg('config-db-json')+'.orig', getCfg('config-db-json'))
        if roll_back_to_test_mode is True:
            self.cfgSet('test-mode', True)
      

    def test_ztp_features(self):

        runCommand("systemctl stop ztp")
        (rv, cmd_output, err) = runCommand(COVERAGE + ZTP_CMD + ' features')
        assert(rv == 0)
        features = getFeatures()
        for feat in features:
           if self.cfgGet(feat):
               assert(feat in cmd_output)
           else:
               assert(feat not in cmd_output)
        (rv, cmd_output, err) = runCommand(COVERAGE + ZTP_CMD + ' features --verbose')
        assert(rv == 0)
        for feat in features:
            assert(feat+': '+ self.cfgGet('info-'+feat) +': '+str(self.cfgGet(feat)) in cmd_output)

    def test_ztp_status(self):
        '''!
          Test validity of ztp status command output
        '''
        content = """{
    "ztp": {
        "0001-test-plugin": {
           "sleep" : "1"
        },
        "0002-test-plugin": {
           "sleep" : "2"
        },
        "0003-test-plugin": {
           "sleep" : "3"
        },
        "restart-ztp-no-config" : false
    }
}"""
        self.__init_ztp_data()
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' enable')
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' status -c')
        assert('1:INACTIVE' == output[0])
        _discover_interval = self.cfgGet('discovery-interval')
        self.cfgSet('discovery-interval', 2)
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")
        os.system("mkdir -p "+self.cfgGet("ztp-run-dir") +"/ztp.lock")
        os.system("echo dhcp:Ethernet0 >" + self.cfgGet("ztp-run-dir")+"/ztp.lock/interface")
        os.rename(getCfg('config-db-json'), getCfg('config-db-json')+'.orig')
        os.system(COVERAGE + ZTP_ENGINE_CMD)

        assert(os.path.isfile(self.cfgGet('ztp-json')) == True)
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' status')
        assert('ZTP Status     : SUCCESS' in output)
        assert('ZTP Source     : dhcp-opt67 (Ethernet0)' in output)
        assert('Runtime        : 07s' in output or \
               'Runtime        : 08s' in output)
        assert('0001-test-plugin: SUCCESS' in output)
        assert('0002-test-plugin: SUCCESS' in output)
        assert('0003-test-plugin: SUCCESS' in output)
        assert("ZTP Admin Mode : True" in output)
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' status -v')
        assert("========================================" == output[0])
        assert("ZTP" == output[1])
        assert("========================================" == output[2])
        assert("ZTP JSON Version : "+getCfg('ztp-json-version') in output)
        assert("0001-test-plugin" in output)
        assert("0002-test-plugin" in output)
        assert("0003-test-plugin" in output)
        assert(output.count("Status          : SUCCESS") == 3)
        assert("ZTP Admin Mode : True" in output)
        assert('Runtime        : 07s' in output or \
               'Runtime        : 08s' in output)
        assert('Runtime         : 01s' in output or \
               'Runtime         : 02s' in output)
        assert('Runtime         : 02s' in output or \
               'Runtime         : 03s' in output)
        assert('Runtime         : 03s' in output or \
               'Runtime         : 04s' in output)
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' status -c')
        assert('5:SUCCESS' == output[0])
        runCommand(COVERAGE + ZTP_CMD + ' disable -y')
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' status -v')
        assert("ZTP Admin Mode : False" in output)
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' status')
        assert("ZTP Admin Mode : False" in output)
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' status -c')
        assert('0:DISABLED' == output[0])
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' enable')

        content = """{
    "ztp": {
        "0001-test-plugin": {
         "description" : "This is Test Plugin 1"
        },
        "0002-test-plugin": {
         "fail" : true
        },
        "0003-test-plugin": {
        },
        "restart-ztp-no-config" : false
    }
}"""
        self.__init_ztp_data()
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt59-v6-url"), "file:///tmp/ztp_input.json")
        os.system("mkdir -p "+self.cfgGet("ztp-run-dir") +"/ztp.lock")
        os.system("echo dhcp6:Ethernet4 >" + self.cfgGet("ztp-run-dir")+"/ztp.lock/interface")
        if os.path.isfile(getCfg('config-db-json')):
            os.remove(getCfg('config-db-json'))
        os.system(COVERAGE + ZTP_ENGINE_CMD)

        assert(os.path.isfile(self.cfgGet('ztp-json')) == True)
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' status -c')
        assert('6:FAILED' == output[0])
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' status')
        assert('ZTP Status     : FAILED' in output)
        assert('0001-test-plugin: SUCCESS' in output)
        assert('0002-test-plugin: FAILED' in output)
        assert('0003-test-plugin: SUCCESS' in output)
        assert('ZTP Source     : dhcp6-opt59 (Ethernet4)' in output)
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' status -v')
        assert('Error           : Plugin failed' in output)
        assert('Error          : 0002-test-plugin FAILED' in output)
        assert('Ignore Result   : False' in output)
        assert('Description     : This is Test Plugin 1' in output)

        content = """{
    "ztp": {
        "0001-test-plugin": {
          "sleep" : 10
        },
        "restart-ztp-no-config" : false
    }
}"""
        self.__init_ztp_data()
        runCommand("sed -i 's:DEBUG=\"\":DEBUG=\"yes\":g' /etc/default/ztp")
        runCommand("sed -i 's:TEST_MODE=\"\":TEST_MODE=\"yes\":g' /etc/default/ztp")
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' run -y')
        assert(self.__check_ztp_status(' status', 'ZTP Service    : Active Discovery', 2) == True)
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' status')
        assert('ZTP Status     : Not Started' in output)
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' status -v')
        assert('ZTP Service    : Active Discovery' in output)
        assert('ZTP Status     : Not Started' in output)
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' status -c')
        assert('2:ACTIVE-DISCOVERY' == output[0])
        self.__write_file("/tmp/ztp_input.json", content)
        self.__write_file(self.cfgGet("opt67-url"), "file:///tmp/ztp_input.json")
        os.system("mkdir -p "+self.cfgGet("ztp-run-dir") +"/ztp.lock")
        os.system("echo dhcp:Ethernet4 >" + self.cfgGet("ztp-run-dir")+"/ztp.lock/interface")
        assert(self.__check_ztp_status(' status', 'ZTP Service    : Processing', 5) == True)
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' status')
        assert('ZTP Service    : Processing' in output)
        assert('ZTP Status     : IN-PROGRESS' in output)
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' status -v')
        assert('ZTP Service    : Processing' in output)
        assert('ZTP Status     : IN-PROGRESS' in output)
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' status -c')
        assert('4:IN-PROGRESS' == output[0])
        os.system("systemctl stop ztp")
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD)
        assert(rc != 0)
        (rc, output, err) = runCommand(COVERAGE + ZTP_CMD + ' foo')
        assert(rc != 0)

        runCommand("sed -i 's:DEBUG=\"yes\":DEBUG=\"\":g' /etc/default/ztp")
        runCommand("sed -i 's:TEST_MODE=\"yes\":TEST_MODE=\"\":g' /etc/default/ztp")
        os.rename(getCfg('config-db-json')+'.orig', getCfg('config-db-json'))
        os.remove("/tmp/ztp_input.json")
        self.cfgSet('restart-ztp-interval', 300)
        self.cfgSet('discovery-interval', _discover_interval)
        os.system("rm -rf "+self.cfgGet("ztp-run-dir")+"/ztp.lock")
