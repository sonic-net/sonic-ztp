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
import time

from ztp.Logger import logger
from ztp.DecodeSysEeprom import sysEeprom
from ztp.ZTPLib import runCommand, get_sonic_version, getCfg

class Downloader:

    '''!
    \brief This class allow to use curl to retrieve data from a server.

    Examples of class usage:

    \code
    ztpDownload = Downloader()

    # Success
    rc,data = ztpDownload.getUrl('http://10.27.219.247:8080/content/test.txt', 'test.txt');
    print rc, data

    # Failure
    rc,data = ztpDownload.getUrl('http://10.27.219.247:8081/content/test.txt', 'test.txt');
    print rc, data
    \endcode
    '''

    def __init__(self, url=None, dst_file=None, incl_http_headers=None, is_secure=None, timeout=None, retry=None, curl_args=None, encrypted=None):
        '''!
        Constructor for the class, and optionally provide the parameters which can be used later by getUrl()

        @param url (str, optional) url of the file you want to get

        @param dst_file (str, optional) Filename for the data being stored. \n
            If not specified, it will be derived from the url (last part of it, e.g. basename).

        @param incl_http_headers (bool, optional) Include or not the additional HTTP headers
            (product name, serial number, mac address)

        @param is_secure (bool, optional) Every SSL connection curl makes is verified or not to be secure

        @param timeout (int, optional) Maximum number of seconds allowed for curl's connection to take. \n
            This  only  limits the connection phase.

        @param retry (int, optional) Number of times curl will retry in case of a transient error

        @param curl_args (str, optional) Options you want to pass to curl command line program

        @param encrypted (bool) Is the connectin with the server being encrypted?

        @return
            In case of success: \n
                Tupple: (0, data) \n
            In case of error: \n
                Tupple: (error code, html content)
        '''
        ## url of the file you want to get
        self.__url = url
        ## Name of the file where the file retrieved from the server is saved
        self.__dst_file = dst_file
        ## Do we send the HTTP headers (product name, serial number, mac address)?
        if incl_http_headers is None:
            self.__incl_http_headers = getCfg('include-http-headers')
        else:
            self.__incl_http_headers = incl_http_headers
        ## Should curl consider the SSL connection as secure or not?
        if is_secure is not None:
            self.__is_secure = is_secure
        else:
            self.__is_secure = getCfg('https-secure')

        ## Maximum number of seconds allowed for curl's connection to take
        if timeout is None:
            self.__timeout = getCfg('curl-timeout')
        else:
            self.__timeout = timeout
        ## Number of times curl will retry in case of a transient error
        if retry is None:
            self.__retry = getCfg('curl-retries')
        else:
            self.__retry = retry
        ## Optional curl cli program options
        self.__curl_args = curl_args
        ## Is the connection with the server encrypted?
        self.__encrypted = encrypted

        # Read system eeprom
        ## Product name read from the system eeprom
        self.__product_name  = sysEeprom.get_product_name();
        ## Serial number read from the system eeprom
        self.__serial_number = sysEeprom.get_serial_number();
        ## MAC address read from the system eeprom
        self.__mac_addr      = sysEeprom.get_mac_addr();

        # We need some items from the global ZTP config file
        ## Read which http-user-agent curl will be returning to the server
        self.__user_agent = getCfg('http-user-agent')

        # Read SONiC version
        self.__sonic_version = get_sonic_version()

        # Generate the http headers
        ## We include Product name, S/N and MAC address in the http headers sent to the server
        self.__http_headers = []
        if self.__product_name is not None:
            self.__http_headers.append('PRODUCT-NAME: ' + self.__product_name)
        if self.__serial_number is not None:
            self.__http_headers.append('SERIAL-NUMBER: ' + self.__serial_number)
        if self.__mac_addr is not None:
            self.__http_headers.append('BASE-MAC-ADDRESS: ' + self.__mac_addr)
        if self.__sonic_version is not None:
            self.__http_headers.append('SONiC-VERSION: ' + self.__sonic_version)

    def getUrl(self, url=None, dst_file=None, incl_http_headers=None, is_secure=True, timeout=None, retry=None, curl_args=None, encrypted=None, verbose=False):
        '''!
        Fetch a file using a given url. The content retrieved from the server is stored into a file.

        In case of a server erreur, the html content is stored into the file. This can be used to have a finer
        diagnostic of the issue.

        @param url (str, optional) url of the file you want to get. \n
            If the url is not given, the one specified in the constructor will be used.

        @param dst_file (str, optional) Filename for the data being stored. \n
            If not specified here and in the colnstructor, it will be derived from the url \n
            (last part of it, e.g. basename).

        @param incl_http_headers (bool, optional) Include or not the additional HTTP headers \n
            (product name, serial number, mac address)

        @param is_secure (bool, optional) Every SSL connection curl makes is verified or not to be secure. \n
            By default, the SSL connection is assumed secure.

        @param timeout (int, optional) Maximum number of seconds allowed for curl's connection to take. \n
            This  only  limits the connection phase.

        @param retry (int, optional) Number of times curl will retry in case of a transient error

        @param curl_args (str, optional) Options you want to pass to curl command line program. \n
            If no parameters are given here, the one given in the constructor will be used.

        @param encrypted (bool) Is the connection with the server being encrypted?

        @return
            Return a tuple: \n
            - In case of success: (0 destination_filename)\n
            - In case of error:   (error_code None)\n
            See here to see the status codes returned:\n
            https://ec.haxx.se/usingcurl-returns.html \n
            Note that we return error 20 in case of an unknown error.
        '''

        # Use arguments provided in the constructor
        if url is None and self.__url is not None:
            url = self.__url
        if dst_file is None and self.__dst_file is not None:
            dst_file = self.__dst_file
        if incl_http_headers is None and self.__incl_http_headers is not None:
            incl_http_headers = self.__incl_http_headers
        if is_secure is None and self.__is_secure is not None:
            is_secure = self.__is_secure
        if timeout is None and self.__timeout is not None:
            timeout = self.__timeout
        if retry is None and self.__retry is not None:
            retry = self.__retry
        if curl_args is None and self.__curl_args is not None:
            curl_args = self.__curl_args
        if encrypted is None and self.__encrypted is not None:
            encrypted = self.__encrypted

        # We can't run without a URL
        if url is None:
            return (-1, dst_file)

        # If no filename is provided, we use the last part of the url
        if dst_file is None:
            dst_file = os.path.basename(url)

        # If there is no path in the provided filename, we store the file under this default location
        try:
            if dst_file.find('/') == -1:
                dst_file = getCfg('ztp-tmp') + '/' + dst_file
        except (AttributeError) as e:
            logger.error("!Exception : %s" % (str(e)))
            return (20, None)

        # Create curl command
        cmd = '/usr/bin/curl -f -v -s -o ' + dst_file
        if self.__user_agent is not None:
            cmd += ' -A "' + self.__user_agent + '"'    # --user-agent
        if is_secure is False:
            cmd += ' -k'                                # --insecure
        if timeout is not None and isinstance(timeout, int) is True:
            cmd += ' --connect-timeout ' + str(timeout)
        if retry is not None and isinstance(retry, int) is True:
            cmd += ' --retry ' + str(retry)
        if incl_http_headers is not None:
            for h in self.__http_headers:
                cmd += ' -H \"' + h + '"'               # --header

        if curl_args is not None:
            cmd += ' ' + curl_args
        cmd += ' ' + url
        if verbose is True:
            logger.debug('%s' % (cmd))

        # Execute curl command
        _retries = retry
        while True:
            _start_time = time.time()
            (rc, cmd_stdout, cmd_stderr) = runCommand(cmd)
            _current_time = time.time()
            if rc !=0 and rc in [5, 6, 7] and _retries != 0 and (_current_time - _start_time) < timeout:
                logger.debug("!Error (%d) encountered while processing the command : %s" % (rc, cmd))
                time.sleep(timeout - (_current_time - _start_time))
                _retries = _retries -1
                continue

            if rc != 0:
                logger.error("!Error (%d) encountered while processing the command : %s" % (rc, cmd))
                for l in cmd_stdout:        # pragma: no cover
                    logger.error(str(l))
                for l in cmd_stderr:
                    logger.error(str(l))
                if os.path.isfile(dst_file):
                    os.remove(dst_file)
                return (20, None)
            else:
                break

        try:
            os.chmod(dst_file, stat.S_IRWXU)
        except FileNotFoundError:
            return (20, None)

        # Use curl result
        return (0, dst_file)
