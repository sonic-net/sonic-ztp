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
import signal
import os
import stat
import pytest

from ztp.ZTPLib import runCommand, getField, getCfg, printable
sys.path.append(getCfg('plugins-dir'))

class TestClass(object):

    '''!
    This class allow to define unit tests for class Firmware
    \endcode
    '''

    def test_cmd(self, tmpdir):

        (rc1, cmd_stdout1, cmd_stderr1) = runCommand('/bin/cat /proc/devices')
        (rc2, cmd_stdout2, cmd_stderr2) = runCommand('/bin/cat /proc/devices', use_shell=True)
        (rc3, cmd_stdout3, cmd_stderr3) = runCommand(['/bin/cat', '/proc/devices'])
        (rc4, cmd_stdout4, cmd_stderr4) = runCommand(['/bin/cat', '/proc/devices'], use_shell=True)
        assert((rc1 == rc2) and (rc2 == rc3) and (rc3 == rc4))
        assert((cmd_stdout1 == cmd_stdout2) and (cmd_stdout2 == cmd_stdout3) and (cmd_stdout3 == cmd_stdout4))
        assert((cmd_stderr1 == cmd_stderr2) and (cmd_stderr2 == cmd_stderr3) and (cmd_stderr3 == cmd_stderr4))

        (rc5, cmd_stdout5, cmd_stderr5) = runCommand(['touch', '/tmp/test_file_644'], use_shell=True, umask=0o022)
        st = os.stat('/tmp/test_file_644')
        assert(0o644, oct(st.st_mode))
        (rc6, cmd_stdout6, cmd_stderr6) = runCommand(['touch', '/tmp/test_file_600'], use_shell=True, umask=0o177)
        st = os.stat('/tmp/test_file_600')
        assert(0o600, oct(st.st_mode))
        runCommand("rm -f /tmp/test_file_644 /tmp/test_file_600")

        (rc1, cmd_stdout1, cmd_stderr1) = runCommand('ps hjk')
        (rc2, cmd_stdout2, cmd_stderr2) = runCommand('ps hjk', use_shell=True)
        (rc3, cmd_stdout3, cmd_stderr3) = runCommand(['ps', 'hjk'])
        (rc4, cmd_stdout4, cmd_stderr4) = runCommand(['ps', 'hjk'], use_shell=True)
        assert((rc1 == rc2) and (rc2 == rc3) and (rc3 == rc4))
        assert((cmd_stdout1 == cmd_stdout2) and (cmd_stdout2 == cmd_stdout3) and (cmd_stdout3 == cmd_stdout4))
        assert((cmd_stderr1 == cmd_stderr2) and (cmd_stderr2 == cmd_stderr3) and (cmd_stderr3 == cmd_stderr4))

        d = tmpdir.mkdir("valid")
        fh = d.join("test.sh")
        fh.write("""#!/bin/sh

        echo $1
        echo $2 > /dev/stderr
        exit $#
        """)
        os.chmod(str(fh), stat.S_IRWXU)
        (rc1, cmd_stdout1, cmd_stderr1) = runCommand(str(fh) + ' ABC XYZ')
        (rc2, cmd_stdout2, cmd_stderr2) = runCommand(str(fh) + ' ABC XYZ', use_shell=True)
        (rc3, cmd_stdout3, cmd_stderr3) = runCommand([str(fh), 'ABC', 'XYZ'])
        (rc4, cmd_stdout4, cmd_stderr4) = runCommand([str(fh), 'ABC', 'XYZ'], use_shell=True)
        assert((rc1 == rc2) and (rc2 == rc3) and (rc3 == rc4))
        assert((cmd_stdout1 == cmd_stdout2) and (cmd_stdout2 == cmd_stdout3) and (cmd_stdout3 == cmd_stdout4))
        assert((cmd_stderr1 == cmd_stderr2) and (cmd_stderr2 == cmd_stderr3) and (cmd_stderr3 == cmd_stderr4))

    def test_getField(self):
        data = dict({'key': 'val'})
        assert (getField(data, 'key', str, 'defval') == 'val')

        data = dict({'key': 10})
        assert (getField(data, 'key', str, 'defval') == 'defval')

        data = dict({'key': 'val'})
        assert (getField(data, 'key2', str, 'defval') == 'defval')

        data = dict({'key': True})
        assert (getField(data, 'key', bool, False) == True)

        data = dict({'key': 'TrUe'})
        assert (getField(data, 'key', bool, False) == True)

        data = dict({'key': 'fTrUe'})
        assert (getField(data, 'key', bool, False) == False)

        data = dict({'key': 'FalSe'})
        assert (getField(data, 'key2', bool, True) == True)

        data = dict({'key': 'FalSe'})
        assert (getField(data, 'key', bool, True) == False)

        data = dict({'key': 10})
        assert (getField(data, 'key', int, 20) == 10)

        data = dict({'key': "20"})
        assert (getField(data, 'key', int, 10) == 20)

        data = dict({'key': "abc"})
        assert (getField(data, 'key', int, 10) == 10)

        data = dict({'key': None})
        assert (getField(data, 'key', int, 10) == 10)

        assert (getField(None, 'key', int, 10) == 10)
        assert (getField(None, None, int, 10) == 10)

        data = dict({'key': '10'})
        assert (getField(data, 'key2', int, 20) == 20)

        data = dict({'key': '10'})
        assert (getField(data, 'key', dict, None) == None)

        data = dict({'key': {'subkey':10} })
        assert (getField(data, 'key', dict, None).get('subkey') == 10)

    def test_misc(self):
        assert(printable("Test-/\=$!()*#!_?><,.][{}+String1234567890") == "Test-/\=$!()*#!_?><,.][{}+String1234567890")
        assert(printable("Te\u20ACst\u20AC") == "Test")
        assert(printable("\u20AC\u20AC") == "")
        assert(printable(None) == None)
        assert(printable({"k": "v"}) == None)
        assert(printable("") == "")
