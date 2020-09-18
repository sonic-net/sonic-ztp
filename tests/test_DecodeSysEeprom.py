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
import shutil
import os
import stat
import pytest

from ztp.DecodeSysEeprom import DecodeSysEeprom
from ztp.ZTPLib import getCfg
from ztp.JsonReader import JsonReader

class TestClass(object):

    '''!
    \brief This class allow to define unit tests for class decodeSysEeprom

    Examples of class usage:

    \code
    pytest-2.7 -v -x test_decodeSysEeprom.py
    \endcode
    '''

    DECODE_SYSEEPROM_PATH = '/usr/local/bin/decode-syseeprom'
    DECODE_SYSEEPROM_BACKUP_PATH = DECODE_SYSEEPROM_PATH + '_org'

    def test_missing_utility(self):
        '''!
        Test when we call the constructor function and decode-syseprom utility is missing
        '''
        shutil.move(self.DECODE_SYSEEPROM_PATH, self.DECODE_SYSEEPROM_BACKUP_PATH)
        syseeprom = DecodeSysEeprom()
        assert(syseeprom.get_product_name() != None)
        assert(syseeprom.get_mac_addr() != None)
        assert(syseeprom.get_serial_number() != None)
        shutil.move(self.DECODE_SYSEEPROM_BACKUP_PATH, self.DECODE_SYSEEPROM_PATH)

    def test_error_utility(self):
        '''!
        Test when we call the constructor function and decode-syseprom utility is returning an error
        '''
        shutil.move(self.DECODE_SYSEEPROM_PATH, self.DECODE_SYSEEPROM_BACKUP_PATH)
        f = open(self.DECODE_SYSEEPROM_PATH, 'w')
        f.write('#!/bin/sh\nexit 1\n')
        f.close()
        st = os.stat(self.DECODE_SYSEEPROM_PATH)
        os.chmod(self.DECODE_SYSEEPROM_PATH, st.st_mode | stat.S_IEXEC)
        syseeprom = DecodeSysEeprom()
        assert(syseeprom.get_product_name() != None)
        assert(syseeprom.get_mac_addr() != None)
        assert(syseeprom.get_serial_number() != None)
        os.remove(self.DECODE_SYSEEPROM_PATH)
        shutil.move(self.DECODE_SYSEEPROM_BACKUP_PATH, self.DECODE_SYSEEPROM_PATH)

    def test_constructor(self):
        '''!
        Test when we call the constructor function with imcomplete or wrong parameters
        '''
        syseeprom = DecodeSysEeprom()
        assert(syseeprom != None)

    def test_product_name(self):
        '''!
        Test if we found the product name in the system eeprom
        '''
        syseeprom = DecodeSysEeprom()
        assert(syseeprom.get_product_name() != None)

    def test_serial_number(self):
        '''!
        Test if we found the serial number in the system eeprom
        '''
        syseeprom = DecodeSysEeprom()
        assert(syseeprom.get_serial_number() != None)

    def test_mac_addr(self):
        '''!
        Test if we found the product name in the system eeprom
        '''
        syseeprom = DecodeSysEeprom()
        assert(syseeprom.get_mac_addr() != None)

    def test_ztp_profile(self):
        syseeprom = DecodeSysEeprom()
        if os.path.isfile('/etc/dhcp/dhclient.conf'):
            fh = open('/etc/dhcp/dhclient.conf')
            dhcp_file = fh.read()
            fh.close()
            client_identifier_string = "send dhcp-client-identifier \"SONiC##" + \
                            syseeprom.get_product_name() + "##" + \
                            syseeprom.get_serial_number()+"\""
            if getCfg('admin-mode') == False:
                assert(client_identifier_string not in dhcp_file)
                assert('send dhcp6.user-class' not in dhcp_file)
                assert('send user-class' not in dhcp_file)
                assert('dhcp6.provisioning-script-url,' not in dhcp_file)
                assert('provisioning-script-url,' not in dhcp_file)
                assert('dhcp6.boot-file-url,' not in dhcp_file)
                assert('tftp-server-name,' not in dhcp_file)
            
            os.system(getCfg('ztp-lib-dir')+'/ztp-profile.sh create ztp_config.json')

            assert(os.path.isfile('/etc/network/ifupdown2/policy.d/ztp_dhcp.json') is True)
            if getCfg('feat-console-logging'):
                assert(os.path.isfile(getCfg('rsyslog-ztp-consile-log-file-conf')) is True)
                fh = open(getCfg('rsyslog-ztp-consile-log-file-conf'))
                console_log_file_conf = fh.read()
                fh.close()
                assert('sonic-ztp' in console_log_file_conf)
                assert('/dev/console' in console_log_file_conf)
            assert(os.path.isfile(getCfg('rsyslog-ztp-log-file-conf')) is True)
            fh = open(getCfg('rsyslog-ztp-log-file-conf'))
            log_file_conf = fh.read()
            fh.close()
            assert('sonic-ztp' in log_file_conf)
            assert(getCfg('log-file') in log_file_conf)

            fh = open('port_table.json', 'w')
            fh.write('''
{
  "PORT_DATA": {
    "PORT_TABLE:Ethernet0": {
      "value": {
        "oper_status": "up"
      }
    },
    "PORT_TABLE:Ethernet1": {
      "value": {
        "oper_status": "down"
      }
    }
  }
}
''')
            fh.close()
            fh = open('ztp_dhcp_disabled.json', 'w')
            fh.write('''
{
  "ZTP_DHCP_DISABLED": "true" 
}
''')
            fh.close()
            os.system('sonic-cfggen -j ztp_config.json -j ztp_dhcp_disabled.json -t /usr/share/sonic/templates/dhclient.conf.j2 > tmp_dhcp_file')
            os.system('sonic-cfggen -j ztp_config.json -j ztp_dhcp_disabled.json -t /usr/share/sonic/templates/interfaces.j2 > tmp_interfaces')
            fh = open('tmp_dhcp_file')
            dhcp_file = fh.read()
            fh.close()
            fh = open('tmp_interfaces')
            intf_file = fh.read()
            fh.close()
            assert('provisioning-script-url,' not in dhcp_file)
            assert('# ZTP out-of-band interface' not in intf_file)
            os.remove('tmp_interfaces')
            os.remove('tmp_dhcp_file')
            os.remove('ztp_dhcp_disabled.json')

            objJson, jsonDict = JsonReader('ztp_config.json')
            os.system('sonic-cfggen -j ztp_config.json -j port_table.json -t /usr/share/sonic/templates/dhclient.conf.j2 > tmp_dhcp_file')
            os.system('sonic-cfggen -j ztp_config.json -j port_table.json -t /usr/share/sonic/templates/interfaces.j2 > tmp_interfaces')
            fh = open('tmp_dhcp_file')
            dhcp_file = fh.read()
            fh.close()
            fh = open('tmp_interfaces')
            intf_file = fh.read()
            fh.close()
            fh = open('/etc/network/ifupdown2/policy.d/ztp_dhcp.json')
            dhcp_policy = fh.read()
            fh.close()
            assert('dhcp-wait" : "no"' in dhcp_policy)
            assert('dhcp6-ll-wait' in dhcp_policy)
            assert('"dhcp6-ll-wait" : "2"' in dhcp_policy)
            assert('eth0' in dhcp_policy)
            assert(client_identifier_string in dhcp_file)
            assert('send dhcp6.user-class' in dhcp_file)
            assert('send user-class' in dhcp_file)
            assert('dhcp6.provisioning-script-url,' in dhcp_file)
            assert('provisioning-script-url,' in dhcp_file)
            assert('dhcp6.boot-file-url,' in dhcp_file)
            assert('tftp-server-name,' in dhcp_file)
            if getCfg('feat-inband'):
               assert(jsonDict.get('ZTP').get('mode').get('inband').lower() == 'true')
               assert(jsonDict.get('PORT').get('Ethernet0').get('admin_status').lower() == 'up')
               assert('auto Ethernet0' in intf_file)
               assert('auto Ethernet1' in intf_file)
               assert('auto Ethernet5000' not in intf_file)
               assert('Ethernet0' in dhcp_policy)
            else:
               assert(jsonDict.get('ZTP').get('mode').get('inband').lower() == 'false')
               assert(jsonDict.get('PORT').get('Ethernet0').get('admin_status').lower() == 'down')
               assert('iface Ethernet0' not in intf_file)

            if getCfg('feat-ipv4'):
               assert(jsonDict.get('ZTP').get('mode').get('ipv4').lower() == 'true')
               assert('iface eth0 inet dhcp' in intf_file)
               if getCfg('feat-inband'):
                   assert('iface Ethernet0 inet dhcp' in intf_file)
                   assert('iface Ethernet1 inet dhcp' not in intf_file)
            else:
               assert(jsonDict.get('ZTP').get('mode').get('ipv4').lower() == 'false')
               assert('iface eth0 inet dhcp' not in intf_file)
               if getCfg('feat-inband'):
                   assert('iface Ethernet0 inet dhcp' not in intf_file)

            if getCfg('feat-ipv6'):
               assert(jsonDict.get('ZTP').get('mode').get('ipv6').lower() == 'true')
               assert('iface eth0 inet6 dhcp' in intf_file)
               assert('    up sysctl net.ipv6.conf.eth0.accept_ra=1' in intf_file)
               assert('    down sysctl net.ipv6.conf.eth0.accept_ra=0' in intf_file)
               if getCfg('feat-inband'):
                   assert('iface Ethernet0 inet6 dhcp' in intf_file)
                   assert('iface Ethernet1 inet6 dhcp' not in intf_file)
            else:
               assert(jsonDict.get('ZTP').get('mode').get('ipv6').lower() == 'false')
               assert('iface eth0 inet6 dhcp' not in intf_file)
               if getCfg('feat-inband'):
                   assert('iface Ethernet0 inet6 dhcp' not in intf_file)
            assert(jsonDict.get('ZTP').get('mode').get('product-name') == syseeprom.get_product_name())
            assert(jsonDict.get('ZTP').get('mode').get('serial-no') == syseeprom.get_serial_number())
            os.system('/usr/lib/ztp/ztp-profile.sh remove')
            os.system('rm -f tmp_dhcp_file ztp_config.json tmp_interfaces port_table.json')
            assert(os.path.isfile('/etc/network/ifupdown2/policy.d/ztp_dhcp.json') is False)
            assert(os.path.isfile(getCfg('rsyslog-ztp-consile-log-file-conf')) is False)
            assert(os.path.isfile(getCfg('rsyslog-ztp-log-file-conf')) is True)

