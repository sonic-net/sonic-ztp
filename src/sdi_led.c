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
 * filename: sdi_led.c
 */


/**************************************************************************************
 *  Implementation of LED resource API.
 ***************************************************************************************/

#include "sdi_led.h"
#include "sdi_led_internal.h"
#include "sdi_resource_internal.h"
#include "sdi_sys_common.h"
#include "std_assert.h"

/**
 * Turn-on the specified LED
 *
 * resource_hdl[in] - Handle of the Resource
 *
 * return t_std_error
 */
t_std_error sdi_led_on (sdi_resource_hdl_t resource_hdl)
{
    t_std_error rc = STD_ERR_OK;
    sdi_resource_priv_hdl_t led_hdl = (sdi_resource_priv_hdl_t)resource_hdl;

    STD_ASSERT(led_hdl != NULL);
    STD_ASSERT(is_sdi_inited());

    if (led_hdl->type != SDI_RESOURCE_LED)
    {
        return(SDI_ERRCODE(EPERM));
    }

    rc = ((sdi_led_sensor_t *)led_hdl->callback_fns)->led_on(led_hdl->callback_hdl);
    if (rc != STD_ERR_OK){
        SDI_ERRMSG_LOG("Failed to turn on the LED sensor device %s\n", led_hdl->name);
    }

    return rc;
}

/**
 * Turn-off the specified LED
 *
 * resource_hdl[in] - Handle of the resource
 *
 * return t_std_error
 */
t_std_error sdi_led_off (sdi_resource_hdl_t resource_hdl)
{
    t_std_error rc = STD_ERR_OK;
    sdi_resource_priv_hdl_t led_hdl = (sdi_resource_priv_hdl_t)resource_hdl;

    STD_ASSERT(led_hdl != NULL);
    STD_ASSERT(is_sdi_inited());

    if (led_hdl->type != SDI_RESOURCE_LED)
    {
        return(SDI_ERRCODE(EPERM));
    }

    rc = ((sdi_led_sensor_t *)led_hdl->callback_fns)->led_off(led_hdl->callback_hdl);
    if (rc != STD_ERR_OK){
        SDI_ERRMSG_LOG("Failed to turn off the LED sensor device %s\n", led_hdl->name);
    }

    return rc;
}

/**
 * Turn-on the digital display LED
 *
 * resource_hdl[in] - Handle of the LED
 *
 * return t_std_error
 */
t_std_error sdi_digital_display_led_on (sdi_resource_hdl_t resource_hdl)
{
    t_std_error rc = STD_ERR_OK;
    sdi_resource_priv_hdl_t led_hdl = (sdi_resource_priv_hdl_t)resource_hdl;

    STD_ASSERT(led_hdl != NULL);

    if (led_hdl->type != SDI_RESOURCE_DIGIT_DISPLAY_LED){
        return(SDI_ERRCODE(EPERM));
    }

    rc = ((sdi_digital_display_led_t *)led_hdl->callback_fns)->digital_display_led_on((led_hdl->callback_hdl));
    if (rc != STD_ERR_OK){
        SDI_ERRMSG_LOG("Failed to trun of %s", led_hdl->name);
    }
    return rc;
}

/**
 * Turn-off the digital display LED
 *
 * resource_hdl[in] - Handle of the LED
 *
 * return t_std_error
 */
t_std_error sdi_digital_display_led_off (sdi_resource_hdl_t resource_hdl)
{
    t_std_error rc = STD_ERR_OK;
    sdi_resource_priv_hdl_t led_hdl = (sdi_resource_priv_hdl_t)resource_hdl;

    STD_ASSERT(led_hdl != NULL);

    if (led_hdl->type != SDI_RESOURCE_DIGIT_DISPLAY_LED){
        return(SDI_ERRCODE(EPERM));
    }

    rc = ((sdi_digital_display_led_t *)led_hdl->callback_fns)->digital_display_led_off((led_hdl->callback_hdl));
    if (rc != STD_ERR_OK){
        SDI_ERRMSG_LOG("Failed to trun of %s", led_hdl->name);
    }
    return rc;
}

/**
 * Sets the specified value in the digital_display_led.
 *
 * hdl[in]           : Handle of the resource
 * display_string[in]: Value to be displayed
 *
 * return t_std_error
 */
t_std_error sdi_digital_display_led_set (sdi_resource_hdl_t hdl, const char *display_string)
{
    t_std_error rc = STD_ERR_OK;
    sdi_resource_priv_hdl_t led_hdl = (sdi_resource_priv_hdl_t)hdl;

    STD_ASSERT(led_hdl != NULL);
    STD_ASSERT(display_string != NULL);

    if (led_hdl->type != SDI_RESOURCE_DIGIT_DISPLAY_LED){
        return(SDI_ERRCODE(EPERM));
    }

    rc = ((sdi_digital_display_led_t *)led_hdl->callback_fns)->digital_display_led_set(led_hdl->callback_hdl,
                                                                                       display_string);
    if (rc != STD_ERR_OK){
        SDI_ERRMSG_LOG("Failed to dispaly %s on LED sensor device %s", display_string, led_hdl->name);
    }
    return rc;
}
