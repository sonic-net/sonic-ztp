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
 * filename: sdi_entity.c
 */


/**************************************************************************************
 * Implementation of generic entity  and resource API.
 ***************************************************************************************/
#include "sdi_entity.h"
#include "sdi_entity_info.h"
#include "sdi_fan.h"
#include "sdi_sys_common.h"
#include "sdi_pin_bus_api.h"
#include "private/sdi_entity_internal.h"
#include "std_assert.h"
#include "std_bit_ops.h"

/**
 * Retrieve presence status of given entity.
 *
 * entity_hdl[in] - handle to the entity whose information has to be retrieved.
 * presence[out]    - true if entity is present, false otherwise
 *
 * return STD_ERR_OK on success and standard error on failure
 */
t_std_error sdi_entity_presence_get(sdi_entity_hdl_t entity_hdl, bool *presence)
{
    sdi_entity_priv_hdl_t entity_priv_hdl = NULL;
    sdi_pin_bus_level_t bus_val = SDI_PIN_LEVEL_LOW;
    t_std_error rc = STD_ERR_OK;

    STD_ASSERT(entity_hdl != NULL);
    STD_ASSERT(presence != NULL);

    entity_priv_hdl = (sdi_entity_priv_hdl_t)entity_hdl;
    if (STD_BIT_TEST(entity_priv_hdl->oper_support_flag, SDI_HOTSWAPPABLE)) {
        STD_ASSERT(entity_priv_hdl->pres_pin_hdl != NULL);
        rc = sdi_pin_read_level(entity_priv_hdl->pres_pin_hdl,
                                 &bus_val);
        if(rc != STD_ERR_OK){
            return rc;
        }
    } else {
        *presence = true;
        return STD_ERR_OK;
    }

    *presence = ( (bus_val == SDI_PIN_LEVEL_HIGH) ? true : false );
    return rc;
}
/**
 * This function is required to support the fault status for the entities
 * which does not have a fault status pin. The entity fault is determined by checking
 * all the resource fault status within that entity and determining the fault status
 * of the entity.This function will be called from sdi_entity_fault_status_get for each
 * entity.As of now only fan is supported and may be extend in future.
 */
static void sdi_check_fault_each_resource(sdi_resource_hdl_t hdl, void *data)
{
    t_std_error rc = STD_ERR_OK;
    bool fault = false;

    if (sdi_resource_type_get(hdl) == SDI_RESOURCE_FAN)
    {
        rc = sdi_fan_status_get(hdl, &fault);
        if (rc != STD_ERR_OK)
        {
            SDI_ERRMSG_LOG("Error in getting fault status for %s %d", sdi_resource_name_get(hdl),rc);
        }
        else
        {
            *((bool *)data) |= fault;
        }
    }
}

/**
 * Checks the fault status for a given entity
 *
 * entity_hdl[in] - handle to the entity whose information has to be retrieved.
 * fault[out] - true if entity has any fault, false otherwise.
 *
 * return STD_ERR_OK on success and standard error on failure
 */
t_std_error sdi_entity_fault_status_get(sdi_entity_hdl_t entity_hdl, bool *fault)
{
    sdi_entity_priv_hdl_t entity_priv_hdl = NULL;
    sdi_pin_bus_level_t bus_val = SDI_PIN_LEVEL_LOW;
    bool pres = false;
    t_std_error rc = STD_ERR_OK;

    STD_ASSERT(entity_hdl != NULL);
    STD_ASSERT(fault != NULL);
    *fault = false;

    entity_priv_hdl = (sdi_entity_priv_hdl_t)entity_hdl;

    if (entity_priv_hdl->fault_status_pin_hdl != NULL) {
        rc = sdi_pin_read_level(entity_priv_hdl->fault_status_pin_hdl,
                                &bus_val);
        if(rc != STD_ERR_OK){
            SDI_ERRMSG_LOG("Error in getting fault status,rc = %d",rc);
        } else {
            *fault = ( (bus_val == SDI_PIN_LEVEL_HIGH) ? true : false );
        }
        return rc;

    } else {
        /*
         * For those entities which does not have fault status pin, fault is determined by checking
         * all the resource fault status within that entity and determining the fault status
         * of the entity
         */
        rc = sdi_entity_presence_get(entity_hdl, &pres);
        if(rc != STD_ERR_OK){
            return rc;
        }
        if(pres != false){
            sdi_entity_for_each_resource(entity_hdl, sdi_check_fault_each_resource, fault);
            return rc;
        }
        else{
            return SDI_ERRCODE(ENXIO);
        }
    }
}

/**
 * Checks the psu output power status for a given psu
 *
 * entity_hdl[in] - handle to the psu entity whose information has to be retrieved.
 * status[out] - true if psu output status is good , false otherwise.
 *
 * return STD_ERR_OK on success , standard error on failure
 */
t_std_error sdi_entity_psu_output_power_status_get(sdi_entity_hdl_t entity_hdl,
                                                   bool *status)
{
    sdi_entity_priv_hdl_t entity_priv_hdl = NULL;
    sdi_pin_bus_level_t bus_val = SDI_PIN_LEVEL_LOW;
    bool pres = false;
    t_std_error rc = STD_ERR_OK;

    STD_ASSERT(entity_hdl != NULL);
    STD_ASSERT(status != NULL);
    *status = false;

    entity_priv_hdl = (sdi_entity_priv_hdl_t)entity_hdl;

    if (entity_priv_hdl->type != SDI_ENTITY_PSU_TRAY) {
        SDI_ERRMSG_LOG("%s : Not a PSU entity", entity_priv_hdl->name);
        return SDI_ERRCODE(ENOTSUP);
    }

    rc = sdi_entity_presence_get(entity_hdl, &pres);
    if (rc != STD_ERR_OK) {
        SDI_ERRMSG_LOG("%s Unable to get Present status:rc=%d",
                       entity_priv_hdl->name, rc);
        return rc;
    }
    if (pres == false) {
        SDI_ERRMSG_LOG("%s entity is not present", entity_priv_hdl->name);
        return(SDI_ERRCODE(EPERM));
    }

    if (entity_priv_hdl->power_output_status_pin_hdl != NULL) {
        rc = sdi_pin_read_level(entity_priv_hdl->power_output_status_pin_hdl,
                                &bus_val);
        if(rc != STD_ERR_OK){
           SDI_ERRMSG_LOG("Error in getting psu output power status, rc=%d",rc);
        } else {
           *status = ( (bus_val == SDI_PIN_LEVEL_HIGH) ? true : false );
        }
    }
    return rc;
}
