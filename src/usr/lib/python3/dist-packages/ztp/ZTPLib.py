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

import datetime
import time
import shlex
import subprocess
from curses.ascii import isprint
import ztp.ZTPCfg
import os.path
from   ztp.defaults import *

try:        # pragma: no cover
    isinstance("", basestring)
    def isString(strVal):
        '''!
          Validate if provided atgument is of string datatype.

          @return
                 True  if strVal is if datatype string
                 False if strVal is not of datatype string

          Pyhon-2 compliant
        '''
        return isinstance(strVal, basestring)
except NameError:
    def isString(strVal):
        '''!
          Validate if provided atgument is of string datatype.

          @return
                 True  if strVal is if datatype string
                 False if strVal is not of datatype string

          Pyhon-3 compliant
        '''
        return isinstance(strVal, str)

## Construct a timestamp in YYYY-MM-DD HH:MM:SS %Z format
def getTimestamp():
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    return now.strftime('%Y-%m-%d %H:%M:%S ') + 'UTC'

## Global variable to keep track of the pid or process created by runCommand()
runcmd_pids = []

def runCommand(cmd, capture_stdout=True, use_shell=False, umask=-1):
    '''!
    Execute a given command

    @param cmd (str) Command to execute. Since we execute the command directly, and not within the
                     context of the shell, the full path needs to be provided ($PATH is not used).
                     Command parameters are simply separated by a space.

    @param capture_stdout (bool) If this is True, the function capture the output of stdout and stderr,
                           and return then a tupple with exit code, stdout, stderr
                           If this is False, the function does not capture stdout and stderr, so
                           they will be likely displayed on the console. We simply return the
                           exit code of the application.

    @param use_shell (bool) Execute subprocess with shell access

    During the execution of the process, the global variable runcmd_pids (it's a list) is updated
    with the PID of the running process.
    '''

    if isString(cmd) is False and isinstance(cmd, list) is False:
        raise ValueError('Process to execute should be a string or a list')
    pid = None
    try:
        if isinstance(cmd, list):
            if use_shell is False:
                shcmd = cmd
            else:
                shcmd = ''
                for c in cmd:
                    shcmd += c + ' '
        else:
            if use_shell is False:
                shcmd = shlex.split(cmd)
            else:
                shcmd = cmd
        if capture_stdout is True:
            proc = subprocess.Popen(shcmd, shell=use_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True, umask=umask)
            pid = proc.pid
            runcmd_pids.append(pid)
            output_stdout, output_stderr = proc.communicate()
            if pid in runcmd_pids:
                runcmd_pids.remove(pid)
            list_stdout = []
            for l in output_stdout.splitlines():
                list_stdout.append(str(l.decode()))
            list_stderr = []
            for l in output_stderr.splitlines():
                list_stderr.append(str(l.decode()))
            return (proc.returncode, list_stdout, list_stderr)
        else:
            proc = subprocess.Popen(shcmd, shell=use_shell, umask=umask)
            pid = proc.pid
            runcmd_pids.append(pid)
            proc.communicate()
            if pid in runcmd_pids:
                runcmd_pids.remove(pid)
            return proc.returncode
    except (OSError, ValueError) as e:
        print("!Exception [%s] encountered while processing the command : %s" % (str(e), str(cmd)))
        if pid is not None and pid in runcmd_pids:
            runcmd_pids.remove(pid)
        if capture_stdout is True:
            return (1, None, None)
        else:
            return 1

## Return build version of SONiC image
def get_sonic_version():
    '''!
    Get curring running SONiC firmware version
    '''

    (rc, build_version, errStr)  = runCommand('sonic-cfggen -y /etc/sonic/sonic_version.yml -v build_version')
    if rc == 0 and build_version is not None:
        return 'SONiC.{}'.format(build_version[0].strip())
    else:
        return None

def getValue(val, data_type=None, default_value=None):
    '''!
    Validate value against provided data type. If possible, Typecast string value
     to int, bool. If invalid value is used return None or provided default value.
    '''
    retVal = val
    if val is not None and data_type is not None:
        try:
            if data_type == str:
                if isString(val) is False:
                    retVal = None
            elif data_type == int:
                retVal = int(val)
            elif data_type == bool:
                if str(val).lower() == "true":
                    retVal = True
                elif str(val).lower() == "false":
                    retVal = False
                else:
                    retVal = None
            else:
                if isinstance(val, data_type) is False:
                    retVal = None
        except (ValueError, TypeError):
            retVal = None

    if retVal is None and default_value is not None:
        retVal = default_value

    return retVal


def getField(data, key, data_type=None, default_value=None):
    '''!
    Get a value of a field "key=value" from a python dict data. Return None
    if key is not found or if value is of wrong data type
    '''
    if data is None or isinstance(data, dict) is False:
        val = None
    elif key is None or isString(key) is False:
        val = None
    else:
        val = data.get(key)

    return getValue(val, data_type, default_value)

def getCfg(key, default_value=None, ztp_cfg=None):
    '''!
    Get a value of a field from ztp_cfg.json. If key is not found in ztp_cfg.json
    get value from default config dictionary.
    '''
    if ztp_cfg is not None:
        cfgObj = ztp_cfg
    else:
        cfgObj = ztp.ZTPCfg.ztpCfg

    if cfgObj[key] is None:
        val = defaultCfg.get(key)
        if val is None:
            return default_value
        return val
    else:
        if defaultCfg.get(key) is not None:
            return getValue(cfgObj[key], type(defaultCfg[key]))
        else:
            return cfgObj[key]

def setCfg(key, value, ztp_cfg=None):
    '''!
    Write key=value to ztp_cfg.json
    '''
    if ztp_cfg is not None:
        ztp_cfg.set(key, value, True)
    else:
        ztp.ZTPCfg.ztpCfg.set(key, value, True)

def getFeatures():
    '''!
    Return list of ZTP features supported by ZTP service
    '''

    features = []
    for feat in defaultCfg.keys():
        if feat[0:5] == 'feat-':
            features.append(feat)
    return features

## Check read configuration file
def validateZtpCfg(ztp_cfg=None):
    '''!
    Validate read ZTP configuration file.

    @exception Raise TypeError or ValueError exception if any invalid paramter is found
    '''
    if ztp_cfg is None or ztp_cfg.json_dict is None:
        raise ValueError('Data dictionary not initialized')

    data = ztp_cfg.json_dict
    for key in data.keys():
        if defaultCfg.get(key) is not None and data.get(key) is not None:
            cfgVal = getValue(data.get(key), type(defaultCfg[key]), None)
            if cfgVal is None:
                raise TypeError('Invalid data type used for ' + key)

def updateActivity(msg, overwrite=True):
    '''!
    Store ZTP activity status along with timestamp. Use overwrite=False to update status
    only if new activity status is different from previous activity status.
    '''

    try:
        activity_file = getCfg('ztp-activity')
        if not overwrite and os.path.isfile(activity_file):
            fh = open(activity_file, 'r')
            activity_str = fh.readline().strip()
            fh.close()
            if activity_str != '':
               split_strings = activity_str.split('|', 1)
               if len(split_strings) == 2 and split_strings[1].strip() == msg.strip():
                   return

        fh = open(activity_file, 'w')
        fh.write('%s | %s' % (getTimestamp(), msg))
        fh.close()
    except:
        pass

def systemReboot():
    '''!
    Helper API to reboot the device.
    '''
    (rc, reboot_help, errStr)  = runCommand('reboot -h | grep "\-y"', use_shell=True)
    if rc == 0:
        os.system('reboot -y')
    else:
        os.system('reboot')

def printable(input):
    '''!
         Filter out non-printable characters from an input string

         @param input (str) Input string

         @return String with non-printable characters removed
                 None if invalid input data type
    '''
    if input is not None and isString(input):
        return ''.join(char for char in input if isprint(char))
    else:
        return None
