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
import pytest

from ztp.ZTPObjects import URL

class TestClass(object):

    '''!
    \brief This class allow to define unit tests for class URL

    Examples of class usage:

    \code
    pytest-2.7 -v -x test_Logger.py
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

    def test_constructor1(self):
        '''!
        Test when we call the constructor function with incomplete or wrong parameters
        '''
        with pytest.raises(TypeError):
            url = URL()
        with pytest.raises(TypeError):
            url = URL(123)
        with pytest.raises(TypeError):
            url = URL([1])
        with pytest.raises(TypeError):
            url = URL([1, 2, 3])
        with pytest.raises(TypeError):
            url = URL((1))
        with pytest.raises(TypeError):
            url = URL((1, 2, 3))
        url = URL('http://localhost://2000/foo.txt')
        assert(url != None)

    def test_constructor2(self):
        '''!
        Test when we call the constructor function with incomplete or wrong parameters
        '''
        url = URL('http://localhost://2000/foo.txt')
        assert(url != None)
        assert(url.getSource() == 'http://localhost://2000/foo.txt')

        dl = [('foo', 'http://server:8080/file.txt')]
        d = dict(dl)
        with pytest.raises(TypeError):
            url = URL(d)

        dl = [('source', 'http://server:8080/file.txt')]
        d = dict(dl)
        url = URL(d)
        assert(url != None)

        dl = [('foo', 'http://server:8080/file.txt')]
        d = dict(dl)
        with pytest.raises(TypeError):
            url = URL(d)

        dl = [('source', 123)]
        d = dict(dl)
        with pytest.raises(TypeError):
            url = URL(d)

        url = URL('http://localhost://2000/foo.txt', 123)
        assert(url != None)

        with pytest.raises(TypeError):
            url = URL(None)

        dl = [('source', 'http://server:8080/file.txt'), ('destination', 123)]
        d = dict(dl)
        with pytest.raises(TypeError):
            url = URL(d)

        dl = [('source', 'http://server:8080/file.txt'), ('destination', 'abc')]
        d = dict(dl)
        url = URL(d)
        assert(url != None)

        dl = [('source', 'http://server:8080/file.txt')]
        d = dict(dl)
        url = URL(d, 'abc')
        assert(url != None)

        dl = [('source', 'http://server:8080/file.txt')]
        d = dict(dl)
        with pytest.raises(TypeError):
            url = URL(d, 123)

    def test_download(self, tmpdir):
        '''!
        Test the download method with destination specified in constructor
        '''

        url = URL('http://localhost://2000/foo.txt')
        assert(url != None)
        result = url.download()
        assert(result == (20, None))

        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        content = 'Hello the world test_download!'
        fh.write(content)
        url = URL('file://'+str(fh), self.__filename('test.txt'))
        (rc, fname) = url.download()
        assert(rc == 0)
        assert(fname == self.__filename('test.txt'))
        assert(self.__read_file(fname) == content)

    def test_download2(self, tmpdir):
        '''!
        Test the download method with destination specified in url_data
        '''

        dt = tmpdir.mkdir("valid")
        fh = dt.join("input.txt")
        content = 'Hello the world test_download2!'
        fh.write(content)
        dl = [('source', 'file://'+str(fh)), ('destination', self.__filename('test.txt'))]
        d = dict(dl)
        url = URL(d)
        (rc, fname) = url.download()
        assert(rc == 0)
        assert(fname == self.__filename('test.txt'))
        assert(self.__read_file(fname) == content)

    def test_download3(self, tmpdir):
        '''!
        Test the download method with destination specified in url_data and optional destination specified
        '''

        dt = tmpdir.mkdir("valid")
        fh = dt.join("input.txt")
        content = 'Hello the world test_download3!'
        fh.write(content)
        dl = [('source', 'file://'+str(fh)), ('destination', self.__filename('test.txt'))]
        d = dict(dl)
        url = URL(d, self.__filename('test3.txt'))
        (rc, fname) = url.download()
        assert(rc == 0)
        assert(fname == self.__filename('test.txt'))
        assert(self.__read_file(fname) == content)


    def test_download4(self, tmpdir):
        '''!
        Test the download method with destination not specified in url_data and optional destination specified
        '''

        dt = tmpdir.mkdir("valid")
        fh = dt.join("input.txt")
        content = 'Hello the world test_download4!'
        fh.write(content)
        dl = [('source',  'file://'+str(fh))]
        d = dict(dl)
        url = URL(d, self.__filename('test.txt'))
        (rc, fname) = url.download()
        assert(rc == 0)
        assert(fname == self.__filename('test.txt'))
        assert(self.__read_file(fname) == content)
