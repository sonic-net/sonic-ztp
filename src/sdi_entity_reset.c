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
 * filename: sdi_entity_reset.c
 */


/**************************************************************************************
 * Implementation of entity reset and power status control APIs.
 ***************************************************************************************/
#include "sdi_entity.h"
#include "sdi_pin_bus_api.h"
#include "sdi_pin_group_bus_api.h"
#include "private/sdi_entity_internal.h"
#include "std_time_tools.h"
#include "std_assert.h"
#include <unistd.h>

/**
 * Reset the specified entity.
 * Reset of entity results in reset of resources and devices as per the reset type.
 * Upon reset, default configurations as specified for platform would be applied.
 * param[in] hdl - handle to the entity whose information has to be retrieved.
 * param[in] type – type of reset to perform.
 * return STD_ERR_OK on success and standard error on failure
 */
t_std_error sdi_entity_reset(sdi_entity_hdl_t hdl, sdi_reset_type_t type)
{
    t_std_error ret = STD_ERR_OK;
    sdi_entity_priv_hdl_t entity_priv_hdl = NULL;

    STD_ASSERT(hdl != NULL);
    entity_priv_hdl = (sdi_entity_priv_hdl_t)hdl;

    if (type >= MAX_NUM_RESET) {
        return SDI_ERRCODE(ENOTSUP);
    }

    /* Check this entity supports reset for this type */
    if (sdi_is_entity_feature_support(entity_priv_hdl, type) == true) {
        if (entity_priv_hdl->reset_pin_grp_hdl[type] == NULL) {
            return SDI_ERRCODE(EINVAL);
        }
        ret = sdi_pin_group_acquire_bus(entity_priv_hdl->reset_pin_grp_hdl[type]);
        if (ret != STD_ERR_OK) {
            return ret;
        }

        ret = sdi_pin_group_write_level(entity_priv_hdl->reset_pin_grp_hdl[type],
                                        entity_priv_hdl->reset_value[type]);

        sdi_pin_group_release_bus(entity_priv_hdl->reset_pin_grp_hdl[type]);

        if (ret != STD_ERR_OK) {
            return ret;
        }
    } else {
        /* return Unsupported , when particular reset type is not supported */
        return SDI_ERRCODE(ENOTSUP);
    }

    /* Take nap before reinit the entity and resources */
    std_usleep(MILLI_TO_MICRO(entity_priv_hdl->delay));
    sdi_entity_init(hdl);
    return ret;
}

/**
 * Change/Control the power status for the specified entity.
 *
 * param[in] hdl - handle to the entity whose information has to be retrieved.
 * param[in] enable – power state to enable / disable
 * return STD_ERR_OK on success and standard error on failure
 */
t_std_error sdi_entity_power_status_control(sdi_entity_hdl_t hdl, bool enable)
{
    t_std_error ret = STD_ERR_OK;
    sdi_entity_priv_hdl_t entity_priv_hdl = NULL;

    STD_ASSERT(hdl != NULL);
    entity_priv_hdl = (sdi_entity_priv_hdl_t)hdl;

    /* Check this entity supports power ON/OFF */
    if (sdi_is_entity_feature_support(entity_priv_hdl, SDI_PWR_CTRL_SUPPORT) == true) {
        if (entity_priv_hdl->power_pin_hdl != NULL) {
            ret = sdi_pin_write_level(entity_priv_hdl->power_pin_hdl, enable);
            if (ret != STD_ERR_OK) {
                return ret;
            }
        } else {
            return SDI_ERRCODE(ENOTSUP);
        }
        if (enable == true) {
            std_usleep(MILLI_TO_MICRO(entity_priv_hdl->delay));
            sdi_entity_init(hdl);
        }
        return STD_ERR_OK;
    } else {
        return SDI_ERRCODE(ENOTSUP);
    }
}
