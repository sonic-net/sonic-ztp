#!/usr/bin/python
# Copyright (c) 2015 Dell Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# THIS CODE IS PROVIDED ON AN  *AS IS* BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT
# LIMITATION ANY IMPLIED WARRANTIES OR CONDITIONS OF TITLE, FITNESS
# FOR A PARTICULAR PURPOSE, MERCHANTABLITY OR NON-INFRINGEMENT.
#
# See the Apache Version 2.0 License for specific language governing
# permissions and limitations under the License.

from pysdi import *
from cmd import Cmd

'''
This utility adds a "shell" interface to the SDI library.
This could be used when doing developing UT to exercise different functionality.
@todo: Not all api are currently covered.  Extend it to include all api.
'''

entity_to_handles = {}

current_entity=None
current_resource=None

def sdi_entity_info_update_callback(ehdl, value):
    entity_to_handles[sdi_entity_name_get(ehdl)]=ehdl
    #sdi_entity_for_each_resource(ehdl, sdi_resource_info_update_callback, ehdl)

def sdi_resource_dump_callback(rhdl, value):
    print sdi_resource_alias_get(rhdl)

def sdi_dump_temperature_resource_callback(rhdl, value):
    if (sdi_resource_type_get(rhdl) != SDI_RESOURCE_TEMPERATURE):
                return
    print (sdi_resource_alias_get(rhdl), sdi_temperature_get(rhdl))

def sdi_dump_fan_resource_callback(rhdl, value):
    if (sdi_resource_type_get(rhdl) != SDI_RESOURCE_FAN):
                return
    print (sdi_resource_alias_get(rhdl), sdi_fan_speed_get(rhdl))


class SdiPrompt(Cmd):
        def do_list_entities(self, args):
                '''list all known entities in the system'''
                print entity_to_handles.keys()

        def do_entity_init(self, entity_name):
                '''list all known entities in the system'''
                if (entity_name == None):
                        print "Need an entity name as parameter"
                        return
                if not (entity_name in entity_to_handles):
                        print "invalid entity_name"
                        return
                return sdi_entity_init(entity_to_handles[entity_name])

        def do_list_entity_resources(self, entity_name):
                '''list all known resources in the given entity'''
                if (entity_name == None):
                        print "Need an entity name as parameter"
                        return
                if not (entity_name in entity_to_handles):
                        print "invalid entity_name"
                        return

                sdi_entity_for_each_resource(entity_to_handles[entity_name], sdi_resource_dump_callback, None)

        def do_list_temperatures(self, entity_name):
                '''list all known temperature resources in the given entity'''
                if (entity_name == None):
                        print "Need an entity name as parameter"
                        return
                if not (entity_name in entity_to_handles):
                        print "invalid entity_name"
                        return

                sdi_entity_for_each_resource(entity_to_handles[entity_name], sdi_dump_temperature_resource_callback, None)

        def do_list_fans(self, entity_name):
                '''list all known fans resources in the given entity'''
                if (entity_name == None):
                        print "Need an entity name as parameter"
                        return
                if not (entity_name in entity_to_handles):
                        print "invalid entity_name"
                        return

                sdi_entity_for_each_resource(entity_to_handles[entity_name], sdi_dump_fan_resource_callback, None)


        def do_quit(self, args):
                """Quits the program."""
                print "Quitting."
                raise SystemExit

if __name__ == "__main__":
    sdi_sys_init()
    ''' Enable these for debugging

    ehdl=sdi_entity_lookup(0,0)
    rhdl=sdi_entity_resource_lookup(ehdl,0,"T2 temp sensor")

    sdi_temperature_get(rhdl)
    sdi_entity_name_get(ehdl)

    sdi_entity_for_each(sdi_entity_dump_callback, None)
    '''
    sdi_entity_for_each(sdi_entity_info_update_callback, None)

    prompt=SdiPrompt()
    prompt.prompt="sdi> "
    prompt.cmdloop("Starting SDI Prompt Loop")
