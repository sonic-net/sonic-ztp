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
 * filename: sdi_i2c.h
 */


/******************************************************************************
 * @file sdi_i2c.h
 * @brief Defines SDI I2C Bus Data Structures and I2C Bus operator functions
 *****************************************************************************/

#ifndef __SDI_I2C_H___
#define __SDI_I2C_H___
#include "std_error_codes.h"
#include "std_type_defs.h"
#include "sdi_bus.h"
#include "sdi_bus_framework.h"
#include "event_log.h"

/**
 * @defgroup sdi_internal_i2c_bus_data_types SDI Internal I2C Bus Data Types
 *
 * @brief SDI I2C Bus Data structures and I2C Bus Operator functions
 * Every I2C Bus Device driver creates i2c bus handle for each of its bus
 * instance. Bus handle specifies I2C (includes SMBUS as it's a sub-set of I2C)
 * bus operations like executing i2c(smbus) transaction, locking the bus before
 * executing the transaction, releasing the bus after executing the transaction,
 * querying the capabile supported i2c operations exported by i2c bus.
 * I2c bus handle encapsulates @ref sdi_bus_t to allow identification of bus.
 *
 * @todo
 *  - Add support for un-implemented SMBUS operations when need arises.
 *      Ex: BLOCK Transfer, PEC, 10BIT I2C Address, Process Call
 *  - Add support for I2C bus operations when need arises.
 *  - Reduce the number of arguments of sdi_smbus_execute by creating a
 *      structure and directly passing pointer to the structure object
 *
 * @ingroup sdi_internal_bus
 *
 * @{
 */

/**
 * @def SDI_I2C_FUNC_I2C
 * Code to detect i2c bus supports I2C Functionality
 */
#define SDI_I2C_FUNC_I2C                    0x00000001
/**
 * @def SDI_I2C_FUNC_SMBUS_READ_BYTE
 * Code to detect i2c bus supports SMBUS READ BYTE transaction
 */
#define SDI_I2C_FUNC_SMBUS_READ_BYTE        0x00020000
/**
 * @def SDI_I2C_FUNC_SMBUS_WRITE_BYTE
 * Code to detect i2c bus supports SMBUS WRITE BYTE transaction
 */
#define SDI_I2C_FUNC_SMBUS_WRITE_BYTE       0x00040000
/**
 * @def SDI_I2C_FUNC_SMBUS_READ_BYTE_DATA
 * Code to detect i2c bus supports SMBUS READ BYTE DATA transaction
 */
#define SDI_I2C_FUNC_SMBUS_READ_BYTE_DATA   0x00080000
/**
 * @def SDI_I2C_FUNC_SMBUS_WRITE_BYTE_DATA
 * Code to detect i2c bus supports SMBUS WRITE BYTE DATA transaction
 */
#define SDI_I2C_FUNC_SMBUS_WRITE_BYTE_DATA  0x00100000
/**
 * @def SDI_I2C_FUNC_SMBUS_READ_WORD_DATA
 * Code to detect i2c bus supports SMBUS READ WORD DATA transaction
 */
#define SDI_I2C_FUNC_SMBUS_READ_WORD_DATA   0x00200000
/**
 * @def SDI_I2C_FUNC_SMBUS_WRITE_WORD_DATA
 * Code to detect i2c bus supports SMBUS WRITE WORD DATA transaction
 */
#define SDI_I2C_FUNC_SMBUS_WRITE_WORD_DATA  0x00400000
/**
 * @def SDI_I2C_FUNC_SMBUS_BYTE
 * Code to detect i2c bus supports I2C BYTE transactions
 */
#define SDI_I2C_FUNC_SMBUS_BYTE (SDI_I2C_FUNC_SMBUS_READ_BYTE | \
                             SDI_I2C_FUNC_SMBUS_WRITE_BYTE)
/**
 * @def SDI_I2C_FUNC_SMBUS_BYTE_DATA
 * Code to detect i2c bus supports I2C BYTE DATA transactions
 */
#define SDI_I2C_FUNC_SMBUS_BYTE_DATA (SDI_I2C_FUNC_SMBUS_READ_BYTE_DATA | \
                                  SDI_I2C_FUNC_SMBUS_WRITE_BYTE_DATA)
/**
 * @def SDI_I2C_FUNC_SMBUS_WORD_DATA
 * Code to detect i2c bus supports I2C WORD DATA transactions
 */
#define SDI_I2C_FUNC_SMBUS_WORD_DATA (SDI_I2C_FUNC_SMBUS_READ_WORD_DATA | \
                                  SDI_I2C_FUNC_SMBUS_WRITE_WORD_DATA)

/**
 * @def SDI_MAX_BYTE_VAL Max value of a Byte
 */
#define SDI_MAX_BYTE_VAL                0xFF

/**
 * @def SDI_MAX_WORD_VAL Max value of a Word
 */
#define SDI_MAX_WORD_VAL               0xFFFF

/**
 * @def SDI_SMBUS_SIZE_NON_BLOCK
 * Default Size of Smbus transaction for non block transaction
 */
#define SDI_SMBUS_SIZE_NON_BLOCK        0

/**
 * @def SDI_SMBUS_OFFSET_NON_CMD
 * Default Command offset of SMBUS Commands for which Command Offset is not
 * applicable (SMBUS Recv/Send Byte)
 */
#define SDI_SMBUS_OFFSET_NON_CMD        0

/**
 * @defgroup sdi_i2c_flags SDI I2C Flag I2C Flag, for ex: SMBUS PEC support
 * @{
 */
/**
 *  @def SDI_I2C_FLAG_PEC
 *  Flag to indicate the SMBus PEC support
 */
#define SDI_I2C_FLAG_PEC                 0x00000002

/**
 *  @def SDI_I2C_FLAG_NONE
 *  Macro to indicate no flag
 */
#define SDI_I2C_FLAG_NONE                 0x0
/**
 * @}
 */

/**
 * @enum sdi_smbus_operation_t
 * SDI I2C Bus Read/Write Operation
 */
typedef enum {
    /**
     * SDI I2C SMBUS WRITE
     */
    SDI_SMBUS_WRITE,
    /**
     * SDI I2C SMBUS READ
     */
    SDI_SMBUS_READ,
} sdi_smbus_operation_t;

/**
 * @enum sdi_smbus_data_type_t
 * SDI I2C SMBUS Data Size involved in SMBUS Transaction
 */
typedef enum {
    /**
     * SDI I2C SMBUS BYTE
     */
    SDI_SMBUS_BYTE,
    /**
     * SDI I2C SMBUS BYTE DATA
     */
    SDI_SMBUS_BYTE_DATA,
    /**
     * SDI I2C SMBUS WORD DATA
     */
    SDI_SMBUS_WORD_DATA,
    /**
     * SDI I2C SMBUS BLOCK DATA
     */
    SDI_SMBUS_BLOCK_DATA,
} sdi_smbus_data_type_t;

/**
 * @typedef sdi_i2c_addr_t
 * SDI I2C Device Address
 */
typedef uint16_t sdi_i2c_addr_t;

/**
 * @typedef sdi_i2c_bus_id_t
 * SDI I2C Bus Identifier Type
 */
typedef sdi_bus_id_t sdi_i2c_bus_id_t;

/**
 * @typedef sdi_i2c_bus_t
 * SDI I2C Bus Data Structure
 */
typedef struct sdi_i2c_bus sdi_i2c_bus_t;

/**
  * @typedef sdi_i2c_bus_hdl_t
  * SDI I2C Bus Handle
  */
typedef sdi_i2c_bus_t *sdi_i2c_bus_hdl_t;

/**
 * @typdef sdi_i2c_bus_capability_t
 * Operations supported by the I2C bus
 */
typedef unsigned long sdi_i2c_bus_capability_t;

/**
 * @struct sdi_i2c_bus_ops
 * SDI I2C Bus Operations defined by every I2C Bus Registered
 */
typedef struct sdi_i2c_bus_ops {
    /**
     * @brief sdi_i2c_acquire_bus
     * Acquire I2C Bus
     * Acquire operation should lock the bus for I2C transaction.
     */
    t_std_error (*sdi_i2c_acquire_bus) (sdi_i2c_bus_hdl_t bus);
    /**
     * @brief sdi_smbus_execute
     * Execute SMBUS Transaction
     * Execute SMBUS Transaction on
     * - bus : SMBus
     * - address : Slave Address
     * - operation : Read/Write Operation
     * - data_type : SMBUS Transaction Data Type (like BYTE, WORD, BLOCK )
     * - commandbuf : specify read/write offset,
     * - buffer : Data to read from/write to of I2C Slave
     * - block_len : Length of block data read from/written to I2C Slave
     *    only for SDI_SMBUS_BLOCK_* SMBUS Commands. Though BLOCK transfer is not
     *  supported now, block_len is added in order to avoid changing the
     *  signature of api when its supported later
     * - flags : Could be used to specify PEC and for other purpose
     *                    if required in future
     */
    t_std_error (*sdi_smbus_execute) (sdi_i2c_bus_hdl_t bus, sdi_i2c_addr_t address,
        sdi_smbus_operation_t operation, sdi_smbus_data_type_t data_type,
        uint_t commandbuf, void *buffer,
        size_t *block_len, uint_t flags);
    /**
     * @brief sdi_i2c_release_bus
     * Release I2C Bus
     * Release operation unlocks the bus for further I2C transaction
     */
    void (*sdi_i2c_release_bus) (sdi_i2c_bus_hdl_t bus);
    /**
     * @brief sdi_i2c_get_capability
     * Get supported Functionality
     * Get the list of supported Transactions (like I2C or SMBUS, if SMBUS:
     * list of supported SMBUS transactions Command, Byte, Word, Block, etc,
     * support for 10Bit I2C Slave Address)
     * For ex: if capability  & SDI_I2C_FUNC_I2C is true, i2c bus supports I2C
     * Functionality
     */
     void (*sdi_i2c_get_capability) (sdi_i2c_bus_hdl_t bus,
        sdi_i2c_bus_capability_t *capability);
} sdi_i2c_bus_ops_t;

/**
 * @struct sdi_i2c_bus
 * SDI I2C Bus Structure Registered by every I2C Bus
 */
typedef struct sdi_i2c_bus {
    /**
     * @brief bus
     * SDI BUS Object
     */
    sdi_bus_t bus;
    /**
     * @brief ops
     * SDI I2C Bus Operations to acquire, release bus and execute transactions
     */
    sdi_i2c_bus_ops_t *ops;
} sdi_i2c_bus_t;

/**
 * @brief sdi_i2c_acquire_bus
 * Wrapper for i2c acquire bus sdi_i2c_acquire_bus
 * @param[in] bus_handle - i2c bus handle
 * @return STD_ERR_OK on success
 */
static inline t_std_error sdi_i2c_acquire_bus(sdi_i2c_bus_hdl_t bus_handle)
{
    return bus_handle->ops->sdi_i2c_acquire_bus(bus_handle);
}

/**
 * @brief sdi_smbus_execute
 * Wrapper for smbus execute bus sdi_smbus_execute
 * @param[in] bus_handle - i2c bus handle
 * @param[in] address - i2c slave address
 * @param[in] operation - read/write operation
 * @param[in] data_type - one of send/recv command, byte, word, block
 * @param[out] commandbuf - offset read from/written to slave
 * @param[out] buffer - data read from/written to slave
 * @param[out] block_len - length of block data read from/writtne to slave
 * @param[in] flags - options if any to be send to i2c execute
 * @return STD_ERR_OK on Success, SDI_I2C_ERRNO on Failure
 */
static inline t_std_error sdi_smbus_execute (sdi_i2c_bus_hdl_t bus_handle,
                         sdi_i2c_addr_t address,
                         sdi_smbus_operation_t operation,
                         sdi_smbus_data_type_t data_type,
                         uint_t commandbuf,
                         void *buffer,
                         size_t *block_len,
                         uint_t flags)
{
    return bus_handle->ops->sdi_smbus_execute(bus_handle, address, operation,
        data_type, commandbuf, buffer, block_len, flags);
}

/**
 * @brief sdi_i2c_release_bus
 * Wrapper for i2c release bus sdi_i2c_release_bus
 * @param[in] bus_handle - i2c bus handle
 * @return NONE
 */
static inline void sdi_i2c_release_bus(sdi_i2c_bus_hdl_t bus_handle)
{
    bus_handle->ops->sdi_i2c_release_bus(bus_handle);
}

/**
 * @brief sdi_i2c_bus_get_capability
 * Wrapper for i2c bus sdi_i2c_bus_get_capability
 * @param[in] bus_handle i2c bus handle
 * @param[out] capability functionality supported by this i2c bus
 * @return none
 */
static inline void sdi_i2c_bus_get_capability
    (sdi_i2c_bus_hdl_t bus_handle, sdi_i2c_bus_capability_t *capability)
{
    bus_handle->ops->sdi_i2c_get_capability(bus_handle, capability);
}
/**
 * @}
 */
#endif /* __SDI_I2C_H___ */
