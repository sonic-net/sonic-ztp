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
import multiprocessing
import json
import pytest

from .testlib import createPySymlink
from ztp.ZTPLib import runCommand, getCfg
from ztp.DecodeSysEeprom import sysEeprom

sys.path.append(getCfg('plugins-dir'))
createPySymlink(getCfg('plugins-dir')+'/configdb-json')

createPySymlink('/usr/lib/ztp/plugins/configdb-json')
from configdb_json import ConfigDBJson

class TestClass(object):

    '''!
    This class allow to define unit tests for class Snmp
    '''

    def __read_file(self, fname):
        try:
            f = open(fname, 'r')
            return f.read()
        except:
            return None

    def __write_file(self, fname, data):
        try:
            f = open(fname, 'w+')
            f.write(data)
        except Exception as e:
            pass

    def test_constructor_wrong_type(self):
        '''!
        Test case when we call the constructor with the wrong type for the argument
        '''
        with pytest.raises(TypeError) as pytest_wrapped_e:
            configdb_json = ConfigDBJson(123)
        with pytest.raises(TypeError) as pytest_wrapped_e:
            configdb_json = ConfigDBJson([])
        with pytest.raises(TypeError) as pytest_wrapped_e:
            configdb_json = ConfigDBJson(('abc', 'foo'))
        with pytest.raises(TypeError) as pytest_wrapped_e:
            configdb_json = ConfigDBJson(None)

    def test_input_nfound(self, tmpdir):
        '''!
        Test case when input file does not exist
        '''
        configdb_json = ConfigDBJson('/abc/xyz/foo')
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            configdb_json.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_invalid_input(self, tmpdir):
        '''!
        Test case when input file is not json syntaxically valid
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "abc" "foo"
        }
        """)
        configdb_json = ConfigDBJson(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            configdb_json.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_input_no_section(self, tmpdir):
        '''!
        Test case when there is no valid configdb-json related section
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "snmp": {
                "halt-on-failure": false,
                "ignore-result": false,
                "reboot-on-failure": false,
                "reboot-on-success": false,
                "restart-agent": false,
                "status": "BOOT",
                "timestamp": "2019-04-29 16:12:08"
            }
        }
        """)
        configdb_json = ConfigDBJson(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            configdb_json.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_json_config_nvalid(self, tmpdir):
        '''!
        Test case when the new json configuration file to apply is syntaxically incorrect.
        Verify that the plugin return with a non zero exit code.
        '''
        content = """
        #!/bin/sh
        exit 1
        """
        self.__write_file("file:///tmp/test_firmware_"+sysEeprom.get_product_name(), content)
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "configdb-json": {
                "clear-config": false,
                "halt-on-failure": false,
                "ignore-result": false,
                "reboot-on-failure": false,
                "reboot-on-success": false,
                "status": "BOOT",
                "timestamp": "2019-05-01 19:49:25",
                "url": {
                    "destination": "/etc/sonic/config_db.json",
                    "source": "file:///tmp/test_firmware_%s"
                }
            }
        }
        """ %(sysEeprom.get_product_name()))
        configdb_json = ConfigDBJson(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            configdb_json.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_json_config_valid_load(self, tmpdir):
        '''!
        Test case when the new json configuration file to apply is syntaxically valid.
        Verify that the new configuration is correctly applied using 'config load'.
        Verify that the plugin does not return with a non zero exit code.
        '''

        d = tmpdir.mkdir("valid")
        fh_before = d.join("config-before.json")
        cmd = '/usr/bin/config save -y ' + str(fh_before)
        rc = runCommand(cmd, capture_stdout=False)
        assert(rc == 0)

        data = self.__read_file(str(fh_before))
        fh_after = d.join("config-after.json")
        self.__write_file(str(fh_after), data)

        cmd = "/bin/sed -i -e 's/\"hostname\": \".*\"/\"hostname\": \"something\"/' " + str(fh_after)
        rc  = runCommand(cmd)

        fh = d.join("input.json")
        fh.write("""
        {
            "configdb-json": {
                "clear-config": false,
                "halt-on-failure": false,
                "ignore-result": false,
                "reboot-on-failure": false,
                "reboot-on-success": false,
                "status": "BOOT",
                "timestamp": "2019-05-01 19:49:25",
                "url": {
                    "destination": "/etc/sonic/config_db.json",
                    "source": "file://%s"
                }
            }
        }
        """ %(str(fh_after)))
        configdb_json = ConfigDBJson(str(fh))
        configdb_json.main()

        fh_after = d.join("config-after.json")
        cmd = '/usr/bin/config save -y ' + str(fh_after)
        rc = runCommand(cmd, capture_stdout=False)
        assert(rc == 0)

        # Collect the differences between the two configurations
        cmd = "/usr/bin/diff --changed-group-format='%>' --unchanged-group-format='' " + str(fh_before) + ' ' + str(fh_after)
        (rc2, cmd_stdout, cmd_stderr) = runCommand(cmd)

        # Restore initial configuration
        cmd = '/usr/bin/config load -y ' + str(fh_before)
        rc = runCommand(cmd, capture_stdout=False)
        assert(rc == 0)

    def test_json_config_valid_reload(self, tmpdir):
        '''!
        Test case when the new json configuration file to apply is syntaxically valid.
        Verify that the new configuration is correctly applied using 'config reload'.
        Verify that the plugin does not return with a non zero exit code.
        '''

        d = tmpdir.mkdir("valid")
        fh_before = d.join("config-before.json")
        cmd = '/usr/bin/config save -y ' + str(fh_before)
        rc = runCommand(cmd, capture_stdout=False)
        assert(rc == 0)

        data = self.__read_file(str(fh_before))
        fh_after = d.join("config-after.json")
        self.__write_file(str(fh_after), data)

        cmd = "/bin/sed -i -e 's/\"hostname\": \".*\"/\"hostname\": \"something\"/' " + str(fh_after)
        rc  = runCommand(cmd)

        fh = d.join("input.json")
        fh.write("""
        {
            "configdb-json": {
                "clear-config": true,
                "halt-on-failure": false,
                "ignore-result": false,
                "reboot-on-failure": false,
                "reboot-on-success": false,
                "status": "BOOT",
                "timestamp": "2019-05-01 19:49:25",
                "url": {
                    "destination": "/etc/sonic/config_db.json",
                    "source": "file://%s"
                }
            }
        }
        """ %(str(fh_after)))
        configdb_json = ConfigDBJson(str(fh))
        configdb_json.main()

        fh_after = d.join("config-after.json")
        cmd = '/usr/bin/config save -y ' + str(fh_after)
        rc = runCommand(cmd, capture_stdout=False)
        assert(rc == 0)

        # Restore initial configuration
        cmd = '/usr/bin/config reload -y ' + str(fh_before)
        rc = runCommand(cmd, capture_stdout=False)
        assert(rc == 0)
        rc = runCommand('/usr/bin/config save -y', capture_stdout=False)
