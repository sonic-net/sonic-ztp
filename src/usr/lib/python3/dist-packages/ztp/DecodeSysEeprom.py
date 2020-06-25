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

from ztp.ZTPLib import runCommand, printable

class DecodeSysEeprom:

    '''!
    \brief This class allow to log data to stdout and/or to a file.
    '''

    def __init__(self):
        '''!
        Constructor for the class.

        @exception Raise an exception if the program decode-syseeprom is not found

        We read the three sections we care about from the eeprom and cache their values.
        '''
        try:
            self.__product_name  = self.__read_sys_eeprom('-p')
            self.__serial_number = self.__read_sys_eeprom('-s')
            self.__mac_addr      = self.__read_sys_eeprom('-m')
        except Exception as v:
            raise Exception(str(v))

    ## Return the Product Name stored in the system eeprom
    def get_product_name(self):
        return self.__product_name

    ## Return the Serial Number stored in the system eeprom
    def get_serial_number(self):
        return self.__serial_number

    ## Return the MAC address stored in the system eeprom
    def get_mac_addr(self):
        return self.__mac_addr

    def __read_sys_eeprom(self, option):
        '''!
        Helper function to read a specific section from the eeprom.

        @param option (str) Option given to decode_syseeprom command line utility
        '''
        cmd = 'decode-syseeprom ' + option
        (rc, cmd_stdout, cmd_stderr) = runCommand(cmd)
        if not rc == 0 or len(cmd_stdout) != 1:
            return 'N.A'
        else:
            return printable(cmd_stdout[0].rstrip())

## Global instance of the class
sysEeprom = DecodeSysEeprom()
