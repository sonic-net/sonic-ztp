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
 * filename: sdi_register_eeprom_api.h
 */


/******************************************************************************
 * \file sdi_register_eeprom_api.h
 * \brief Header file prvoides register functions for eeprom device driver
 *****************************************************************************/
#ifndef __SDI_REGISTER_EEPROM_API
#define __SDI_REGISTER_EEPROM_API
#include "sdi_eeprom_api.h"

/** get system  eeprom data of a particular area
  * \param[in] code indicates which area of the eeprom data will be read out
  * \param[out] address of the data to be read out
  * \param[in] length of the buffer will be read out
  * \return t_std_error
  */
typedef t_std_error (*sdi_sys_eeprom_data_get_fn_t)(sdi_sys_eeprom_code_t code, uint8_t *buf,
                                                                           size_t len);

/** all eeprom related functions */
typedef struct {
    sdi_sys_eeprom_data_get_fn_t data_get;
} sdi_eeprom_handler_t;

/** register all SYS EEPROM related functions
  * \param[in] handlers list of all functions to be registered
  * \return t_std_error
  */
t_std_error register_eeprom(sdi_eeprom_handler_t *handlers);

/** deregister all EEPROM related functions
  * \return t_std_error
  */
t_std_error deregister_eeprom();

#endif    /* __SDI_REGISTER_EEPROM_API */
