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
 * filename: sdi_startup.c
 */


/**************************************************************************************
 * SDI Framework core functions.
 ***************************************************************************************/
#include "std_error_codes.h"
#include "sdi_bus_framework.h"
#include "sdi_resource_internal.h"
#include "sdi_sys_common.h"
#include "private/sdi_entity_internal.h"
#include "std_bit_ops.h"

/**
 * @var sdi_init_status used to get the sdi initialization status
 */
static bool sdi_init_status = false;

/**
 * Initialize the specified entity.
 * Upon Initialization, default configurations as specified for platform would
 * be applied
 * param[in] hdl - handle to the entity whose information has to be initialised.
 * param[out] init_status - entity initialization status.
 * return None
 */
static void sdi_sys_entity_init(sdi_entity_hdl_t hdl, void *init_status)
{
    t_std_error ret = STD_ERR_OK;

   /* Initialize fixed entities.User(like PAS) will initialize Hot-Swappable entities*/
    if (STD_BIT_TEST((((sdi_entity_priv_hdl_t)hdl)->oper_support_flag),
                        SDI_HOTSWAPPABLE) == 0) {
        ret = sdi_entity_init(hdl);
        /* Find the initial failure, it could be the reason for the subsequent
         * component or entity failures */
        if ((init_status != NULL) && (ret != STD_ERR_OK) &&
                            (*((t_std_error *)init_status) == STD_ERR_OK)) {
            *((t_std_error *)init_status) = ret;
            SDI_ERRMSG_LOG("Entity(%s) Init failed.rc=%d \n",
                          ((sdi_entity_priv_hdl_t)hdl)->name, ret);
        }
    }
}

/**
 * Initializes the SDI sub-system which includes sdi bus framework intialization and
 * creates db files for dirvers, resources and entities
 *
 * return STD_ERR_OK on success and standard error on failure
 */
t_std_error sdi_sys_init(void)
{
    t_std_error rc = STD_ERR_OK;

    sdi_bus_framework_init();
    sdi_resource_mgr_init();
    sdi_register_drivers(SDI_DEVICE_CONFIG_FILE);
    sdi_register_entities(SDI_ENTITY_CONFIG_FILE);
    /* Initialise each entities */
    sdi_entity_for_each(&sdi_sys_entity_init, &rc);
    if (rc != STD_ERR_OK) {
        SDI_ERRMSG_LOG("Atleast one Entity failed in the init."
                       "Check the SDI log for detail.rc=%d \n", rc);
    }

    sdi_init_status = true;

    return rc;
}

/**
 * Returns the initialization status for sdi sub-system
 */
bool is_sdi_inited(void)
{
    return sdi_init_status;
}
