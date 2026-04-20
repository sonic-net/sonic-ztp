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
import pytest

from ztp.ZTPLib import runCommand, getCfg
from .testlib import createPySymlink
sys.path.append(getCfg('plugins-dir'))

createPySymlink(getCfg('plugins-dir')+'/connectivity-check')
from connectivity_check import ConnectivityCheck

class TestClass(object):

    '''!
    This class allow to define unit tests for class ConnectivityCheck
    '''

    def test_data_hardening_test1(self, tmpdir):
        '''!
        Test case when we call the plugin with incomplete or wrong data
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "Foo": "empty"
        }
        """)
        connectivity_check = ConnectivityCheck(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            connectivity_check.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_data_hardening_test2(self, tmpdir):
        '''!
        Test case when we call the plugin with incomplete or wrong data
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "ztp": { }
        }
        """)
        connectivity_check = ConnectivityCheck(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            connectivity_check.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_ping_localhost(self, tmpdir):
        '''!
        Test case pinging IPV4 localhost:
        Verify that pinging IPV4 localhost succeeds
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
                "connectivity-check": {
                    "ping-hosts": "127.0.0.1",
                    "deadline": 15
                  }
        }
        """)
        connectivity_check = ConnectivityCheck(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            connectivity_check.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 0

    def test_ping_localhost_interface_nok(self, tmpdir):
        '''!
        Test case pinging IPV4 localhost using an interface:
        Verify that pinging IPV4 localhost fails on non existent interface
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
                "connectivity-check": {
                    "ping-hosts": "127.0.0.1",
                    "interface": "ethX",
                    "retry-count": 2,
                    "retry-interval": 15,
                    "timeout": "10"
                  }
        }
        """)
        connectivity_check = ConnectivityCheck(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            connectivity_check.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_ping_localhost_interface_ok(self, tmpdir):
        '''!
        Test case pinging IPV4 localhost using an interface:
        Verify that pinging IPV4 localhost succeeds on existent interface
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
                "connectivity-check": {
                    "ping-hosts": "127.0.0.1",
                    "interface": "lo",
                    "deadline": 15
                  }
        }
        """)
        connectivity_check = ConnectivityCheck(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            connectivity_check.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 0

    def test_ping_localhost_args_nok(self, tmpdir):
        '''!
        Test case pinging IPV4 localhost using arguments:
        Verify that pinging IPV4 localhost fails on non existent interface
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
                "connectivity-check": {
                    "ping-hosts": "127.0.0.1",
                    "args": "-I ethX",
                    "retry-count": 2,
                    "retry-interval": 15,
                    "timeout": "10"
                  }
        }
        """)
        connectivity_check = ConnectivityCheck(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            connectivity_check.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_ping_localhost_args_ok(self, tmpdir):
        '''!
        Test case pinging IPV4 localhost using arguments:
        Verify that pinging IPV4 localhost succeeds on existent interface
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
                "connectivity-check": {
                    "ping-hosts": "127.0.0.1",
                    "args": "-I lo",
                    "deadline": 15
                  }
        }
        """)
        connectivity_check = ConnectivityCheck(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            connectivity_check.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 0

    def test_ping_non_routable_address(self, tmpdir):
        '''!
        Test case pinging non routable IPV4 address:
        Verify that pinging IPV4 non routable address fails
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
                "01-connectivity-check": {
                    "retry-count": 2,
                    "retry-dhcp" : true,
                    "retry-interval": 15,
                    "timeout": "10",
                    "ping-hosts": ["192.0.2.1", 123]
                  }
        }
        """)
        (rc, interfaces_exit_time, cmd_stderr) = runCommand("systemctl show --value -p ExecMainExitTimestampMonotonic interfaces-config")
        connectivity_check = ConnectivityCheck(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            connectivity_check.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1
        (rc, interfaces_exit_time_new, cmd_stderr) = runCommand("systemctl show --value -p ExecMainExitTimestampMonotonic interfaces-config")
        assert (int(interfaces_exit_time_new[0]) > int(interfaces_exit_time[0]))

    def test_ping_ipv6_localhost(self, tmpdir):
        '''!
        Test case pinging IPV6 localhost
        Verify that pinging IPV6 localhost succeeds
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
                "connectivity-check": {
                    "ping6-hosts": ["0:0:0:0:0:0:0:1"],
                    "retry-count": -2,
                    "retry-interval": -15
                  }
        }
        """)
        connectivity_check = ConnectivityCheck(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            connectivity_check.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 0

    def test_ping_ipv6_localhost_interface_nok(self, tmpdir):
        '''!
        Test case pinging IPV6 localhost using an interface
        Verify that pinging IPV6 localhost fails
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
                "connectivity-check": {
                    "ping6-hosts": ["0:0:0:0:0:0:0:1"],
                    "interface": "ethX",
                    "retry-count": 2,
                    "retry-interval": 15,
                    "timeout": "10"
                  }
        }
        """)
        connectivity_check = ConnectivityCheck(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            connectivity_check.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_ping_ipv6_localhost_interface_ok(self, tmpdir):
        '''!
        Test case pinging IPV6 localhost using an interface
        Verify that pinging IPV6 localhost succeeds
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
                "connectivity-check": {
                    "ping6-hosts": ["0:0:0:0:0:0:0:1"],
                    "interface": "lo",
                    "retry-count": -2,
                    "retry-interval": -15
                  }
        }
        """)
        connectivity_check = ConnectivityCheck(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            connectivity_check.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 0

    def test_ping_ipv6_non_routable_address(self, tmpdir):
        '''!
        Test case pinging non routable IPV6 address:
        Verify that pinging IPV6 non routable address fails
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
                "connectivity-check": {
                    "ping6-hosts": ["0:0:0:0:0:0:0:1", "fe:80:0:0:0:0:0:1"],
                    "retry-count": 2
                  }
        }
        """)
        connectivity_check = ConnectivityCheck(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            connectivity_check.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1
