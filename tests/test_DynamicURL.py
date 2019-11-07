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

from ztp.ZTPObjects import DynamicURL
from ztp.ZTPObjects import Identifier

from ztp.DecodeSysEeprom import sysEeprom

class TestClass(object):

    '''!
    \brief This class allow to define unit tests for class DynamicURL

    Examples of class usage:

    \code
    pytest-2.7 -v -x test_Logger.py
    \endcode
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

    def test_constructor1(self):
        '''!
        Test when we call the constructor function with incomplete or wrong parameters
        '''

        with pytest.raises(TypeError):
            durl = DynamicURL()

        dl_url = [('source', 'http://localhost:2000/test.txt'), ('destination', 'abc')]
        d_url = dict(dl_url)
        with pytest.raises(TypeError):
            durl = DynamicURL(d_url)

    def test_constructor2(self):
        '''!
        Test when we call the constructor function with incomplete or wrong parameters
        '''

        dl = [('identifier', 'product-name')]
        d = dict(dl)
        dl_url = [('source', d)]
        d_url = dict(dl_url)
        durl = DynamicURL(d_url)
        s = durl.getSource();
        assert(s == sysEeprom.get_product_name())

    def test_constructor3(self):
        '''!
        Test when we call the constructor function with incomplete or wrong parameters
        '''

        dl = [('identifier', 'product-name')]
        d = dict(dl)
        dl_url = [('source', d)]
        d_url = dict(dl_url)
        durl = DynamicURL(d_url, 'abc')
        with pytest.raises(TypeError):
            durl = DynamicURL(d_url, [12])

    def test_constructor4(self):
        '''!
        Test when we call the constructor function with incomplete or wrong parameters
        '''

        dl = [('identifier', 123)]
        d = dict(dl)
        dl_url = [('source', d)]
        d_url = dict(dl_url)
        with pytest.raises(TypeError):
            durl = DynamicURL(d_url)

    def test_constructor5(self):
        '''!
        Test when we call the constructor function with incomplete or wrong parameters
        '''

        dl = [('identifier', 'product-name'), ('prefix', 'XYZ_')]
        d = dict(dl)
        dl_url = [('source', d)]
        d_url = dict(dl_url)
        durl = DynamicURL(d_url)
        s = durl.getSource();
        assert(s == 'XYZ_'+sysEeprom.get_product_name())

    def test_constructor6(self):
        '''!
        Test when we call the constructor function with incomplete or wrong parameters
        '''

        dl = [('identifier', 'product-name'), ('prefix', 123)]
        d = dict(dl)
        dl_url = [('source', d)]
        d_url = dict(dl_url)
        with pytest.raises(TypeError):
            durl = DynamicURL(d_url)

    def test_constructor7(self):
        '''!
        Test when we call the constructor function with incomplete or wrong parameters
        '''

        dl = [('identifier', dict([('url', None)]) )]
        d = dict(dl)
        dl_url = [('source', d)]
        d_url = dict(dl_url)
        with pytest.raises(ValueError):
            durl = DynamicURL(d_url)

    def test_constructor8(self):
        '''!
        Test when we call the constructor function with incomplete or wrong parameters
        '''

        dl = [('identifier', 'product-name'), ('suffix', '_XYZ')]
        d = dict(dl)
        dl_url = [('source', d)]
        d_url = dict(dl_url)
        durl = DynamicURL(d_url)
        s = durl.getSource();
        assert(s == sysEeprom.get_product_name()+'_XYZ')

    def test_constructor9(self):
        '''!
        Test when we call the constructor function with incomplete or wrong parameters
        '''

        dl = [('identifier', 'product-name'), ('suffix', 123)]
        d = dict(dl)
        dl_url = [('source', d)]
        d_url = dict(dl_url)
        with pytest.raises(TypeError):
            durl = DynamicURL(d_url)

    def test_download1(self):
        '''!
        Test when we call download() method
        '''

        dl = [('identifier', 'product-name'), ('prefix', 'XYZ_')]
        d = dict(dl)
        dl_url = [('source', d)]
        d_url = dict(dl_url)
        durl = DynamicURL(d_url)
        s = durl.getSource();
        assert(s == 'XYZ_'+sysEeprom.get_product_name())
        durl.download();

    def test_download2(self):
        '''!
        Test when we call download() method
        '''

        content = 'Hello the world!'
        self.__write_file("/tmp/test_firmware_"+sysEeprom.get_product_name(), content)

        dl = [('identifier', 'product-name'), ('prefix', 'file:///tmp/test_firmware_')]
        d = dict(dl)
        dl_url = [('source', d)]
        d_url = dict(dl_url)
        durl = DynamicURL(d_url)
        s = durl.getSource()
        assert(s == 'file:///tmp/test_firmware_'+sysEeprom.get_product_name())

        rc, dest = durl.download();
        assert(rc == 0)
        assert(self.__read_file(dest) == content)
