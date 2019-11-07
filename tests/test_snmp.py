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

from ztp.ZTPLib import runCommand, getCfg
from .testlib import createPySymlink
sys.path.append(getCfg('plugins-dir'))
createPySymlink(getCfg('plugins-dir') + '/snmp')
from snmp import Snmp

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

    def test_constructor_wrong_type(self):
        '''!
        Test case when we call the constructor with the wrong type for the argument
        '''
        with pytest.raises(TypeError) as pytest_wrapped_e:
            snmp = Snmp(123)
        with pytest.raises(TypeError) as pytest_wrapped_e:
            snmp = Snmp([])
        with pytest.raises(TypeError) as pytest_wrapped_e:
            snmp = Snmp(('abc', 'foo'))
        with pytest.raises(TypeError) as pytest_wrapped_e:
            snmp = Snmp(None)

    def test_input_nfound(self, tmpdir):
        '''!
        Test case when input file does not exist
        '''
        snmp = Snmp('/abc/xyz/foo')
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            snmp.main()
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
        snmp = Snmp(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            snmp.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_input_no_section(self, tmpdir):
        '''!
        Test case when there is no valid snmp related section
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
        snmp = Snmp(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            snmp.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_create_snmp_yml(self, tmpdir):
        '''!
        Test case when the file snmp.yml does not exist:
        verify that the file is being created
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "snmp": {
                "community-ro": "foo",
                "halt-on-failure": false,
                "ignore-result": false,
                "reboot-on-failure": false,
                "reboot-on-success": false,
                "restart-agent": true,
                "snmp-location": "public",
                "status": "BOOT",
                "timestamp": "2019-04-29 16:12:08"
            }
        }
        """)
        snmp = Snmp(str(fh))
        fh_snmp_yml = d.join("snmp.yml")
        snmp._Snmp__snmp_yml = str(fh_snmp_yml)
        snmp.main()
        f = self.__read_file(str(fh_snmp_yml))
        assert(f == """snmp_rocommunity: foo
snmp_location: public
""")

    def test_update_snmp_yml_case1(self, tmpdir):
        '''!
        Test case when the file snmp.yml already exist:
        verify that the file is being updated
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "snmp": {
                "community-ro": "foo",
                "halt-on-failure": false,
                "ignore-result": false,
                "reboot-on-failure": false,
                "reboot-on-success": false,
                "restart-agent": false,
                "snmp-location": "public",
                "status": "BOOT",
                "timestamp": "2019-04-29 16:12:08"
            }
        }
        """)
        snmp = Snmp(str(fh))
        fh_snmp_yml = d.join("snmp.yml")
        fh_snmp_yml.write("""snmp_rocommunity: ABC
snmp_location: DEF
""")
        snmp._Snmp__snmp_yml = str(fh_snmp_yml)
        snmp.main()
        f = self.__read_file(str(fh_snmp_yml))
        assert(f == """snmp_rocommunity: foo
snmp_location: public
""")

    def test_update_snmp_yml_case2(self, tmpdir):
        '''!
        Test case when the file snmp.yml already exist:
        verify that the file is being updated
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "snmp": {
                "community-ro": "foo",
                "halt-on-failure": false,
                "ignore-result": false,
                "reboot-on-failure": false,
                "reboot-on-success": false,
                "restart-agent": false,
                "snmp-location": "public",
                "status": "BOOT",
                "timestamp": "2019-04-29 16:12:08"
            }
        }
        """)
        snmp = Snmp(str(fh))
        fh_snmp_yml = d.join("snmp.yml")
        fh_snmp_yml.write("""snmp_rocommunity: foo
snmp_location: DEF
""")
        snmp._Snmp__snmp_yml = str(fh_snmp_yml)
        snmp.main()
        f = self.__read_file(str(fh_snmp_yml))
        assert(f == """snmp_rocommunity: foo
snmp_location: public
""")

    def test_update_snmp_yml_case3(self, tmpdir):
        '''!
        Test case when the file snmp.yml already exist:
        verify that the file is being updated
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "snmp": {
                "community-ro": "foo",
                "halt-on-failure": false,
                "ignore-result": false,
                "reboot-on-failure": false,
                "reboot-on-success": false,
                "restart-agent": false,
                "snmp-location": "public",
                "status": "BOOT",
                "timestamp": "2019-04-29 16:12:08"
            }
        }
        """)
        snmp = Snmp(str(fh))
        fh_snmp_yml = d.join("snmp.yml")
        fh_snmp_yml.write("""snmp_location: public
""")
        snmp._Snmp__snmp_yml = str(fh_snmp_yml)
        snmp.main()
        f = self.__read_file(str(fh_snmp_yml))
        assert(f == """snmp_location: public
snmp_rocommunity: foo
""")
