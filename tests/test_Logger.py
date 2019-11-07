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
import stat
import pytest
import syslog
import subprocess

from ztp.Logger import Logger
from ztp.ZTPLib import getCfg, setCfg, getTimestamp
from ztp.defaults import *

ZTP_CFG_JSON=cfg_file

class TestClass(object):

    '''!
    \brief This class allow to define unit tests for class Logger

    Examples of class usage:

    \code
    pytest-2.7 -v -x test_Logger.py
    \endcode
    '''

    def __search_file(self, fname, msg):
        try:
            subprocess.check_call(['grep', '-q', msg, fname])
        except:
            pass
            return False
        return True

    def __read_file(self, fname):
        try:
            f = open(fname, 'r')
            content = f.read()
            f.close()
            return content
        except:
            return None

    def test_constructor1(self):
        '''!
        Test when we call the constructor function with incomplete or wrong parameters
        '''
        log = Logger('')
        assert(log != None)
        log = Logger(123)
        assert(log != None)
        with pytest.raises(TypeError):
            log = Logger([1])
        with pytest.raises(TypeError):
            log = Logger([1, 2, 3])
        log = Logger((1))
        assert(log != None)
        with pytest.raises(TypeError):
            log = Logger(123, 234, 456)
        log = Logger(log_level=123)
        assert(log != None)
        with pytest.raises(TypeError):
            log = Logger(123, log_file=123)

    def test_constructor2(self):
        '''!
        Test when we call the constructor function with incomplete or wrong parameters
        '''
        shutil.move(ZTP_CFG_JSON, ZTP_CFG_JSON+'.orig')
        f = open(ZTP_CFG_JSON, 'w')
        f.write('{"log-level" : 123, "log-file" : False}\n')
        f.close()
        log = Logger()
        assert(log != None)
        shutil.move(ZTP_CFG_JSON+'.orig', ZTP_CFG_JSON)

    def test_constructor3(self):
        '''!
        Test when we call the constructor function with incomplete or wrong parameters
        '''
        shutil.move(ZTP_CFG_JSON, ZTP_CFG_JSON+'.orig')
        f = open(ZTP_CFG_JSON, 'w')
        f.write('{"log-level" : "INFO"}\n')
        f.close()
        log = Logger()
        assert(log != None)
        shutil.move(ZTP_CFG_JSON+'.orig', ZTP_CFG_JSON)

    def test_setLevel(self):
        '''!
        Test setLevel() method
        '''
        log = Logger('')
        assert(log != None)
        s = log.setLevel(-1)
        assert(s == None)
        s = log.setLevel('')
        assert(s == None)
        s = log.setLevel('abc')
        assert(s == None)
        s = log.setLevel('debug')
        assert(s == None)
        assert(log.getLevel() == syslog.LOG_DEBUG)
        s = log.setLevel('warning')
        assert(s == None)
        assert(log.getLevel() == syslog.LOG_WARNING)
        s = log.setLevel('xyz')
        assert(s == None)
        assert(log.getLevel() == syslog.LOG_INFO)
        with pytest.raises(TypeError):
            log.setLevel(None)

    def test_invalid_log_level(self):
        '''!
        Test invalid log level
        '''
        log = Logger()
        assert(log != None)
        log.log(123, 'foo')

    def test_logging_output(self):
        '''!
        Test logging on both stdout and console
        '''
        if os.path.isfile("/tmp/test_Logger.txt"):
            os.remove("/tmp/test_Logger.txt")
        os.remove("/etc/rsyslog.d/10-ztp-log-file.conf")
        log = Logger(log_file="/tmp/test_Logger.txt")
        assert(log != None)
        log.setLevel("warning")
        msg = "Test 1 " + getTimestamp()
        log.warning(msg)
        assert(self.__search_file('/var/log/syslog', msg ) == True)
        assert(self.__search_file('/tmp/test_Logger.txt', msg ) == True)

        msg = "Test 2 " + getTimestamp()
        log.debug(msg)
        assert(self.__search_file('/var/log/syslog', msg ) != True)
        assert(self.__search_file('/tmp/test_Logger.txt', msg ) != True)

        log.setLevel("error")
        msg = "Test 3 " + getTimestamp()
        log.debug(msg)
        assert(self.__search_file('/var/log/syslog', msg ) != True)
        assert(self.__search_file('/tmp/test_Logger.txt', msg ) != True)


        log.setLevel("critical")
        msg = "Test 4 " + getTimestamp()
        log.info(msg)
        assert(self.__search_file('/var/log/syslog', msg ) != True)
        assert(self.__search_file('/tmp/test_Logger.txt', msg ) != True)

        log.setLevel("warning")
        msg = "Test 5 " + getTimestamp()
        log.warning(msg)
        assert(self.__search_file('/var/log/syslog', msg ) == True)
        assert(self.__search_file('/tmp/test_Logger.txt', msg ) == True)


        msg = "Test 6 " + getTimestamp()
        log.error(msg)
        assert(self.__search_file('/var/log/syslog', msg ) == True)
        assert(self.__search_file('/tmp/test_Logger.txt', msg ) == True)

        log.setLevel("critical")
        msg = "Test 7 " + getTimestamp()
        log.debug(msg)
        assert(self.__search_file('/var/log/syslog', msg ) != True)
        assert(self.__search_file('/tmp/test_Logger.txt', msg ) != True)

        msg = "Test 8 " + getTimestamp()
        log.info(msg)
        assert(self.__search_file('/var/log/syslog', msg ) != True)
        assert(self.__search_file('/tmp/test_Logger.txt', msg ) != True)

        msg = "Test 9 " + getTimestamp()
        log.warning(msg)
        assert(self.__search_file('/var/log/syslog', msg ) != True)
        assert(self.__search_file('/tmp/test_Logger.txt', msg ) != True)

        msg = "Test 10 " + getTimestamp()
        log.error(msg)
        assert(self.__search_file('/var/log/syslog', msg ) != True)
        assert(self.__search_file('/tmp/test_Logger.txt', msg ) != True)

        msg = "Test 11 " + getTimestamp()
        log.critical(msg)
        assert(self.__search_file('/var/log/syslog', msg ) == True)
        assert(self.__search_file('/tmp/test_Logger.txt', msg ) == True)

    def test_invalid_log_level(self):
        '''!
        Test invalid log level
        '''
        saved_value = getCfg('log-level')
        setCfg('log-level', None)
        log = Logger()
        assert(log != None)
        setCfg('log-level', saved_value)
