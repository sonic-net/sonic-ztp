#!/usr/bin/python
#
# Copyright (c) 2015 Dell Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# THIS CODE IS PROVIDED ON AN #AS IS* BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT
#  LIMITATION ANY IMPLIED WARRANTIES OR CONDITIONS OF TITLE, FITNESS
# FOR A PARTICULAR PURPOSE, MERCHANTABLITY OR NON-INFRINGEMENT.
#
# See the Apache Version 2.0 License for specific language governing
# permissions and limitations under the License.
#

from ctypes import *

'''
Standard Enum types for resources.
This needs to be updated to keep in sync with the definitions in sdi_entity.h
@todo can these be auto-generated from header files?
@todo not all resources and API are currently covered. extend support for all SDI api.
'''
SDI_RESOURCE_TEMPERATURE=0
SDI_RESOURCE_FAN=1

class SdiError(Exception):
        def __init__(self, value):
                self.value=value
        def __str__(self, value):
                return repr(self.value)

'''
@todo location of libsdi_sys_v2 must not be hardcoded.
'''
sdi_sys=CDLL("/opt/dell/os10/lib/libsdi_sys_v2.so")

def sdi_sys_init():
    return sdi_sys.sdi_sys_init()

def sdi_entity_init(ehdl):
    return sdi_sys.sdi_entity_init(ehdl)

def sdi_entity_lookup(entity_type, entity_instance):
    return sdi_sys.sdi_entity_lookup(entity_type, entity_instance)

def sdi_entity_resource_lookup(entity_handle, resource_type, resource_name):
    return sdi_sys.sdi_entity_resource_lookup(entity_handle, resource_type, resource_name)

def sdi_entity_name_get(ehdl):
    return  c_char_p(sdi_sys.sdi_entity_name_get(ehdl)).value


def sdi_temperature_get(resource_handle):
    temperature=c_int()
    err=sdi_sys.sdi_temperature_get(resource_handle, byref(temperature))
    #print temperature.value
    if (err): raise SdiError(err)
    return temperature.value

def sdi_fan_speed_get(resource_handle):
    speed=c_int()
    err=sdi_sys.sdi_fan_speed_get(resource_handle, byref(speed))
    print speed.value
    if (err): raise SdiError(err)
    return speed.value

def sdi_resource_alias_get(rhdl):
    return  c_char_p(sdi_sys.sdi_resource_alias_get(rhdl)).value

def sdi_resource_type_get(rhdl):
    return  sdi_sys.sdi_resource_type_get(rhdl)

def sdi_entity_dump_callback(ehdl, value):
    print sdi_entity_name_get(ehdl)
    sdi_entity_for_each_resource(ehdl, sdi_resource_dump_callback, None)

def sdi_resource_dump_callback(rhdl, value):
    print sdi_resource_alias_get(rhdl)

def sdi_entity_for_each(callback_fn, data):
    sdi_entity_dump_fn=sdi_entity_callback_fn_type(callback_fn)
    sdi_sys.sdi_entity_for_each(sdi_entity_dump_fn, data)

def sdi_entity_for_each_resource(ehdl, callback_fn, data):
    sdi_resource_dump_fn=sdi_resource_callback_fn_type(callback_fn)
    sdi_sys.sdi_entity_for_each_resource(ehdl, sdi_resource_dump_fn, data)


sdi_entity_callback_fn_type=CFUNCTYPE(None, POINTER(c_int), POINTER(c_int))
sdi_resource_callback_fn_type=CFUNCTYPE(None, POINTER(c_int), POINTER(c_int))


'''
   Following is sample to exercise that the API work fine.
'''
if __name__ == "__main__":
    sdi_sys_init()
    ehdl=sdi_entity_lookup(0,0)
    rhdl=sdi_entity_resource_lookup(ehdl,0,"T2 temp sensor")

    sdi_temperature_get(rhdl)
    sdi_entity_name_get(ehdl)


    sdi_entity_for_each(sdi_entity_dump_callback, None)
