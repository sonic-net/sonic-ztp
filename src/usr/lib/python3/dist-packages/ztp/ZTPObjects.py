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
import socket
import tempfile
import subprocess
from ztp.DecodeSysEeprom import sysEeprom
from ztp.Downloader import Downloader
from ztp.Logger import logger
from ztp.ZTPLib import isString, get_sonic_version, runCommand, getField, getCfg, updateActivity

class Identifier:
    '''!
    \brief This class is used to resolve switch identifier string to be used by DynamicURL.
    '''

    def getIdentifier(self):
        '''!
         Obtain the resolved identifier string based on the identifier data.

         @return
              In case of success: \n
                Identifier string \n
              In case of error: \n
                None
        '''
        try:
            identifier_data = self.identifier_data
            if isinstance(identifier_data, dict) is False:
                if identifier_data == "hostname":
                    return socket.gethostname()
                elif identifier_data == "hostname-fqdn":
                    return socket.getfqdn()
                elif identifier_data == "serial-number":
                    return sysEeprom.get_serial_number()
                elif identifier_data == "product-name":
                    return sysEeprom.get_product_name()
                elif identifier_data == "mac":
                    return sysEeprom.get_mac_addr()
                elif identifier_data == "sonic-version":
                    return get_sonic_version()
                else:
                    return identifier_data
            elif identifier_data.get('url') is not None:
                url_data = identifier_data.get('url')
                (fd, filename) = tempfile.mkstemp(prefix='identifier_', dir=getCfg('ztp-tmp'))
                os.close(fd)
                urlObj = URL(url_data, filename)
                updateActivity('Downloading identifier script from \'%s\'' %(urlObj.getSource()))
                rc, identifier_script = urlObj.download()
                if rc == 0 and os.path.isfile(identifier_script):
                    updateActivity('Executing identifier script downloaded from \'%s\'' %(urlObj.getSource()))
                    (rc, cmd_stdout, cmd_stderr) = runCommand([identifier_script])
                    if rc != 0:
                        logger.error('Error encountered while executing identifier %s Exit code: (%d).'
                                    % (identifier_script, rc))
                        return None
                    if len(cmd_stdout) == 0:
                        return ""
                    else:
                        return cmd_stdout[0]
        except (TypeError, ValueError) as e:
            logger.error('Exception: [%s] encountered while processing identifier data in dynamic URL.'
                         % str(e))
            return None
        return None

    def __init__(self, identifier_data=None):
        '''!
            Constructor for the Identifier class.

            @param identifier_data (dict, optional) Information to be used to resolve a switch identifier string.
        '''
        self.identifier_data = identifier_data

class URL:
    '''!
    \brief This class is used to describe a file that needs to be downloaded.
    '''
    def getSource(self):
        '''!
         Obtain the source URL of the file to be downloaded

         @return String representing the source URL
        '''
        return self.__source

    def download(self, destination=None):
        '''!
         Start download operation

         @return
                Return a tuple: \n
                - In case of success: (0, destination_filename)\n
                - In case of error:   (error_code, None)\n
                See here to see the status codes returned:\n
                https://ec.haxx.se/usingcurl-returns.html \n
                Note: error_code=20 is returned in case of an unknown error.
        '''
        return self.objDownload.getUrl(dst_file=destination)

    def __init__(self, url_data, destination=None):
        '''!
            Constructor for the URL class.

            @param url_data (dict) Information to be used to download the file
            @param destination (str, optional) When specified, this represents the filename used to save the \n
                                               downloaded file as. If destination value is available in url_data,
                                               this parameter is ignored.
        '''
        argError = False
        self.__destination = None
        if isString(url_data):
            self.__source = url_data
            self.__destination = destination
        elif isinstance(url_data, dict) is False or \
             url_data.get('source') is None or \
             isString(url_data.get('source')) is False:
            argError = True
        elif isinstance(url_data, dict):
            self.__source = url_data.get('source')
            if url_data.get('destination') is None:
                self.__destination = destination
            else:
                self.__destination = url_data.get('destination')
            if self.__destination is not None and isString(self.__destination) is False:
                argError = True

        if argError:
            logger.debug('URL provided with invalid argument types.')
            raise TypeError('URL provided with invalid argument types.')

        self.url_data = url_data
        if isinstance(url_data, dict):
            self.objDownload = Downloader(self.__source, \
                                          self.__destination, \
                                          incl_http_headers=getField(self.url_data, 'include-http-headers', bool, None), \
                                          is_secure=getField(self.url_data, 'secure', bool, None), \
                                          curl_args=self.url_data.get('curl-arguments'), \
                                          encrypted=getField(self.url_data, 'encrypted', bool, None), \
                                          timeout=getField(self.url_data, 'timeout', int, None))
        else:
            self.objDownload = Downloader(self.__source, self.__destination)

class DynamicURL:
    '''!
    \brief This class is used to describe a file that needs to be downloaded. The source URL
     of the remote file is evaluated at runtime wile it is being downloaded.
    '''

    def getSource(self):
        '''!
         Obtain the source URL of the file to be downloaded

         @return String representing the source URL
        '''
        return self.__source

    def download(self, destination=None):
        '''!
         Start download operation

         @return
                Return a tuple: \n
                - In case of success: (0, destination_filename)\n
                - In case of error:   (error_code, None)\n
                See here to see the status codes returned:\n
                https://ec.haxx.se/usingcurl-returns.html \n
                Note: error_code=20 is returned in case of an unknown error.
        '''
        return self.objDownload.getUrl(dst_file=destination)

    def __init__(self, dyn_url_data, destination=None):
        '''!
            Constructor for the DynamicURL class.

            @param dyn_url_data (dict) Information to be used to download the file
            @param destination (str, optional) When specified, this represents the filename used to save the \n
                                               downloaded file as. If destination value is available in url_data,
                                               this parameter is ignored.

            @exception Raise ValueError if insufficient input is provided.
            @exception Raise TypeError if invalid input is provided or if switch identifier could not be resolved.

            Switch identifier string is resolved as part of the constructor.
        '''
        if dyn_url_data is None or isinstance(dyn_url_data, dict) is False or \
           dyn_url_data.get('source') is None or isinstance(dyn_url_data.get('source'), dict) is False or \
           dyn_url_data.get('source').get('identifier') is None:
            logger.debug('DynamicURL provided with invalid argument types.')
            raise TypeError('DynamicURL provided with invalid argument types')

        self.__destination = None
        if dyn_url_data.get('destination') is not None:
            self.__destination = dyn_url_data.get('destination')
        elif destination is not None:
            self.__destination = destination

        if self.__destination is not None and \
           isString(self.__destination) is False:
            logger.debug('DynamicURL provided with invalid argument types.')
            raise TypeError('DynamicURL provided with invalid argument types')

        self.dyn_url_data = dyn_url_data
        source = dyn_url_data.get('source')

        self.__source = ''
        if source.get('prefix') is not None:
            if isString(source.get('prefix')):
                self.__source = source.get('prefix')
            else:
                raise TypeError('DynamicURL provided with invalid argument types.')


        objIdentifier = Identifier(source.get('identifier'))
        identifier = objIdentifier.getIdentifier()
        if identifier is None:
            raise ValueError('DynamicURL source identifier could not be evaluated.')
        else:
            self.__source = self.__source + identifier

        if source.get('suffix') is not None:
            if isString(source.get('suffix')):
                self.__source = self.__source + source.get('suffix')
            else:
                raise TypeError('DynamicURL provided with invalid argument types.')

        self.objDownload = Downloader(self.__source, \
                                      self.__destination, \
                                      incl_http_headers=getField(self.dyn_url_data, 'include-http-headers', bool, None), \
                                      is_secure=getField(self.dyn_url_data, 'secure', bool, None), \
                                      curl_args=self.dyn_url_data.get('curl-arguments'), \
                                      encrypted=getField(self.dyn_url_data, 'encrypted', bool, None), \
                                      timeout=getField(self.dyn_url_data, 'timeout', int, None))
