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
import stat
import socket

import pytest

from ztp.ZTPObjects import Identifier
from ztp.DecodeSysEeprom import sysEeprom

class TestClass(object):

    '''!
    \brief This class allow to define unit tests for class Identifier

    Examples of class usage:

    \code
    pytest-2.7 -v -x test_Logger.py
    \endcode
    '''

    def test_hostname(self):
        '''!
        Test when we call the constructor function using hostname
        '''

        id = Identifier('hostname')
        v = id.getIdentifier()
        assert(v == socket.gethostname())

    def test_sonic_version(self):
        '''!
        Test when we call the constructor function using sonic-version
        '''

        id = Identifier('sonic-version')
        v = id.getIdentifier()
        build_version = None
        with open('/etc/sonic/sonic_version.yml') as fp:
            line = fp.readline()
            while line:
                version_info = line.split(':')
                if version_info[0] == 'build_version':
                    ver = version_info[1].strip()
                    ver = ver.lstrip('\'')
                    ver = ver.rstrip('\'')
                    build_version = 'SONiC.{}'.format(ver)
                    break
                line = fp.readline()
        fp.close()
        assert(v == build_version)

    def test_hostname_fqdn(self):
        '''!
        Test when we call the constructor function using hostname-fqdn
        '''

        id = Identifier('hostname-fqdn')
        v = id.getIdentifier()
        assert(v == socket.getfqdn())

    def test_serial_number(self):
        '''!
        Test when we call the constructor function using the serial number
        '''

        id = Identifier('serial-number')
        v = id.getIdentifier()
        assert(v == sysEeprom.get_serial_number())

    def test_product_name(self):
        '''!
        Test when we call the constructor function using the product name
        '''

        id = Identifier('product-name')
        v = id.getIdentifier()
        assert(v == sysEeprom.get_product_name())

    def test_other(self):
        '''!
        Test when we call the constructor function using the product name
        '''

        id = Identifier('other')
        v = id.getIdentifier()
        assert(v == 'other')

    def test_wrong_parameter1(self):
        dl = [('url', 'other')]
        d = dict(dl)
        id = Identifier(d)
        v = id.getIdentifier()
        assert(v == None)

    def test_wrong_parameter2(self):
        dl = [('url', [1])]
        d = dict(dl)
        id = Identifier(d)
        v = id.getIdentifier()
        assert(v == None)

    def test_get_url1(self, tmpdir):
        dt = tmpdir.mkdir("valid")
        fh = dt.join("input.txt")
        content = '#!/bin/sh\n\necho "Hello"'
        fh.write(content)
        dl = [('url', 'file://'+str(fh))]
        d = dict(dl)
        id = Identifier(d)
        v = id.getIdentifier()
        assert(v == 'Hello')

    def test_get_url2(self, tmpdir):
        dt = tmpdir.mkdir("valid")
        fh = dt.join("input.txt")
        content = '#!/bin/sh\n\necho "Hello"'
        fh.write(content)
        dl_url = [('source', 'file://'+str(fh)), ('destination', 'abc')]
        d_url = dict(dl_url)
        dl = [('url', d_url)]
        d = dict(dl)
        id = Identifier(d)
        v = id.getIdentifier()
        assert(v == 'Hello')

    def test_get_url3(self, tmpdir):
        dt = tmpdir.mkdir("valid")
        fh = dt.join("input.txt")
        content = 'XYZ ABC'
        fh.write(content)
        dl_url = [('source', 'file://'+str(fh)), ('destination', 'abc')]
        d_url = dict(dl_url)
        dl = [('url', d_url)]
        d = dict(dl)
        id = Identifier(d)
        v = id.getIdentifier()
        assert(v == None)

    def test_get_url4(self, tmpdir):
        dt = tmpdir.mkdir("valid")
        fh = dt.join("input.txt")
        content = '#!/bin/sh\nexit -1'
        fh.write(content)
        dl_url = [('source', 'file://'+str(fh)), ('destination', 'abc')]
        d_url = dict(dl_url)
        dl = [('url', d_url)]
        d = dict(dl)
        id = Identifier(d)
        v = id.getIdentifier()
        assert(v == None)

    def test_get_url5(self, tmpdir):
        dt = tmpdir.mkdir("valid")
        fh = dt.join("input.txt")
        content = '#!/bin/sh\n\necho "Hello"'
        fh.write(content)
        dl = [('url', None)]
        d = dict(dl)
        id = Identifier(d)
        v = id.getIdentifier()
        assert(v == None)
