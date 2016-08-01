
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
/*************************************************************
 *Implementation of SDI Target Entity and SDI Target Resource.
 *************************************************************/

#include "unittest/sdi_unit_test.h"
#include <iostream>

/**
 * SdiTargetResource constructor is invoked to obtain specific details of each resource in every
 * entity using sdi resource handle.
 */
SdiTargetResource::SdiTargetResource(sdi_resource_hdl_t res_hdl)
{
    resource_alias_name=sdi_resource_alias_get(res_hdl);
    resource_type=sdi_resource_type_get(res_hdl);
}

/**
 * A callback funtion which will be called for each resource.
 * @param res_hdl[in] - Resource handle
 * @param user_data[in] - user data
 * @todo List to be added for other resources.
 */
void register_resource(sdi_resource_hdl_t res_hdl, void *user_data)
{
    SdiTargetEntity *self=static_cast<SdiTargetEntity *>(user_data);
    if (sdi_resource_type_get(res_hdl) == SDI_RESOURCE_FAN) {
        self->target_resource.push_back(new SdiTargetFanResource(res_hdl));
    }
    else
    {
        self->target_resource.push_back(new SdiTargetResource(res_hdl));
    }
}

/**
 * SdiTargetEntity constructor is invoked to obtain specific details of all target entities using sdi entity handle.
 */
SdiTargetEntity::SdiTargetEntity(sdi_entity_hdl_t hdl)
{
    entity_name=sdi_entity_name_get(hdl);
    entity_type=sdi_entity_type_get(hdl);
    {
        sdi_entity_for_each_resource(hdl,register_resource, this);
    }
}

/**
 * SdiTargetFanResource construtor is invoked to get specific
 * details of Target Fan Resource.
 * @todo Get the speed of fan
 */
SdiTargetFanResource::SdiTargetFanResource(sdi_resource_hdl_t res_hdl):SdiTargetResource(res_hdl)
{
    hdl=res_hdl;
}

/**
 * SdiTargetImplementation constructor is invoked to populate the target entity list.
 * @todo An api to get the maximum number of entities.
 */
SdiTargetImplementation::SdiTargetImplementation(void)
{
#define SDI_MAX_ENTITY_TYPE_SUPPORTED 3
    for(entity_type=0; (entity_type<SDI_MAX_ENTITY_TYPE_SUPPORTED); entity_type++)
    {
        max_entities=sdi_entity_count_get((static_cast<sdi_entity_type_t>(entity_type)));
        for(entity_id=0; (entity_id<=max_entities);++entity_id) {
            hdl = sdi_entity_lookup(static_cast<sdi_entity_type_t>(entity_type), entity_id);
            if(hdl != NULL)
                target_entity.push_back(new SdiTargetEntity(hdl));
        }
    }
}
