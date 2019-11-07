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
import syslog
from ztp.ZTPLib import isString, getTimestamp, getCfg, runCommand

class Logger:

    '''!
    \brief This class allow to log data to syslog and/or to a file.

    There are five logging levels, from Debug to Critical.
    The default mode is to show logs from INFO level and above
    (INFO, Warning, Error, Critical).

    There are actuallt two levels of logging:
      - one for the text being shown on stdout
      - one for the text sent to a log file

    Examples of class usage:

    \code
    logger = Logger()
    logger.setLevel(Logger.ERROR)
    logger.debug('cmd="%s"' % (cmd))
    logger.error('An error happened  here')
    \endcode
    '''

    ## Debug level logging
    DEBUG = syslog.LOG_DEBUG
    ## Information level logging
    INFO = syslog.LOG_INFO
    ## Warning level logging
    WARNING = syslog.LOG_WARNING
    ## Error level logging
    ERROR = syslog.LOG_ERR
    ## Critical level logging
    CRITICAL = syslog.LOG_CRIT

    def __init__(self, log_level=None, log_file=None):
        '''!
        Constructor for the class.

        @param log_level (int) Log level for messages sent to syslog, expressed as a numeric constant
        @param log_file  (str) Name of the file where logging is written to
        '''

        ## Initialize the variables to default value. Later on, when the configuration
        ## is available, this function will be called again so their values will be
        ## defined depending of the configuration.

        ## Save logging level for stdout and file
        self.__log_level = log_level
        if log_level is None:
             self.__log_level = getCfg('log-level', self.INFO)
        self.setLevel(self.__log_level)

        ## Save logging filename
        self.__log_file = log_file
        if log_file is None:
             self.__log_file = getCfg('log-file')
        self.setlogFile(self.__log_file)
        ## Log to stdout, useful for test-mode
        self.__log_console = False

        syslog.openlog(ident='sonic-ztp', logoption=syslog.LOG_PID)

    def __str_to_int_level(self, str_level):
        '''!
        Convert a log level expressed as astring (e.g. "DEBUG") to a numeric constant (e.g. DEBUG).

        @param str_level (str) Log level expressed as a string
        @return return the integer value from a string
        '''
        if str_level.upper() == 'DEBUG':
            return self.DEBUG
        elif str_level.upper() == 'INFO':
            return self.INFO
        elif str_level.upper() == 'WARNING':
            return self.WARNING
        elif str_level.upper() == 'ERROR':
            return self.ERROR
        elif str_level.upper() == 'CRITICAL':
            return self.CRITICAL
        else:
            print('Invalid log level string %s. Using INFO.' % str_level)
            return self.INFO

    def __int_level_to_str(self, int_level):
        '''!
        Convert a log level expressed as an int (e.g. syslog.DEBUG) to a string (e.g. 'DEBUG').

        @param int_level (int) Log level expressed as an integer
        @return return the string value for the log level
        '''
        if int_level == self.DEBUG:
            return 'DEBUG'
        elif int_level == self.INFO:
            return 'INFO'
        elif int_level == self.WARNING:
            return 'WARNING'
        elif int_level == self.ERROR:
            return 'ERROR'
        elif int_level == self.CRITICAL:
            return 'CRITICAL'
        else:
            return 'INFO'

    def setLevel(self, log_level):
        '''!
        Set the current level of logging.

        @param log_level (int) log level which will be shown on stdout (DEBUG, INFO, WARNING, ERROR or CRITICAL)
        @exception Raise TypeError if incorrect parameter type
        '''

        if not isString(log_level) and not type(log_level) == int:
            raise TypeError("Log Level must be a number or a string")

        if type(log_level) == int:
            self.__log_level = log_level
        else:
            self.__log_level = self.__str_to_int_level(log_level)

        if type(log_level) == int:
            if (self.__log_level > self.DEBUG) or (self.__log_level < self.CRITICAL):
                self.__log_level = self.INFO

        syslog.setlogmask(syslog.LOG_UPTO(self.__log_level))

    def setlogFile(self, log_file=None):
        '''!
        Set the log file to store all logs generated during ZTP

        @param log_file (str) log file
        @exception Raise TypeError if incorrect parameter type
        '''

        rsyslog_conf_file = getCfg("rsyslog-ztp-log-file-conf", '/etc/rsyslog.d/10-ztp.conf')
        if log_file is None or (isString(log_file) and log_file == ''):
            if os.path.isfile(rsyslog_conf_file):
                os.remove(rsyslog_conf_file)
            return

        if not isString(log_file):
            raise TypeError("Log file must be a string")

        self.__log_file = log_file
        change = True
        if os.path.isfile(rsyslog_conf_file):
            fh = open(rsyslog_conf_file, 'r')
            if fh.readline().strip() == ':programname, contains, "sonic-ztp"  ' + log_file:
                change = False
            fh.close()

        if change:
           fh = open(rsyslog_conf_file, 'w')
           fh.write(':programname, contains, "sonic-ztp"  ' + log_file)
           fh.close()
           runCommand('systemctl restart rsyslog', capture_stdout=False)

    def setConsoleLogging(self, mode=True):
        '''!
        Enable/disable logging to console
        '''
        self.__log_console = mode

    def getLevel(self):
        '''!
        Return log level being used to filter messages
        '''
        return  self.__log_level

    def getLogFile(self):
        '''!
        Return log file used to store logs in addition to syslog
        '''
        return  self.__log_file

    def log(self, log_level, fmt, *args):
        '''!
        Log a formatted message - the logging level needs to be provided.

        @param log_level (int) Log level for this particular log message. Depending on 
                               log level, the message will be shown or not.

        '''
        syslog.syslog(log_level, fmt + '\n' % args)
        if self.__log_console:
            print('sonic-ztp '+ self.__int_level_to_str(log_level)  + ' ' +fmt % args)

    def debug(self, fmt, *args):
        '''!
        Helper function to log a formatted message - similar to log(Logger.DEBUG, ...
        '''
        self.log(self.DEBUG, fmt, *args)

    def info(self, fmt, *args):
        '''!
        Helper function to log a formatted message - similar to log(Logger.INFO, ...
        '''
        self.log(self.INFO, fmt, *args)

    def warning(self, fmt, *args):
        '''!
        Helper function to log a formatted message - similar to log(Logger.WARNING, ...
        '''
        self.log(self.WARNING, fmt, *args)

    def error(self, fmt, *args):
        '''!
        Helper function to log a formatted message - similar to log(Logger.ERROR, ...
        '''
        self.log(self.ERROR, fmt, *args)

    def critical(self, fmt, *args):
        '''!
        Helper function to log a formatted message - similar to log(Logger.CRITICAL, ...
        '''
        self.log(self.CRITICAL, fmt, *args)

## Global instance of the logger
logger = Logger()
