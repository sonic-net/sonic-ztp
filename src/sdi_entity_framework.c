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
 * filename: sdi_entity_framework.c
 */


/**************************************************************************************
 * Core SDI framework which provides core api that work on entity.
 ***************************************************************************************/
#include "sdi_resource_internal.h"
#include "private/sdi_entity_internal.h"
#include "sdi_entity.h"
#include "sdi_sys_common.h"
#include "sdi_pin_bus_framework.h"
#include "sdi_pin_group_bus_framework.h"
#include "sdi_entity_info.h"
#include "std_llist.h"
#include "std_config_node.h"
#include "std_assert.h"
#include "std_utils.h"
#include "std_time_tools.h"
#include "std_bit_ops.h"
#include <errno.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#define SDI_STR_FIXED_SLOT           "FIXED_SLOT"
#define SDI_FIXED_SLOT_SIZE          10

static const char *reset_type_attr_str[MAX_NUM_RESET] = {"warm_reset", "cold_reset"};

/**
 * var Head of entity list
 */
static std_dll_head entity_list;

/**
 * sdi_entity_node_t - Used to hold entity related data
 */
typedef struct sdi_entity_node {
    std_dll node; /**< node to an entity*/
    sdi_entity_hdl_t entity_hdl; /**< entity specific data*/
} sdi_entity_node_t;

/**
 * sdi_entity_resource_node_t - Used to maintain the list of resources on linked list
 */
typedef struct sdi_entity_resource_node {
    std_dll node;  /**< node to an entity resource*/
    sdi_resource_hdl_t hdl; /**< resource specific data*/
} sdi_entity_resource_node_t;

/**
 * Returns the name of entity
 */
const char *sdi_entity_name_get(sdi_entity_hdl_t hdl)
{
    return ((sdi_entity_priv_hdl_t)hdl)->name;
}

/**
 * Returns the type of entity
 */
sdi_entity_type_t sdi_entity_type_get(sdi_entity_hdl_t hdl)
{
    return ((sdi_entity_priv_hdl_t)hdl)->type;
}

/**
 * Return the first entity dllnode from entity list
 */
static sdi_entity_node_t *sdi_entity_find_first(void)
{
    return (sdi_entity_node_t *)std_dll_getfirst(&entity_list);
}

/**
 * Return the entity dllnode next to given dllnode from entity list
 */
static sdi_entity_node_t *sdi_entity_find_next(sdi_entity_node_t *node)
{
    return(sdi_entity_node_t *)std_dll_getnext(&entity_list, (std_dll *)node);
}

/**
 * Retrieve number of entities supported by system of given type
 * etype[in] : entity type
 * return number of entities of the specified type
 */
uint_t sdi_entity_count_get(sdi_entity_type_t etype)
{
    uint_t entity_count = 0;
    sdi_entity_node_t *hdl = NULL;
    sdi_entity_priv_hdl_t entity_hdl = NULL;

    for (hdl = sdi_entity_find_first(); (hdl != NULL);
         hdl = sdi_entity_find_next(hdl))
    {
        entity_hdl = (sdi_entity_priv_hdl_t)hdl->entity_hdl;

        if(entity_hdl->type == etype)
        {
            entity_count++;
        }
    }
    return entity_count;

}

/**
 * Iterate on entity list and run specified function on every entity
 *
 * hdl[in] - entity handle
 * fn[in] - function that would be called for each entity
 * user_data[in] - user data that will be passed to the function
 */
void sdi_entity_for_each(void (*fn)(sdi_entity_hdl_t hdl, void *user_data),
                         void *user_data)
{
    sdi_entity_node_t *hdl = NULL;
    for (hdl = sdi_entity_find_first(); (hdl != NULL);
         hdl = sdi_entity_find_next(hdl))
    {
        (*fn)(hdl->entity_hdl, user_data);
    }
}
/**
 * Retrieve the handle of the specified entity.
 * etype[in] - Type of entity
 * instance[in] - Instance of the entity of specified type that has
 * to be retrieved.
 * return - If the API succeeds, the handle to the specified entity,
 * else NULL.
 */
sdi_entity_hdl_t sdi_entity_lookup(sdi_entity_type_t etype, uint_t instance)
{
    sdi_entity_node_t *hdl = NULL;
    sdi_entity_priv_hdl_t entity_hdl = NULL;


    for (hdl = sdi_entity_find_first(); (hdl != NULL);
         hdl = sdi_entity_find_next(hdl))
    {
        entity_hdl = (sdi_entity_priv_hdl_t)hdl->entity_hdl;

        if ((entity_hdl->type == etype) && (entity_hdl->instance == instance))
        {
            return hdl->entity_hdl;
        }
    }
    return NULL;
}
/**
 * Retrieve number of resources of given type within given entity.
 * hdl[in] - handle to the entity whose information has to be retrieved.
 * resource_type[in] - type of resource. Example, temperature, fan etc.
 * return - returns the number of entities of the specified type that
 * are supported on this system.
 */
uint_t sdi_entity_resource_count_get(sdi_entity_hdl_t hdl, sdi_resource_type_t resource_type)
{
    uint_t resource_count = 0;
    sdi_entity_resource_node_t *node = NULL;
    sdi_entity_priv_hdl_t entity_hdl = NULL;
    sdi_resource_priv_hdl_t resource_hdl = NULL;
    std_dll_head *resource_head = NULL;

    STD_ASSERT(hdl != NULL);

    entity_hdl = (sdi_entity_priv_hdl_t)hdl;
    resource_head = (std_dll_head *)entity_hdl->resource_list;
    STD_ASSERT(resource_head != NULL);

    for ((node=(sdi_entity_resource_node_t *)std_dll_getfirst(resource_head));
         (node != NULL);
         (node=(sdi_entity_resource_node_t *)std_dll_getnext(resource_head, (std_dll *)node)))
    {
        resource_hdl = (sdi_resource_priv_hdl_t)node->hdl;
        if(resource_hdl->type == resource_type)
        {
            resource_count++;
        }
    }
    return resource_count;
}
/**
 * Retrieve the handle of the resource whose name is known.
 * hdl[in] - handle to the entity whose information has to be
 * retrieved.
 * resource[in] - The type of resource that needs to be looked up.
 * alias[in] - the name of the alias. example, "BOOT_STATUS" led.
 * return - if a resource maching the criteria is found, returns handle to it.
 * else returns NULL.
 */
sdi_resource_hdl_t sdi_entity_resource_lookup(sdi_entity_hdl_t hdl,
                                              sdi_resource_type_t resource, const char *alias)
{
    sdi_entity_resource_node_t *node = NULL;
    sdi_entity_priv_hdl_t entity_hdl = NULL;
    sdi_resource_priv_hdl_t resource_hdl = NULL;
    std_dll_head *resource_head = NULL;

    STD_ASSERT(hdl != NULL);

    entity_hdl = (sdi_entity_priv_hdl_t)hdl;
    resource_head = (std_dll_head *)entity_hdl->resource_list;
    STD_ASSERT(resource_head != NULL);

    for ((node=(sdi_entity_resource_node_t *)std_dll_getfirst(resource_head));
         (node != NULL);
         (node=(sdi_entity_resource_node_t *)std_dll_getnext(resource_head, (std_dll *)node)))
    {
        resource_hdl = (sdi_resource_priv_hdl_t)node->hdl;
        if (strncmp(resource_hdl->alias, alias, SDI_MAX_NAME_LEN) == 0)
        {
            return node->hdl;
        }
    }
    return NULL;
}

/**
 * Retrieve the alias name of the given resource.
 * resource_hdl[in] - handle to the resource whose name has to be retrieved.
 * return  - the alias name of the resource. example, "BOOT_STATUS" led.
 * else returns NULL.
 */
const char * sdi_resource_alias_get(sdi_resource_hdl_t resource_hdl)
{
    STD_ASSERT(resource_hdl != NULL);

    return ((sdi_resource_priv_hdl_t)resource_hdl)->alias;
}

/**
 * Iterate on each resource and run specified function on every entity
 *
 * hdl[in] - Entity handle
 * fn[in] - function that would be called for each resource
 * user_data[in] - user data that will be passed to the function
 */
void sdi_entity_for_each_resource(sdi_entity_hdl_t hdl,
                                  void (*fn)(sdi_resource_hdl_t hdl, void *user_data),
                                  void *user_data)
{
    sdi_entity_resource_node_t *node;
    sdi_entity_priv_hdl_t entity_hdl=(sdi_entity_priv_hdl_t)hdl;
    std_dll_head *resource_head=(std_dll_head *)entity_hdl->resource_list;

    STD_ASSERT(fn != NULL);

    for ((node=(sdi_entity_resource_node_t *)std_dll_getfirst(resource_head));
     (node);
     (node=(sdi_entity_resource_node_t *)std_dll_getnext(resource_head, (std_dll *)node)))
    {
        (*fn)(node->hdl, user_data);
    }
}

/**
 * create an structure to hold entity information, and return a handle to it
 *
 * type[in] - type of the entity that has to be created.
 * instance[in] - instance of the entity
 * name[in] - Name of the entity
 *
 * return handle to the entity created if successful else returns NULL.
 */
sdi_entity_hdl_t sdi_entity_create(sdi_entity_type_t type, uint_t instance, const char *name)
{
    sdi_reset_type_t reset_type;
    sdi_entity_priv_hdl_t entity_hdl = (sdi_entity_priv_hdl_t)calloc(1, sizeof(struct sdi_entity));
    STD_ASSERT(entity_hdl != NULL);

    STD_ASSERT(name != NULL);

    strncpy(entity_hdl->name, name, SDI_MAX_NAME_LEN);
    entity_hdl->type=type;
    entity_hdl->instance=instance;
    entity_hdl->oper_support_flag = 0;
    entity_hdl->entity_info_hdl = NULL;
    entity_hdl->delay = 0;
    entity_hdl->power_output_status_pin_hdl = NULL;
    entity_hdl->pres_pin_hdl = NULL;
    entity_hdl->fault_status_pin_hdl = NULL;
    entity_hdl->power_pin_hdl = NULL;
    for (reset_type = 0; reset_type < MAX_NUM_RESET; reset_type++) {
         entity_hdl->reset_pin_grp_hdl[reset_type] = NULL;
    }
    entity_hdl->resource_list = (std_dll_head *)calloc(1, sizeof(std_dll_head));
    STD_ASSERT(entity_hdl->resource_list != NULL);
    std_dll_init(entity_hdl->resource_list);

    return (sdi_entity_hdl_t)entity_hdl;
}

/**
 * Add the entity specified by hdl to the entity-pool.
 *
 * hdl[in] - handle of the entity to be added
 */
void sdi_entity_add(sdi_entity_hdl_t hdl)
{
    sdi_entity_node_t *newnode=(sdi_entity_node_t *)calloc(1, sizeof(sdi_entity_node_t));
    STD_ASSERT(newnode != NULL);

    newnode->entity_hdl = hdl;

    std_dll_insertatback(&entity_list, (std_dll *)newnode);
}

/**
 * Add the specified resource to specified entity
 *
 * ehdl[in] -  handle of the entity to which the resource has to be added.
 * resource[in] - handle of the resource which needs to be added to entity
 * name[in] - Name of the resource by which it known within this entity
 */
void sdi_entity_add_resource(sdi_entity_hdl_t ehdl, sdi_resource_hdl_t resource, const char *name)
{
    sdi_entity_resource_node_t *newnode = NULL;

    STD_ASSERT(name != NULL);

    newnode = (sdi_entity_resource_node_t *)calloc(1, sizeof(sdi_entity_resource_node_t));
    STD_ASSERT(newnode != NULL);

    strncpy(((sdi_resource_priv_hdl_t)resource)->alias, name, SDI_MAX_NAME_LEN);
    newnode->hdl = resource;
    std_dll_insertatback(((sdi_entity_priv_hdl_t)ehdl)->resource_list, (std_dll *)newnode);
}


/**
 * Gets the entity type based on name. Entity names can be retrieved from config file
 *
 * entity_name[in] - entity name
 *
 * return entity type
 */
static sdi_entity_type_t sdi_entity_string_to_type(const char *entity_name)
{
    int entity_index;
    /* Note: Names must be in the same order as defined for enum sdi_entity_type_t */
    static const char * sdi_entity_names[] = {
        "SDI_ENTITY_SYSTEM_BOARD",
        "SDI_ENTITY_FAN_TRAY",
        "SDI_ENTITY_PSU_TRAY"
    };
    int max_sdi_entities = (sizeof(sdi_entity_names)/sizeof(sdi_entity_names[0]));

    STD_ASSERT(entity_name != NULL);

    entity_index = dn_std_string_to_enum(sdi_entity_names, max_sdi_entities, entity_name);

    if(entity_index < STD_ERR_OK){
    /*Could not find entity type, means SDI entiy-list db is corrupted, hence assert*/
        STD_ASSERT(false);
    }

    return (sdi_entity_type_t)entity_index;
}

/**
 * Adds entity handler to the entity list
 *
 * hdl[in] - Handler of entity which needs to be added to entity list
 */
static void sdi_add_entity(sdi_entity_hdl_t entity_hdl)
{
    sdi_entity_node_t *node = NULL;

    node=(sdi_entity_node_t *)calloc(1, sizeof(sdi_entity_node_t));
    STD_ASSERT(node != NULL);

    node->entity_hdl = entity_hdl;
    std_dll_insertatfront(&entity_list, (std_dll *)node);
}

/**
 * Add or register resources to the entity.
 *
 * param node[in] - Entity node whose attribute values needs to be determined
 * param entity_hdl[in] - Handler of entity which needs to add resources
 * return None
 */
static void sdi_entity_register_resources(std_config_node_t node, sdi_entity_hdl_t entity_hdl)
{
    std_config_node_t resource = NULL;

    for ((resource = std_config_get_child(node));
         (resource != NULL);
         (resource = std_config_next_node(resource)))
    {
        sdi_resource_hdl_t res_hdl = NULL;
        char *resource_name = NULL;
        char *resource_reference = NULL;

        STD_ASSERT((resource_reference = std_config_attr_get(resource, "reference")) != NULL);
        STD_ASSERT((resource_name = std_config_attr_get(resource, "name")) != NULL);

        res_hdl = sdi_find_resource_by_name(resource_reference);
        STD_ASSERT(res_hdl != NULL);

        /* In case of ENTITY_INFO, initialise the entity_info handler of entity */
        if (sdi_resource_type_get(res_hdl) == SDI_RESOURCE_ENTITY_INFO) {
            ((sdi_entity_priv_hdl_t)entity_hdl)->entity_info_hdl = res_hdl;
        }
        sdi_entity_add_resource(entity_hdl, res_hdl, resource_name);
    }
}

/**
 * Retrieve feature support of the entity.
 *
 * param entity_hdl[in] - Handler of entity.
 * param type[in] - type of entity feature.
 * return true, if feature supported. Otherwise false.
 */
bool sdi_is_entity_feature_support(sdi_entity_hdl_t entity_hdl,
                                   sdi_entity_feature_t type)
{
    STD_ASSERT(entity_hdl != NULL);
    return (STD_BIT_TEST(((sdi_entity_priv_hdl_t)entity_hdl)->oper_support_flag,
                                             type) != 0);
}

/**
 * Fill reset and power control status attributes and values to the entity.
 *
 * param node[in] - Entity node whose attribute values needs to be determined
 * param entity_hdl[in] - Handler of entity which needs to be filled
 * return None
 */
static void sdi_fill_reset_info(std_config_node_t node, sdi_entity_hdl_t entity_hdl)
{
    char *config_attr = NULL;
    sdi_reset_type_t reset_type;
    sdi_entity_priv_hdl_t entity_priv_hdl = NULL;

    entity_priv_hdl = (sdi_entity_priv_hdl_t) entity_hdl;

    for (reset_type = WARM_RESET; reset_type < MAX_NUM_RESET; reset_type++) {
         config_attr = std_config_attr_get(node, reset_type_attr_str[reset_type]);
         if (config_attr != NULL) {
             STD_BIT_SET(entity_priv_hdl->oper_support_flag, reset_type);
             entity_priv_hdl->reset_value[reset_type] = strtoul(config_attr, NULL, 0x10);
         }
    }

    config_attr = std_config_attr_get(node, "warm_reset_register");
    if (config_attr != NULL) {
        entity_priv_hdl->reset_pin_grp_hdl[WARM_RESET] =
                         sdi_get_pin_group_bus_handle_by_name(config_attr);
    }

    config_attr = std_config_attr_get(node, "cold_reset_register");
    if (config_attr != NULL) {
        entity_priv_hdl->reset_pin_grp_hdl[COLD_RESET] =
                         sdi_get_pin_group_bus_handle_by_name(config_attr);
    }

    config_attr = std_config_attr_get(node, "power");
    if (config_attr != NULL) {
        STD_BIT_SET(entity_priv_hdl->oper_support_flag, SDI_PWR_CTRL_SUPPORT);
        entity_priv_hdl->power_pin_hdl = sdi_get_pin_bus_handle_by_name(config_attr);
    }

    config_attr = std_config_attr_get(node, "delay");
    if (config_attr != NULL) {
        entity_priv_hdl->delay = strtoul(config_attr, NULL, 10);
    }

}

/**
 * Allocates and Initilizes the data structures for a given node and adds this to entity
 * list
 *
 * node[in] - Node whose attribute values needs to be determined
 *
 */
void sdi_register_entity(std_config_node_t node)
{
    const char *entity_name=std_config_name_get(node);
    char *alias_name = NULL;
    char *presence_name = NULL;
    char *fault_name = NULL;
    char alias[SDI_MAX_NAME_LEN] = {0};
    char *config_attr = NULL;
    uint_t instance = 0;
    sdi_entity_type_t entity_type;
    sdi_entity_hdl_t entity_hdl = NULL;
    sdi_entity_priv_hdl_t entity_priv_hdl = NULL;

    memset(alias, '\0', sizeof(alias));
    /**
     * @TODO: std_config_attr_get may return null if attribute is not defined.
     * However, such errors can be caught with offline xml validation.
     * Check feasibility
     */
    STD_ASSERT((config_attr = std_config_attr_get(node, "instance")) != NULL);
    instance = atoi(config_attr);
    alias_name = std_config_attr_get(node,"alias");

    if (alias_name == NULL) {
        snprintf(alias, SDI_MAX_NAME_LEN, "%s-%u",entity_name, instance);
    } else {
        strncpy(alias, alias_name, SDI_MAX_NAME_LEN);
    }

    STD_ASSERT((config_attr = std_config_attr_get(node, "type")) != NULL);
    entity_type = sdi_entity_string_to_type(config_attr);

    SDI_TRACEMSG_LOG("\nregistering entity: %s@%d\n", config_attr, instance);
    entity_hdl =  sdi_entity_create(entity_type, instance, alias);
    STD_ASSERT(entity_hdl);

    entity_priv_hdl = (sdi_entity_priv_hdl_t) entity_hdl;
    STD_ASSERT((presence_name = std_config_attr_get(node, "presence")) != NULL);
    if (strncmp(presence_name, SDI_STR_FIXED_SLOT, SDI_FIXED_SLOT_SIZE) != 0) {
           STD_BIT_SET(entity_priv_hdl->oper_support_flag, SDI_HOTSWAPPABLE);
           entity_priv_hdl->pres_pin_hdl = sdi_get_pin_bus_handle_by_name(presence_name);
           STD_ASSERT(entity_priv_hdl->pres_pin_hdl != NULL);
    } else {
        /* if presence attribute is a FIXED_SLOT, consider it as FIXED Entity */
        STD_BIT_CLEAR(entity_priv_hdl->oper_support_flag, SDI_HOTSWAPPABLE);
        entity_priv_hdl->pres_pin_hdl = NULL;
    }

    fault_name = std_config_attr_get(node, "fault");
    if (fault_name != NULL) {
        entity_priv_hdl->fault_status_pin_hdl = sdi_get_pin_bus_handle_by_name(fault_name);
    }

    config_attr = std_config_attr_get(node, "power_output_status");
    if (config_attr != NULL) {
        entity_priv_hdl->power_output_status_pin_hdl =
                         sdi_get_pin_bus_handle_by_name(config_attr);
    }

    sdi_fill_reset_info(node, entity_hdl);
    sdi_entity_register_resources(node, entity_hdl);
    sdi_add_entity(entity_hdl);
}



/**
 * Initializes the internal data structures for the entity and creates entity-db
 *
 * entity_cfg_file[in] - Entity config files which has inforamtion about the devices on
 * each entity
 *
 */
void sdi_register_entities(const char * entity_cfg_file)
{
    std_config_hdl_t cfg_hdl;
    std_config_node_t root, entity;

    STD_ASSERT(entity_cfg_file != NULL);

    cfg_hdl = std_config_load(entity_cfg_file);
    root =  std_config_get_root(cfg_hdl);

    STD_ASSERT(root != NULL);

    std_dll_init(&entity_list);

    for (entity=std_config_get_child(root);(entity != NULL); entity=std_config_next_node(entity))
    {
        SDI_TRACEMSG_LOG("Found entity: %s\n", std_config_name_get(entity));
        sdi_register_entity(entity);
    }

    std_config_unload(cfg_hdl);
}

/**
 * Initialize the specified entity.
 * Upon Initialization, default configurations as specified for platform would
 * be applied
 * param[in] hdl - handle to the entity whose information has to be initialised.
 * return STD_ERR_OK on success and standard error on failure
 */
t_std_error sdi_entity_init(sdi_entity_hdl_t hdl)
{
    uint_t data = 0;
    bool presence = false;
    t_std_error rc = STD_ERR_OK;
    t_std_error ret = STD_ERR_OK;
    std_dll_head *resource_head = NULL;
    sdi_entity_info_t *entity_info = NULL;
    sdi_entity_resource_node_t *node = NULL;
    sdi_entity_priv_hdl_t entity_hdl = NULL;

    STD_ASSERT(hdl != NULL);
    entity_hdl = (sdi_entity_priv_hdl_t)hdl;
    resource_head = (std_dll_head *)entity_hdl->resource_list;

    rc = sdi_entity_presence_get(hdl, &presence);
    if (presence != true) {
        return SDI_ERRCODE(EPERM);
    }

    entity_info = calloc(sizeof(sdi_entity_info_t), 1);
    STD_ASSERT(entity_info != NULL);

    /* Initialise each devices in the entity.
     *   TODO : DO Device init
     */

    if (entity_hdl->entity_info_hdl != NULL) {
        rc = sdi_entity_info_read(entity_hdl->entity_info_hdl, entity_info);
        if (rc == STD_ERR_OK) {
            memcpy(&entity_hdl->entity_info, entity_info, sizeof(sdi_entity_info_t));
        } else {
            SDI_ERRMSG_LOG("entity_info read failed.rc=%d \n", rc);
        }
    }
    /* Initialise each resources in the entity */
    for ((node=(sdi_entity_resource_node_t *)std_dll_getfirst(resource_head));
         (node != NULL);
         (node=(sdi_entity_resource_node_t *)std_dll_getnext(resource_head, (std_dll *)node)))
    {
          /* In case of FAN resource, it has to initialise with max fan speed */
          if (sdi_resource_type_get(node->hdl) == SDI_RESOURCE_FAN) {
              /* Retrieve Max FAN Speed from the FAN eeprom or entity_info */
              if (entity_info != NULL) {
                  data = entity_info->max_speed;
              } else {
                /* TODO: Decide max speed to initialise, in case of read failure */
              }
          }
          ret = sdi_resource_init(node->hdl, &data);
          if (ret != STD_ERR_OK) {
              SDI_ERRMSG_LOG("Resource init failed %s.rc=%d\n",
                             sdi_resource_name_get(node->hdl), ret);
          }
          rc |= ret;
    }

    free(entity_info);
    return rc;
}

/**
 * @TODO: Below two functions are added as a interim solution for PAS
 * compilation.These functions will be removed once the PAS team clean-up
 * their code.
 */

/**
 * Retrieve the handle of first resource of the specified type within the entity.
 * hdl[in] -  handle to the entity whose information has to be retrieved.
 * resource[in] - The type of resource that needs to be looked up.
 * return - if a resource maching the criteria is found, returns handle to it.
 *          else returns NULL.
 */
sdi_resource_hdl_t sdi_entity_get_first_resource(sdi_entity_hdl_t hdl,
                                                 sdi_resource_type_t resource)
{
    return NULL;
}
/**
 * Retrieve the handle of next resource of the specified type within the entity.
 * hdl[in] - handle to the entity whose information has to be retrieved.
 * resource[in] - The type of resource that needs to be looked up.
 * return - if a resource maching the criteria is found, returns handle to it.
 *          else returns NULL.
 */
sdi_resource_hdl_t sdi_entity_get_next_resource(sdi_resource_hdl_t hdl,
                                                sdi_resource_type_t resource)
{
    return NULL;
}

/**
 * Returns the type of resource from resource handler
 */
sdi_resource_type_t sdi_resource_type_get(sdi_resource_hdl_t hdl)
{
    return sdi_internal_resource_type_get(hdl);
}
