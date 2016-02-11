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
 * filename: sdi_bus.h
 */


/******************************************************************************
 * @file sdi_bus.h
 * @brief Defines data structures to represent a bus, register and initialize
 * the bus. Bus can be I2C/GPIO/PCI or even virtual bus.
 *****************************************************************************/

#ifndef __SDI_BUS_H___
#define __SDI_BUS_H___

#include "std_error_codes.h"
#include "std_type_defs.h"
#include "std_config_node.h"
#include "std_llist.h"
#include "std_mutex_lock.h"
#include "sdi_sys_common.h"

/**
 * @defgroup sdi_internal_bus SDI Internal Bus
 * @brief Defines the interface to which Bus-Drivers must adhere to for them to be
 * recognized and loaded by the SDI subsystem
 * Every class of bus(I2c, GPIO etc) needs a bus-driver.  Every bus-driver must export an
 * object of type @ref sdi_bus_driver_t so that it can be recognized by SDI;.
 * Examples of bus-drivers include "i2c-mux-drivers" which export pins as individual i2c
 * buses, pin-group that exports a group of pins as group etc.
 *
 * @ingroup sdi_internal
 * @{
 */

/**
 * @enum sdi_bus_type_t
 * Different types of bus supported by SDI
 */
typedef enum {
    /**
     * SDI I2C Bus
     */
    SDI_I2C_BUS,
    /**
     * SDI PIN Bus
     */
    SDI_PIN_BUS,
    /**
     * SDI PIN Group Bus
     */
    SDI_PIN_GROUP_BUS,
    /**
     * SDI PSEUDO Bus
     */
    SDI_PSEUDO_BUS,
    /**
     * SDI MAX Bus.It must be at last
     */
    SDI_MAX_BUS
} sdi_bus_type_t;

/**
 * @typedef sdi_bus_id_t
 * A Unique Identifier for every registered SDI BUS
 */
typedef uint_t sdi_bus_id_t;

/**
 * @typedef sdi_dev_list_t
 * List to add devices attached to bus
 */
typedef struct sdi_dev_list {
    /**
     * @brief head of the dynamic linked list
     */
    std_dll_head head;
    /**
     * @brief lock to syncronize access to dynamic linked list
     */
    std_mutex_type_t lock;
} sdi_dev_list_t;

/**
 * @typedef sdi_bus_t
 * Typedef to sdi bus Data structure @ref sdi_bus
 */
typedef struct sdi_bus sdi_bus_t;

/**
 * @typedef sdi_bus_hdl_t
 * SDI BUS handle, a pointer to SDI Bus object @ref sdi_bus_t
 */
typedef sdi_bus_t *sdi_bus_hdl_t;

/**
 * @struct sdi_bus
 * Data structures to represent a bus
 */
struct sdi_bus {
    /**
     * @brief bus_type
     * SDI BUS TYPE
      */
    sdi_bus_type_t bus_type;
    /**
     * @brief bus id
     * SDI BUS identifier specified during bus creation.
     */
    sdi_bus_id_t bus_id;
    /**
     * @brief bus name
     * SDI Bus Name specified during bus creation.
     */
    char bus_name[SDI_MAX_NAME_LEN];
    /**
     * @brief dev_list
     * Dynamic linked list to add list of devices attached to bus
     */
    sdi_dev_list_t sdi_device_list;
    /**
     * @brief bus_init
     * Initialize the bus based on the configuration parsed as part of
     * registration function
     * Initialize every device attached to the bus
     */
    t_std_error (*bus_init) (sdi_bus_hdl_t bus_hdl);
};

/**
 * @typedef sdi_bus_driver_t
 * SDI BUS Driver Registration and Initialization Function Pointers
 *
 * A bus driver registers and initializes its bus and for every device on the
 * bus invokes device driver's registration and initialization.
 *
 * Every bus must define a data structure of this type with its bus driver name
 * appended with _entry for it to be registered.
 * For ex:
 * sdi_busx_driver_entry = {
 *     .bus_register = busx_register,
 *     .bus_init = busx_init
 * };
 */
typedef struct sdi_bus_driver {
    /**
     * @brief bus_register
     * Parse configuration and convert it to bus data structure
     * Registers the bus
     * On successful registration populates registered bus handle in bus_hdl
     * Registers every device attached to the bus
     */
    t_std_error (*bus_register) (std_config_node_t node, sdi_bus_hdl_t *bus_hdl);
    /**
     * @brief bus_init
     * Initialize the bus based on the configuration parsed as part of
     * registration function
     * Initialize every device attached to the bus
     */
    t_std_error (*bus_init) (sdi_bus_t *bus);
} sdi_bus_driver_t;

/**
 * @}
 */
#endif /* __SDI_BUS_H___ */
