
/*
 * Copyright (c) 2016 Dell Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
 *
 * THIS CODE IS PROVIDED ON AN  *AS IS* BASIS, WITHOUT WARRANTIES OR
 * CONDITIONS OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT
 *  LIMITATION ANY IMPLIED WARRANTIES OR CONDITIONS OF TITLE, FITNESS
 * FOR A PARTICULAR PURPOSE, MERCHANTABLITY OR NON-INFRINGEMENT.
 *
 * See the Apache Version 2.0 License for specific language governing
 * permissions and limitations under the License.
 */


/* OPENSOURCELICENSE */

/****************************************************************
 * Implementation of SDI Reference Entity and SDI Reference Resource.
 ****************************************************************/

#include "unittest/sdi_unit_test.h"
#include "std_utils.h"
#include <iostream>
#include <map>
#include <string>
#include <cassert>
#define SDI_DEBUG 0
#define SDI_LOG(s) if(SDI_DEBUG) cout<<s<<endl;

using namespace std;

/**
 * Gets the resource type based on name.Resource names can be retrieved from config file.
 * @param resource_name[in] - resource name
 * @return resource type.
 */
sdi_resource_type_t toResourceType(string resource_name)
{
    map<string,sdi_resource_type_t> rmap;
    rmap["SDI_RESOURCE_TEMPERATURE"]=SDI_RESOURCE_TEMPERATURE;
    rmap["SDI_RESOURCE_FAN"]=SDI_RESOURCE_FAN;
    rmap["SDI_RESOURCE_LED"]=SDI_RESOURCE_LED;
    rmap["SDI_RESOURCE_DIGIT_DISPLAY_LED"]=SDI_RESOURCE_DIGIT_DISPLAY_LED;
    rmap["SDI_RESOURCE_ENTITY_INFO"]=SDI_RESOURCE_ENTITY_INFO;
    rmap["SDI_RESOURCE_UPGRADABLE_PLD"]=SDI_RESOURCE_UPGRADABLE_PLD;
    rmap["SDI_RESOURCE_MEDIA"]=SDI_RESOURCE_MEDIA;
    map<string,sdi_resource_type_t>::iterator it;
    it=rmap.find(resource_name);
    if(it->second<STD_ERR_OK)
    {
        assert(false);
        cout<<"Resource is not present"<<endl;
    }
    return it->second;
}

/**
 * SdiReferenceResource constructor is invoked to obtain specific data of the reference resource using resource node.
 */
SdiReferenceResource::SdiReferenceResource(std_config_node_t config_node)
{
    string cfg_attr;
    cfg_attr =std_config_attr_get(config_node,"type");
    if(cfg_attr.size()!=0)
    {
        resource_type=toResourceType(cfg_attr);
    }
    resource_alias_name=std_config_attr_get(config_node, "name");
}

/**
 * Validates information recieved from target and reference resources.
 * @param target[in] - reference to SdiTargetResource object.
 * @return true,if the resource alias names and resource types of target and reference
 * are equal.
 */
bool SdiReferenceResource::isValidResourceImplementation(SdiTargetResource &target)
{
    bool resource_valid=false;
    if(SdiReferenceResource::resource_alias_name==target.SdiTargetResource::resource_alias_name)
    {
        SDI_LOG("THE RESOURCE NAME MATCHES!!")
        if(SdiReferenceResource::resource_type==(target.SdiTargetResource::resource_type))
        {
            SDI_LOG("THE RESOURCE TYPE MATCHES!!")
            resource_valid=true;
        }
    }
    return resource_valid;
}

/**
 * Gets the entity type based on name. Entity names can be retrieved from config file.
 * @param entity_name[in] - entity name
 * @return entity type
 */
sdi_entity_type_t toEntityType(string entity_name)
{
    map<string,sdi_entity_type_t> emap;
    emap["SDI_ENTITY_SYSTEM_BOARD"]=SDI_ENTITY_SYSTEM_BOARD;
    emap["SDI_ENTITY_FAN_TRAY"]=SDI_ENTITY_FAN_TRAY;
    emap["SDI_ENTITY_PSU_TRAY"]=SDI_ENTITY_PSU_TRAY;
    map<string,sdi_entity_type_t>::iterator it;
    it=emap.find(entity_name);
    if(it->second<STD_ERR_OK)
    {
        assert(false);
        cout<<"Entity is not present"<<endl;
    }
    return it->second;
}

/**
 * SdiReferenceEntity constructor is invoked to obtain specific details of the reference entity using the entity node.
 */
SdiReferenceEntity::SdiReferenceEntity(std_config_node_t entity_node)
{
    string cfg_attr;
    /* Instance of an Entity. */
    int instance=0;
    std_config_node_t resource;
    cfg_attr=std_config_attr_get(entity_node,"instance");
    if(cfg_attr.size()!=0)
    {
        instance=atoi(std_config_attr_get(entity_node,"instance"));
        cout<<"Instance:"<<instance<<endl;
    }
    entity_name=std_config_attr_get(entity_node,"alias");
    cfg_attr = std_config_attr_get(entity_node, "type");
    if((cfg_attr.size()!=0))
    {
        entity_type = toEntityType(cfg_attr);
    }
    for (resource=std_config_get_child(entity_node); (resource != NULL); resource=std_config_next_node(resource))
    {
        cfg_attr =std_config_attr_get(resource,"type");
        if(cfg_attr.size()!=0)
        {
            res_type=toResourceType(cfg_attr);
        }
            reference_resource.push_back(new SdiReferenceResource(resource));
    }
}

/**
 * Validates information recieved from target and reference.
 * @param target[in] - reference to SdiTargetEntity object.
 * @return true,if the entity alias names and entity types of target and reference are equal.
 */
bool SdiReferenceEntity::isValidEntityImplementation(SdiTargetEntity &target)
{
    bool reference_valid=false;
    /* Resource list iterators.*/
    vector <SdiTargetResource *>::iterator target_resource_iterator;
    vector <SdiReferenceResource *>::iterator reference_resource_iterator;
    if(entity_name==target.entity_name)
    {
        if(entity_type==target.entity_type)
        {
             SDI_LOG("THE ENTITY TYPE MATCHES!!")
        }
        for(reference_resource_iterator=reference_resource.begin();reference_resource_iterator!=reference_resource.end();reference_resource_iterator++)
        {
            for(target_resource_iterator=target.target_resource.begin();target_resource_iterator!=target.target_resource.end();target_resource_iterator++)
            {
                reference_valid=(*(*reference_resource_iterator)).isValidResourceImplementation(*(*target_resource_iterator));
                if(reference_valid)
                    break;
            }
        }
    }
    return reference_valid;
}

/**
 * SdiReferenceImplementation constructor is invoked to traverse the config file and populate the reference entity list.
 */
SdiReferenceImplementation::SdiReferenceImplementation(void)
{
        std_config_hdl_t cfg_hdl;
        std_config_node_t root, entity;
        const char * entity_cfg_file="entity_gt.xml";
        cfg_hdl = std_config_load(entity_cfg_file);
        root =  std_config_get_root(cfg_hdl);
        for (entity=std_config_get_child(root);(entity != NULL); entity=std_config_next_node(entity))
        {
            reference_entity.push_back(new SdiReferenceEntity(entity));
        }
        std_config_unload(cfg_hdl);
}

/**
 * Validates information recieved from target and reference entities.
 * @param target[in] - reference to SdiTargetImplementation object.
 * @return true,if the contents in the target and reference entity lists are equal. Otherwise false.
 */
bool SdiReferenceImplementation::isValidImplementation(SdiTargetImplementation &target)
{
    bool valid=false;
    /* Entity list iterators.*/
    vector <SdiTargetEntity *>::iterator target_entity_iterator;
    vector <SdiReferenceEntity *>::iterator reference_entity_iterator;
    if(reference_entity.size()!=0 && target.target_entity.size()!=0)
    {
        for(reference_entity_iterator=reference_entity.begin();reference_entity_iterator!=reference_entity.end();reference_entity_iterator++)
        {
            for(target_entity_iterator=target.target_entity.begin();target_entity_iterator!=target.target_entity.end();target_entity_iterator++)
            {
                valid=(*(*reference_entity_iterator)).isValidEntityImplementation(*(*target_entity_iterator));
                if(valid)
                    break;
            }
        }
    }
    return valid;
}
