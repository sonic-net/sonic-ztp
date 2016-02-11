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
 * filename: sdi_bus_api.h
 */


/******************************************************************************
 * @file sdi_bus_api.h
 * @brief Defines SDI BUS Read/Write APIs
 * @note: Only byte read/byte write for I2C Bus is implemented.
 * @todo: When the need arises, Add support for word/4byte and support for other
 * buses.
 *****************************************************************************/

#ifndef __SDI_BUS_API_H__
#define __SDI_BUS_API_H__

#include "std_error_codes.h"
#include "std_type_defs.h"
#include "sdi_bus.h"
#include "sdi_driver_internal.h"

/**
 * @defgroup sdi_bus_api SDI Bus Read/Write API
 * @brief SDI BUS API
 * Implements generic bus read and write APIs. Abstracts the type of bus. Helps
 * when Device driver doesn't need to be aware of the type of bus to which it is
 * attached to.
 *
 * @ingroup sdi_internal_bus
 *
 * @{
 */

/**
 * @brief sdi_bus_read_byte
 * Read a byte of data from a specified offset of a device using bus api.
 * @param[in] bus_hdl - Bus handle on which device data to be read is attached.
 * @param[in] addr - Device address
 * @param[in] offset - Offset within device
 * @param[out] buffer - Data read from device is populated in this buffer.
 * @return STD_ERR_OK on success, SDI_ERRCODE(ENOTSUP) if unsupported or
 * STD failure code on error.
 */
t_std_error sdi_bus_read_byte(sdi_bus_hdl_t bus_hdl, sdi_device_addr_t addr,
                              uint_t offset, uint8_t *buffer);

/**
 * @brief sdi_bus_write_byte
 * Write a byte of data to a specified offset of a device using bus api.
 * @param[in] bus_hdl - Bus handle on which device data to be written is attached.
 * @param[in] addr - Device address
 * @param[in] offset - Offset within device
 * @param[in] buffer - Data to be written to device offset address
 * @return STD_ERR_OK on success, SDI_ERRCODE(ENOTSUP) if unsupported or
 * STD failure code on error.
 */
t_std_error sdi_bus_write_byte(sdi_bus_hdl_t bus_hdl, sdi_device_addr_t addr,
                               uint_t offset, uint8_t buffer);


/**
 * @}
 */

#endif /* __SDI_BUS_API_H__ */
