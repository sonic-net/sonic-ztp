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
 * filename: sdi_register_fan_api.h
 */


/******************************************************************************
 * \file sdi_register_fan_api.h
 * \brief Header file prvoides register functions for fan device driver
 *****************************************************************************/
#ifndef __SDI_REGISTER_API
#define __SDI_REGISTER_API
#include "sdi_fantray_api.h"

/** get total number of fan trays in a L/C
  * \param[out] total number of fan trays
  * \return t_std_error
  */
typedef t_std_error (*sdi_fantray_count_get_fn_t)(uint_t *fantray_count);

/** get total number of fans in a fantray
  * \param[in] id of the individual fan tray
  * \param[out] total number of fans in a fan tray
  * \return t_std_error
  */
typedef t_std_error (*sdi_fantray_fan_count_get_fn_t)(uint_t fantray_id, uint_t *fan_count);

/** get various field of manufacturing info
  * \param[in] id of the individual fan tray
  * \param[in] particular field of the manufacturing info
  * \param[out] buffer contains the information
  * \param[in] length of the buffer
  * \return t_std_error
  */
typedef t_std_error (*sdi_fantray_mfg_info_get_fn_t)(uint_t fantray_id,
                                               sdi_fantray_mfg_code_t code,
                                               uint8_t *buf, size_t len);

/** get fan tray presence info
  * \param[in] id of the individual fan tray
  * \param[out] presence status
  * \return t_std_error
  */
typedef t_std_error (*sdi_fantray_presence_get_fn_t)(uint_t fantray_id,
                                               sdi_fantray_presence_t *status);

/** get fan speed in rpm of a fan tray
  * \param[in] id of the individual fan tray
  * \param[in] id of an individual fan of the fan tray
  * \param[out] speed in RPM
  * \return t_std_error
  */
typedef t_std_error (*sdi_fantray_fan_speed_rpm_get_fn_t)(uint_t fantray_id, uint_t fan_id,
                                               uint_t *speed);

/** set fan speed in rpm of a fan tray
  * \param[in] id of the individual fan tray
  * \param[in] id of an individual fan of the fan tray
  * \param[in] speed in RPM
  * \return t_std_error
  */
typedef t_std_error (*sdi_fantray_fan_speed_rpm_set_fn_t)(uint_t fantray_id, uint_t fan_id,
                                               uint_t speed);

/** set fan speed in percentage of a fan tray
  * \param[in] id of the individual fan tray
  * \param[in] id of an individual fan of the fan tray
  * \param[in] speed in percentage
  * \return t_std_error
  */
typedef t_std_error (*sdi_fantray_fan_speed_percentage_set_fn_t)(uint_t fantray_id,
                                               uint_t fan_id, uint_t percent);

/** get fan speed in percentage of a fan tray
  * \param[in] id of the individual fan tray
  * \param[in] id of an individual fan of the fan tray
  * \param[out] speed in percentage
  * \return t_std_error
  */
typedef t_std_error (*sdi_fantray_fan_speed_percentage_get_fn_t)(uint_t fantray_id,
                                               uint_t fan_id, uint_t *percent);

/** get maximum fan speed of a fan tray
  * \param[in] id of the individual fan tray
  * \param[in] id of an individual fan of the fan tray
  * \param[out] speed in RPM
  * \return t_std_error
  */
typedef t_std_error (*sdi_fantray_fan_max_speed_get_fn_t)(uint_t fantray_id, uint_t fan_id,
                                               uint_t *speed);

/** get status of a fan tray
  * \param[in] id of the individual fan tray
  * \param[out] current status of the fan tray
  * \return t_std_error
  */
typedef t_std_error (*sdi_fantray_status_get_fn_t)(uint_t fantray_id,
                                               sdi_fantray_status_t *status);

/** all fan tray related functions */
typedef struct {
    sdi_fantray_count_get_fn_t fantray_count_get;
    sdi_fantray_fan_count_get_fn_t fan_count_get;
    sdi_fantray_mfg_info_get_fn_t mfg_info_get;
    sdi_fantray_presence_get_fn_t presence_get;
    sdi_fantray_fan_speed_rpm_get_fn_t speed_rpm_get;
    sdi_fantray_fan_speed_rpm_set_fn_t speed_rpm_set;
    sdi_fantray_fan_speed_percentage_set_fn_t speed_percent_set;
    sdi_fantray_fan_speed_percentage_get_fn_t speed_percent_get;
    sdi_fantray_fan_max_speed_get_fn_t max_speed;
    sdi_fantray_status_get_fn_t status;
} sdi_fan_tray_handler_t;

/** register all fan tray related functions
  * \param[in] key type of the fan tray
  * \param[in] handlers list of all functions to be registered
  * \return t_std_error
  */
t_std_error register_fan_tray(char *key, sdi_fan_tray_handler_t *handlers);

/** deregister all fan tray related functions
  * \param[in] key type of the fan tray
  * \return t_std_error
  */
t_std_error deregister_fan_tray(char *key);

#endif    /* __SDI_REGISTER_FAN_API */
