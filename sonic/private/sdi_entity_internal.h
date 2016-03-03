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
 * filename: sdi_entity_internal.h
 */


/**
 * @file sdi_entity_internal.h
 * @brief  entity  API for use within the SDI framework and drivers.
 *
 * @defgroup sdi_internal_entity_api SDI Internal Entity API
 * @brief API to manimuplate resources within SDI.
 *
 * @ingroup sdi_internal
 * Entity refers to collection of resources that are grouped as single element.
 * Every entity is typically identied with a unique partnumber, serial number etc.
 *
 * @{
 */

#ifndef __SDI_ENTITY_INTERNAL_H_
#define __SDI_ENTITY_INTERNAL_H_

#include "sdi_entity.h"
#include "sdi_resource_internal.h"
#include "sdi_pin.h"
#include "sdi_pin_group.h"
#include "sdi_entity_info.h"
#include "std_llist.h"

/**
 * @struct sdi_entity_t
 * entity data structure which contains details of an entity
 */
struct sdi_entity {
    char name[SDI_MAX_NAME_LEN]; /**<null terminated string for name of the entity*/
    uint_t oper_support_flag; /**<functionality or operation support of an entity.
                               * entity can support different reset types,
                               * power control support, etc.
                               * see also @ref sdi_entity_feature_t */
    sdi_entity_type_t type; /**<type of an entity*/
    uint_t instance; /**<instance of an entity*/
    uint_t reset_value[MAX_NUM_RESET]; /**<value to reset as per type */
    uint_t delay; /**<apply default config after power ON - duration */
    sdi_pin_bus_hdl_t power_output_status_pin_hdl; /**<psu power output
                                                    * status handler */
    sdi_pin_bus_hdl_t pres_pin_hdl; /**<presence handler */
    sdi_pin_bus_hdl_t fault_status_pin_hdl; /**<fault status handler */
    sdi_pin_bus_hdl_t power_pin_hdl; /**<power ON/OFF handler */
    sdi_pin_group_bus_hdl_t reset_pin_grp_hdl[MAX_NUM_RESET]; /**<reset pin
                                                               * group handlers */
    sdi_resource_hdl_t entity_info_hdl; /**entity_info handler of an entity */
    sdi_entity_info_t entity_info; /**<entity_info of an entity */
    std_dll_head *resource_list;/**<list of resources that are part of this entity*/
}sdi_entity_t;

/**
 * @defgroup sdi_entity_feature_t SDI ENTITY FEATURES.
 * List of entity features supported by SDI.
 * @ingroup sdi_sys
 * @{
 */
typedef enum {
    SDI_WARM_RESET_TYPE, /**<WARM RESET TYPE support bit */
    SDI_COLD_RESET_TYPE, /**<COLD RESET TYPE support bit */
    SDI_HOTSWAPPABLE,    /**<HOTSWAPPABLE device */
    SDI_PWR_CTRL_SUPPORT, /**<POWER CONTROL SUPPORT bit */
} sdi_entity_feature_t;
/**
 * @}
 */

/** An opaque handle to entity. */
typedef struct sdi_entity *sdi_entity_priv_hdl_t;

/**
 * @brief create an structure to hold entity information, and return an
 * handle to it.
 * @param[in] type - type of the entity that has to be created.
 * @param[in] instance - instance of the entity with respect to  type.
 * @param[in] name - pointer to name of the entity. name must be null
 *            terminated and it's lenth should be less than
 *            SDI_MAX_NAME_LEN
 * @return handle to the entity created if successful else returns NULL.
 *
 * @note
 * Application must subsequently add this handle to global entity-pool if needed
 */
sdi_entity_hdl_t sdi_entity_create(sdi_entity_type_t type, uint_t instance, const char *name);

/**
 * @brief Add the entity specified by hdl to the entity-pool.
 * @param[in] hdl handle of the entity to be added.
 */
void sdi_entity_add(sdi_entity_hdl_t hdl);

/**
 * @brief add the specified resource to specified entity
 * @param[in] ehdl handle of the entity to which the resource has to be added.
 * @param[in] rhld handle of the resource that must be added to the entity.
 * @param[in] name name by which the specified entity will be known within this entity
 * @param[in] name name by which the specified entity will be known within this entity
 */
void sdi_entity_add_resource(sdi_entity_hdl_t ehdl, sdi_resource_hdl_t rhdl, const char *name);

/**
 * @brief Initializes the internal data structures for the entity and creates entity-db.
 *
 * @param entity_cfg_file[in] - Entity config files which has inforamtion about the
 * devices on each entity
 *
 */
void sdi_register_entities(const char * driver_cfg_file);

/**
 * @brief Retrieve feature support of the entity.
 *
 * @param entity_hdl[in] - Handler of entity.
 * @param type[in] - type of entity feature.
 * return true, if feature supported. Otherwise false.
 */
bool sdi_is_entity_feature_support(sdi_entity_hdl_t entity_hdl, sdi_entity_feature_t type);

/**
 * @}
 */

#endif /*__SDI_ENTITY_INTERNAL_H_*/
