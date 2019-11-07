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
import time
import shutil
import stat

from .testlib import HttpServer, data

from ztp.Downloader import Downloader
from ztp.defaults import *

ZTP_CFG_JSON=cfg_file

class TestClass(object):

    '''!
    \brief This class allow to define unit tests for class Downloader

    Examples of class usage:

    \code
    pytest-2.7 -v -x test_Downloader.py
    \endcode
    '''

    def __filename(self, fname):
        return os.getcwd() + '/' + fname

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
        assert(os.path.isfile(ZTP_CFG_JSON) is True)
        dn = Downloader('')
        assert(dn != None)
        dn = Downloader(123)
        assert(dn != None)
        dn = Downloader([1])
        assert(dn != None)
        dn = Downloader([1, 2, 3])
        assert(dn != None)
        dn = Downloader((1))
        assert(dn != None)
        dn = Downloader(ZTP_CFG_JSON, '/tmp/test.json', incl_http_headers=True, is_secure=False, timeout=30, retry=3, curl_args='', encrypted=False)
        assert(dn != None)
        dn.getUrl()
        dn = Downloader(ZTP_CFG_JSON, is_secure=True)
        assert(dn != None)
        dn.getUrl(is_secure=None)

    def test_getUrl_hardening(self):
        '''!
        Test when we call the download function with incomplete or wrong parameters
        '''
        dn = Downloader()
        assert(dn != None)
        try:
            assert(dn.getUrl() == (-1, None))
            assert(dn.getUrl('') == (20, None))
            dn.getUrl(123)
        except (TypeError, AttributeError) as e:
            print('Exception: %s' % (e))
        try:
            dn.getUrl([1])
        except (TypeError, AttributeError) as e:
            print('Exception: %s' % (e))
        try:
            dn.getUrl([1, 2, 3])
        except (TypeError, AttributeError) as e:
            print('Exception: %s' % (e))
        try:
            dn.getUrl((1))
        except (TypeError, AttributeError) as e:
            print('Exception: %s' % (e))

    def test_unsupported_protocols(self):
        '''!
        Test unsupported protocol
        '''
        http = HttpServer()
        dn = Downloader()
        http.start()
        (rc, fname) = dn.getUrl('ABCXYZ://localhost:2001/test.txt', self.__filename('test.txt'), verbose=True)
        assert(rc == 20)
        (rc, fname) = dn.getUrl('abc://foo', '/a/b/c/d/destination_file')
        assert(rc == 20)
        assert(fname == None)
        http.stop()

    def test_http_fail_to_connect(self):
        '''!
        Test http:failed to connect
        '''
        http = HttpServer()
        dn = Downloader()
        http.start()
        (rc, fname) = dn.getUrl('http://localhost:2001/test.txt', self.__filename('test.txt'))
        http.stop()
        assert(rc == 20)

    def test_http_host_resolve(self):
        '''!
        Test http: could not resolve host
        '''
        http = HttpServer()
        dn = Downloader()
        http.start()
        (rc, fname) = dn.getUrl('http:localhost:2000', self.__filename('test.txt'), verbose=True)
        http.stop()
        assert(rc == 20)

    def test_http_not_found(self):
        '''!
        Test http: not found
        '''
        http = HttpServer()
        dn = Downloader()
        http.start(http_error_code=400)
        (rc, fname) = dn.getUrl('http://localhost:2000', self.__filename('test.txt'))
        http.stop()
        assert(rc == 20)

    def test_http_write_error(self):
        '''!
        Test http: write error
        '''
        http = HttpServer()
        dn = Downloader()
        http.start()
        (rc, fname) = dn.getUrl('http://localhost:2000', '/a/b/c/foo/test/xyz')
        http.stop()
        assert(rc == 20)

    def test_http_url_malformed(self):
        '''!
        Test http: url malformed
        '''
        http = HttpServer()
        dn = Downloader()
        http.start()
        (rc, fname) = dn.getUrl('file://A/a/B/b/C/c/foo', self.__filename('test.txt'), verbose=True)
        http.stop()
        assert(rc == 20)

    def test_http_read_file(self):
        '''!
        Test http: retrieve sucessfully a file from http server, save it on disk,
        and verify its integrity
        '''
        content = 'Hello the world!'
        http = HttpServer()
        dn = Downloader()
        http.start(text=content)
        (rc, fname) = dn.getUrl('http://localhost:2000/test.txt', self.__filename('test.txt'), is_secure=False)
        http.stop()
        assert(rc == 0)
        assert(fname == self.__filename('test.txt'))
        assert(self.__read_file(fname) == content)

    def test_http_read_file_write_error(self, tmpdir):
        '''!
        Test http: retrieve sucessfully a file from http server, try it to save as
        an existent directory filename
        '''
        d = tmpdir.mkdir("valid")
        content = 'Hello the world!'
        http = HttpServer()
        dn = Downloader()
        http.start(text=content)
        (rc, fname) = dn.getUrl('http://localhost:2000/test.txt', d, is_secure=False)
        http.stop()
        assert(rc == 20)
        assert(fname == None)

    def test_http_timeout(self):
        '''!
        Test http: timeout
        '''
        http = HttpServer()
        dn = Downloader()
        http.start(timeout=10)
        # Use non routable IP address
        (rc, fname) = dn.getUrl('http://10.255.255.1:2000/test.txt', self.__filename('test.txt'), timeout=20)
        http.stop()
        assert(rc == 20)
        # Not able to resolve server hostname via DNS
        (rc, fname) = dn.getUrl('http://foo-ae6951e8-0a8c-46c8-b443-4eec0fffeb4d/test.txt', self.__filename('test.txt'), timeout=20)
        assert(rc == 20)

    def test_ftp_timeout(self):
        '''!
        Test ftp: timeout
        '''
        http = HttpServer()
        dn = Downloader()
        http.start()
        # Use non routable IP address
        (rc, fname) = dn.getUrl('ftp://10.255.255.1:2000/test.txt', self.__filename('test.txt'), timeout=10)
        http.stop()
        assert(rc == 20)
        # Not able to resolve server hostname via DNS
        (rc, fname) = dn.getUrl('ftp://foo-ae6951e8-0a8c-46c8-b443-4eec0fffeb4d/test.txt', self.__filename('test.txt'), timeout=10)
        assert(rc == 20)

    def test_http_curl_not_found(self):
        '''!
        Test: curl utility not found
        '''
        shutil.move('/usr/bin/curl', '/usr/bin/curl_org')
        f = open('/usr/bin/curl', 'w')
        f.write('#!/bin/sh\nexit 1\n')
        f.close()
        st = os.stat('/usr/bin/curl')
        os.chmod('/usr/bin/curl', st.st_mode | stat.S_IEXEC)
        dn = Downloader()
        (rc, fname) = dn.getUrl(ZTP_CFG_JSON)
        shutil.move('/usr/bin/curl_org', '/usr/bin/curl')
        assert(rc == 20)
        assert(fname == None)
