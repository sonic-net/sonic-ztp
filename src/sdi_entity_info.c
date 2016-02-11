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

/*
 * filename: sdi_entity_info.c
 */


/**************************************************************************************
 * brief   Entity Info Functionality provider.
 *         Currently entity_info providing support for read operations.
***************************************************************************************/

#include "sdi_resource_internal.h"
#include "sdi_sys_common.h"
#include "std_assert.h"
#include "sdi_entity_info_internal.h"
#include <string.h>


/**
 * brief - Read the entity info.
 *
 * param[in]   resource_hdl - resource .
 * param[out] entity_info - info to fill.
 *
 * return STD_ERR_OK for success and the respective error code in case of failure.
 */
t_std_error sdi_entity_info_read(sdi_resource_hdl_t resource_hdl,
                                 sdi_entity_info_t *entity_info)
{
    t_std_error rc = STD_ERR_OK;
    sdi_resource_priv_hdl_t entity_info_hdl = (sdi_resource_priv_hdl_t)resource_hdl;

    /* Validate arguments */
    STD_ASSERT(entity_info != NULL);
    STD_ASSERT(entity_info_hdl != NULL);

    if(sdi_resource_type_get(resource_hdl) != SDI_RESOURCE_ENTITY_INFO) {
        return(SDI_ERRCODE(EPERM));
    }

    memset(entity_info, 0, sizeof(sdi_entity_info_t));
    rc = ((entity_info_t *)entity_info_hdl->callback_fns)->entity_info_data_get(
                           entity_info_hdl->callback_hdl, entity_info);
    if(rc != STD_ERR_OK) {
        SDI_ERRMSG_LOG("Failed to get the entity content of %s ",
                       entity_info_hdl->name);
    }

    return rc;
}
