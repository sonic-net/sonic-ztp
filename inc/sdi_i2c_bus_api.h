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
 * filename: sdi_i2c_bus_api.h
 */


/******************************************************************************
 * @file sdi_i2c_bus_api.h
 * @brief Defines SDI I2C BUS APIs to execute I2C transactions
 *****************************************************************************/

#ifndef __SDI_I2C_BUS_API_H__
#define __SDI_I2C_BUS_API_H__
#include "std_error_codes.h"
#include "std_type_defs.h"
#include "sdi_i2c.h"

/**
 * @defgroup sdi_internal_i2c_bus_api SDI Internal I2C Bus API
 * @brief SDI I2C Bus API
 * Any I2C Slave device that needs to access its registers via I2C Bus
 * uses the APIs listed in this file.
 *
 * @todo: SMBUS Block transactions and Process Call when required
 *
 * @note on SMBUS Command Format specified in Format: comment before every
 * sdi_smbus* function:
 * All SDI I2C SMBUS APIs format explained below follows these conventions:
 * - Transaction from initiator (can be master of I2C BUS) are denoted in
 * all small letters
 * - Transaction from responder (can be an I2C slave) are denoted in all
 * CAPITAL letters
 * - Size of Every Transaction is marked inside parenthesis
 *
 * @ingroup sdi_internal_bus
 *
 * @{
 */

/**
 * @brief sdi_smbus_recv_byte
 * Execute SMBUS Receive Byte on Slave.
 * Format:
 * <b>
 * start (1) : slave Address (7) : rd (1) : ACK (1) : DATABYTE (8) : ack(1) :
 * stop (1)
 * </b>
 * @param[in] bus_handle : i2c bus handle
 * @param[in] i2c_addr : i2c slave address
 * @param[out] buffer : byte read from slave via i2c
 * @param[in] flags : options if any to be sent @sa sdi_i2c_flags for
 * supported flags
 * @return returns
 * - STD_ERR_OK on success,
 * - SDI_ERRNO on failure.
 */
t_std_error sdi_smbus_recv_byte(sdi_i2c_bus_hdl_t bus_handle,
                                sdi_i2c_addr_t i2c_addr, uint8_t *buffer,
                                uint_t flags);

/**
 * @brief sdi_smbus_send_byte
 * Execute SMBUS Send Byte on Slave.
 * Format:
 * <b>
 * start (1) : slave address (7) : wr (1) : ACK (1) : databyte (8) : ACK(1) :
 * stop (1)
 * </b>
 * @param[in] bus_handle : i2c bus handle
 * @param[in] i2c_addr : i2c slave address
 * @param[in] buffer : byte to be written to slave via i2c
 * @param[in] flags : options if any to be sent @sa sdi_i2c_flags for
 * supported flags
 * @return returns
 * - STD_ERR_OK on success,
 * - SDI_ERRNO on failure.
 */
t_std_error sdi_smbus_send_byte(sdi_i2c_bus_hdl_t bus_handle,
                                sdi_i2c_addr_t i2c_addr, uint8_t buffer,
                                uint_t flags);

/**
 * @brief sdi_smbus_read_byte
 * Execute SMBUS Read Byte on Slave.
 * Format:
 * <b>
 * start (1) : slave address (7) : wr (1) : ACK (1) : cmd (8) : ACK(1) :
 * start (1) : slave address (7) : rd (1) : ACK (1) : DATABYTE (8) : ack(1) :
 * stop (1)
 * </b>
 * @param[in] bus_handle : i2c bus handle
 * @param[in] i2c_addr : i2c slave address
 * @param[in] cmd : address offset
 * @param[out] buffer : byte read from slave via i2c
 * @param[in] flags : options if any to be sent @sa sdi_i2c_flags for
 * supported flags
 * @return returns
 * - STD_ERR_OK on success,
 * - SDI_ERRNO on failure.
 */
t_std_error sdi_smbus_read_byte(sdi_i2c_bus_hdl_t bus_handle,
                                sdi_i2c_addr_t i2c_addr, uint_t cmd,
                                uint8_t *buffer, uint_t flags);

/**
 * @brief sdi_smbus_write_byte
 * Execute SMBUS Write Byte on Slave.
 * Format:
 * <b>
 * start (1) : slave address (7) : wr (1) : ACK (1) : cmd (8) : ACK(1) :
 * databyte (8) : ACK(1) : stop (1)
 * </b>
 * @param[in] bus_handle : i2c bus handle
 * @param[in] i2c_addr : i2c slave address
 * @param[in] cmd : address offset
 * @param[in] buffer : byte to be written to slave via i2c
 * @param[in] flags : options if any to be sent @sa sdi_i2c_flags for
 * supported flags
 * @return returns
 * - STD_ERR_OK on success,
 * - SDI_ERRNO on failure.
 */
t_std_error sdi_smbus_write_byte(sdi_i2c_bus_hdl_t bus_handle,
                                 sdi_i2c_addr_t i2c_addr, uint_t cmd,
                                 uint8_t buffer, uint_t flags);

/**
 * @brief sdi_smbus_read_multi_byte
 * Execute SMBUS Read multiple bytes one after another on Slave.
 * Format:
 * <b>
 * start (1) : slave address (7) : wr (1) : ACK (1) : cmd (8) : ACK(1) :
 * start (1) : slave address (7) : rd (1) : ACK (1) : DATABYTE (8) : ack(1) :
 * stop (1)
 * </b>
 * @param[in] bus_handle : i2c bus handle
 * @param[in] i2c_addr : i2c slave address
 * @param[in] cmd : address offset
 * @param[out] buffer : buffer to read data from slave via i2c.buffer must
 * be capable of holding byt_count number of bytes.
 * @param[in] byte_count : no.of bytes to read
 * @param[in] flags : options if any to be sent @sa sdi_i2c_flags for
 * supported flags
 * @return returns
 * - STD_ERR_OK on success,
 * - SDI_ERRNO on failure.
 */
t_std_error sdi_smbus_read_multi_byte(sdi_i2c_bus_hdl_t bus_handle,
                                sdi_i2c_addr_t i2c_addr, uint_t cmd,
                                uint8_t *buffer, uint_t byte_count, uint_t flags);

/**
 * @brief sdi_smbus_write_multi_byte
 * Execute SMBUS Write multiple bytes one after another on Slave.
 * Format:
 * <b>
 * start (1) : slave address (7) : wr (1) : ACK (1) : cmd (8) : ACK(1) :
 * databyte (8) : ACK(1) : stop (1)
 * </b>
 * @param[in] bus_handle : i2c bus handle
 * @param[in] i2c_addr : i2c slave address
 * @param[in] cmd : address offset
 * @param[in] buffer : data buffer to be written to slave via i2c
 * @param[in] byte_count : no.of bytes to write
 * @param[in] flags : options if any to be sent @sa sdi_i2c_flags for
 * supported flags
 * @return returns
 * - STD_ERR_OK on success,
 * - SDI_ERRNO on failure.
 */
t_std_error sdi_smbus_write_multi_byte(sdi_i2c_bus_hdl_t bus_handle,
                                 sdi_i2c_addr_t i2c_addr, uint_t cmd,
                                 uint8_t *buffer, uint_t byte_count, uint_t flags);

/**
 * @brief sdi_smbus_read_word
 * Execute SMBUS Read Word On Slave.
 * Format:
 * <b>
 * start (1) : slave address (7) : wr (1) : ACK (1) : cmd (8) : ACK(1) :
 * start (1) : slave address (7) : rd (1) : ACK (1) : DATABYTELOW (8) : ack(1) :
 * DATABYTEHIGH (8) : ack (1) : stop (1)
 * </b>
 * @param[in] bus_handle : i2c bus handle
 * @param[in] i2c_addr : i2c slave address
 * @param[in] cmd : address offset
 * @param[out] buffer : word read from slave via i2c
 * @param[in] flags : options if any to be sent @sa sdi_i2c_flags for
 * supported flags
 * @return returns
 * - STD_ERR_OK on success,
 * - SDI_ERRNO on failure.
 */
t_std_error sdi_smbus_read_word(sdi_i2c_bus_hdl_t bus_handle,
                                sdi_i2c_addr_t i2c_addr, uint_t cmd,
                                uint16_t *buffer, uint_t flags);

/**
 * @brief sdi_smbus_write_word
 * Execute SMBUS Write Word on Slave.
 * Format:
 * <b>
 * start (1) : slave address (7) : wr (1) : ACK (1) : cmd (8) : ACK(1) :
 * databytelow (8) : ACK(1) : databytehigh (8) : ACK (1) : stop (1)
 * </b>
 * @param[in] bus_handle : i2c bus handle
 * @param[in] i2c_addr : i2c slave address
 * @param[in] cmd : address offset
 * @param[in] buffer : word to be written to slave via i2c
 * @param[in] flags : options if any to be sent @sa sdi_i2c_flags for
 * supported flags
 * @return returns
 * - STD_ERR_OK on success,
 * - SDI_ERRNO on failure.
 */
t_std_error sdi_smbus_write_word(sdi_i2c_bus_hdl_t bus_handle,
                                 sdi_i2c_addr_t i2c_addr, uint_t cmd,
                                 uint16_t buffer, uint_t flags);

/**
 * @}
 */
#endif /* __SDI_I2C_BUS_API_H__ */
