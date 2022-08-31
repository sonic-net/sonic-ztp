#!/bin/bash
###########################################################################
# Copyright 2019 Broadcom. The term "Broadcom" refers to Broadcom Inc.    #
# and/or its subsidiaries.                                                #
#                                                                         #
# Licensed under the Apache License, Version 2.0 (the "License");         #
# you may not use this file except in compliance with the License.        #
# You may obtain a copy of the License at                                 #
#                                                                         #
#   http://www.apache.org/licenses/LICENSE-2.0                            #
#                                                                         #
# Unless required by applicable law or agreed to in writing, software     #
# distributed under the License is distributed on an "AS IS" BASIS,       #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.#
# See the License for the specific language governing permissions and     #
# limitations under the License.                                          #
###########################################################################
# SONiC ZTP configuration setup utility                                   #
#                                                                         #
# This script is used to manage configuration used                        #
# by SONiC ZTP to start DHCP discovery to source                          #
# switch provisioning information.                                        #
#                                                                         #
###########################################################################

# Initalize constants
RETRY_COUNT=24
RETRY_INTERVAL=5
ZTP_LIB_PATH=/usr/lib/ztp/
TMP_ZTP_CONFIG_DB_JSON=/tmp/ztp_config_db.json
CONFIG_DB_JSON=/etc/sonic/config_db.json
ZTP_CONFIG_TEMPLATE=${ZTP_LIB_PATH}/templates/ztp-config.j2
DHCP_POLICY_TEMPLATE=${ZTP_LIB_PATH}/templates/ifupdown2_dhcp_policy.j2
DHCP_POLICY_FILE=/etc/network/ifupdown2/policy.d/ztp_dhcp.json
SYSLOG_CONF_FILE=/etc/rsyslog.d/10-ztp-log-forwarding.conf
SYSLOG_CONSOLE_CONF_FILE=/etc/rsyslog.d/10-ztp-console-logging.conf
CMD=$1
ZTP_ACTIVITY=/var/run/ztp/activity

PLATFORM=`sonic-cfggen -H -v DEVICE_METADATA.localhost.platform`
PRESET=(`head -n 1 /usr/share/sonic/device/$PLATFORM/default_sku`)
HW_KEY=${PRESET[0]}

# Command usage and help
usage()
{
    cat << EOF
 Usage:  ztp-profile.sh < create [destination_file] | install <discovery|resume> | remove [config-fallback] >

         create  - Create ZTP configuration used to initialze switch ports
         install - Create and load ZTP configuration used to initialize switch ports
                   and start DHCP discovery
         remove  - If the switch is running ZTP configuration, reload startup configuration
                   or factory default configuration if startup configuration is missing.
EOF
}

updateActivity()
{
    if [ ! -e ${ZTP_ACTIVITY} ]; then
        mkdir -p $(dirname ${ZTP_ACTIVITY})
    fi
    echo "$(date '+%Y-%m-%d %H:%M:%S %Z' -u) | $1" > ${ZTP_ACTIVITY}
}

# Get ztp profile information for Config DB
get_ztp_profile()
{
    ZTP_PROF_LOADED=$(sonic-db-cli CONFIG_DB HGET "ZTP|mode" "profile")
    INBAND=$(sonic-db-cli CONFIG_DB HGET "ZTP|mode" "inband")
    IPV6=$(sonic-db-cli CONFIG_DB HGET "ZTP|mode" "ipv6")
    IPV4=$(sonic-db-cli CONFIG_DB HGET "ZTP|mode" "ipv4")

    if [ "${ZTP_PROF_LOADED}" = "active" ]; then
        ZTP_STRING="ztp;inband:${INBAND};ipv4:${IPV4};ipv6:${IPV6}"
    else
        ZTP_STRING="no-ztp"
    fi

    echo $ZTP_STRING
}

get_feature()
{
    if ztp features | grep -q "$1" ; then
        echo "true"
    else
        echo "false"
    fi
}

# ztp profile string based on features enabled
get_ztp_feature_string()
{
    echo "ztp;inband:$(get_feature inband);ipv4:$(get_feature ipv4);ipv6:$(get_feature ipv6)"
}

# Create DHCP policy used by ifupdown2
dhcp_policy_create()
{
    # Remove dhclient leases to accommodate usage of link layer address
    # as DUID type while sending out DHCPv6 requests.
    if [ ! -e ${DHCP_POLICY_FILE} ]; then
        rm -f /var/lib/dhcp/dhclient6.*.leases
    fi
    sonic-cfggen -H -k ${HW_KEY} -a "{\"ZTP_INBAND\": \"$(get_feature inband)\", \
            \"ZTP_IPV4\": \"$(get_feature ipv4)\", \"ZTP_IPV6\": \"$(get_feature ipv6)\"}" \
           -p -t ${DHCP_POLICY_TEMPLATE} > ${DHCP_POLICY_FILE}
}

# Create ZTP configuration
ztp_config_create()
{
    DEST_FILE=$1
    if [ "$DEST_FILE" = "" ]; then
        DEST_FILE=${TMP_ZTP_CONFIG_DB_JSON}
    fi

    PRODUCT_NAME=$(decode-syseeprom  -p | tr -dc '[[:print:]]')
    SERIAL_NO=$(decode-syseeprom  -s | tr -dc '[[:print:]]')
    sonic-cfggen -H -k ${HW_KEY} -a "{\"ZTP_INBAND\": \"$(get_feature inband)\", \
             \"ZTP_IPV4\": \"$(get_feature ipv4)\", \"ZTP_IPV6\": \"$(get_feature ipv6)\", \
             \"PRODUCT_NAME\": \"${PRODUCT_NAME}\",  \"SERIAL_NO\": \"${SERIAL_NO}\"}" \
             -p -t ${ZTP_CONFIG_TEMPLATE} > ${DEST_FILE}
    dhcp_policy_create
}

# Create and load requested configuration profile
load_config()
{
    if [ "$1" = "ztp" ]; then
        DEST_FILE=${TMP_ZTP_CONFIG_DB_JSON}
        rm -f ${TMP_ZTP_CONFIG_DB_JSON}
        ztp_config_create ${TMP_ZTP_CONFIG_DB_JSON}
    else
        DEST_FILE=${CONFIG_DB_JSON}
        /usr/bin/config-setup factory ${CONFIG_DB_JSON}
    fi

    if [ -e ${DEST_FILE} ]; then
        config reload ${DEST_FILE} -y -f
        rm -f ${TMP_ZTP_CONFIG_DB_JSON}
        return 0
    else
        echo "Failed to generate and apply ${1} configuration profile."
    fi
    return 1
}

wait_for_system_online()
{
    TRIES=${RETRY_COUNT}
    # Obtain the list of interfaces that may be created after some delay
    HOTPLUG_LIST=$(sonic-db-cli CONFIG_DB KEYS "PORT*" | cut -f2 -d\|)

    while [ ${TRIES} -gt 0 ]
    do
        RETRY=0
        for PORT in ${HOTPLUG_LIST}; do
            if [ ! -d /sys/class/net/${PORT} ]; then
                RETRY=1
                break;
            fi
        done
        [ ${RETRY} -eq 0 ] && break
        sleep ${RETRY_INTERVAL}
        TRIES=`expr $TRIES - 1`
    done

    if [ "${TRIES}" = "0" ]; then
        return 1
    fi
    return 0
}

### Execution starts here ###
CMD="$1"

# Validate input
if [ "$CMD" = "" ]; then
    usage
    exit 1
fi

# Process ZTP profile install request
if [ "$CMD" = "install" ] ; then

    # Detect and create ZTP configuration profile if needed
    FEATURE_STRING=$(get_ztp_feature_string)
    ZTP_DB_PROFILE=$(get_ztp_profile)
    if [ "${FEATURE_STRING}" != "${ZTP_DB_PROFILE}" ]; then
        if [ ! -e ${CONFIG_DB_JSON} ] || [ "$2" = "discovery" ]; then
            # setup rsyslog forwarding
            touch ${SYSLOG_CONF_FILE}
            if [ "$(get_feature console-logging)" = "true" ]; then
                echo ":programname, contains, \"sonic-ztp\"  /dev/console" > ${SYSLOG_CONSOLE_CONF_FILE}
            fi
            systemctl restart rsyslog
            ln -sf /usr/lib/ztp/dhcp/ztp-rsyslog /etc/dhcp/dhclient-exit-hooks.d/ztp-rsyslog
            echo "Installing ZTP configuration profile to initiate ZTP discovery."
            # Install DHCP policy for interfaces participating in ZTP
            dhcp_policy_create
            # create and load ztp configuration
            updateActivity "Installing ZTP configuration profile"
            load_config ztp
        fi
    fi

    # Wait for in-band interfaces to become available
    # Default max wait time is 2 minutes
    updateActivity "Waiting for system online status before continuing ZTP"
    echo "Waiting for system online status before continuing ZTP. (This may take 30--$(expr $RETRY_COUNT \* $RETRY_INTERVAL) seconds)."
    wait_for_system_online
    if [ "$?" != "0" ]; then
        echo "Error: System is not ready. Proceeding with ZTP after waiting for $(expr $RETRY_COUNT \* $RETRY_INTERVAL) seconds."
    else
        echo "System is ready to respond."
    fi

    if [ "$2" = "resume" ] && [ "$(get_ztp_profile)" = "$(get_ztp_feature_string)" ]; then
        # Restart interface configuration again to pickup newly created interfaces
        # to start DHCP discovery
        if [ "$(ztp status -c)" = "4:IN-PROGRESS" ]; then
            echo "Restarting network configuration."
            updateActivity "Restarting network configuration"
            systemctl restart interfaces-config
            echo "Restarted network configuration."
        fi
    fi
fi

# Process ZTP profile remove request
if [ "$CMD" = "remove" ] ; then

    # Remove ZTP configuration profile if it still exists
    if [ "$(get_ztp_profile)" != "no-ztp" ]; then
        # Cleanup locks held by the ZTP session
        rm -rf /var/run/ztp/ztp.lock

        if [ "$2" = "config-fallback" ]; then
            updateActivity "Waiting for system online status before stopping ZTP"
            echo "Waiting for system online status before stopping ZTP. (This may take 30--$(expr $RETRY_COUNT \* $RETRY_INTERVAL) seconds)."
            wait_for_system_online
            if [ "$?" != "0" ]; then
                echo "Error: System is not ready. Proceeding with stopping ZTP after waiting for $(expr $RETRY_COUNT \* $RETRY_INTERVAL) seconds."
            fi

            if [ -e ${CONFIG_DB_JSON} ]; then
                updateActivity "Removing ZTP configuration profile and loading startup configuration"
                echo "Removing ZTP configuration profile. Loading startup configuration."
                config reload ${CONFIG_DB_JSON} -y -f
            else
                updateActivity "Removing ZTP configuration profile and loading factory default configuration"
                echo "Removing ZTP configuration profile. Loading factory default configuration."
                load_config factory
            fi
        else
            # Remove ZTP configuration from config-db
            sonic-db-cli CONFIG_DB DEL "ZTP|mode" > /dev/null
            sonic-db-cli CONFIG_DB DEL "COPP_TRAP|l2dhcp" > /dev/null
        fi

        updateActivity "Restarting network configuration"
        # Restart interface configuration to stop DHCP
        systemctl restart interfaces-config
    fi

    # Remove ZTP DHCP policy
    rm -f ${DHCP_POLICY_FILE}

    # Remove syslog forwarding and console logging configuration
    if [ -f /etc/dhcp/dhclient-exit-hooks.d/ztp-rsyslog ] || \
      [ -f ${SYSLOG_CONF_FILE} ] || \
      [ -f ${SYSLOG_CONSOLE_CONF_FILE} ]; then
        rm -f /etc/dhcp/dhclient-exit-hooks.d/ztp-rsyslog
        rm -f ${SYSLOG_CONF_FILE} ${SYSLOG_CONSOLE_CONF_FILE}
        # Restart rsyslog for syslog config changes to be applied
        systemctl restart rsyslog
    fi
fi

# Create ZTP configuration
if [ "$CMD" = "create" ]; then
    ztp_config_create $2
    # setup console logging of ztp status
    if [ "$(get_feature console-logging)" = "true" ]; then
        echo ":programname, contains, \"sonic-ztp\"  /dev/console" > ${SYSLOG_CONSOLE_CONF_FILE}
    fi
    systemctl restart rsyslog
fi

exit 0
