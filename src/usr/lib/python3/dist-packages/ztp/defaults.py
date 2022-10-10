'''
Copyright 2019 Broadcom. The term "Broadcom" refers to Broadcom Inc.
and/or its subsidiaries.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

defaultCfg = dict( \
{
  "acl-url"              : "/var/run/ztp/dhcp_acl_url", \
  "admin-mode"           : True, \
  "config-db-json"       : "/etc/sonic/config_db.json", \
  "curl-retries"         : 3, \
  "curl-timeout"         : 30, \
  "discovery-interval"   : 10, \
  "config-fallback"      : False, \
  "feat-console-logging" : True, \
  "feat-inband" : True, \
  "feat-ipv4" : True, \
  "feat-ipv6" : True, \
  "graph-url"            : "/var/run/ztp/dhcp_graph_url", \
  "halt-on-failure"      : False, \
  "https-secure"         : True, \
  "http-user-agent"      : "SONiC-ZTP/0.1", \
  "ignore-result"        : False, \
  "include-http-headers" : True, \
  "opt59-v6-url"         : "/var/run/ztp/dhcp6_59-ztp_data_url", \
  "opt66-tftp-server"    : "/var/run/ztp/dhcp_66-ztp_tftp_server", \
  "opt67-url"            : "/var/run/ztp/dhcp_67-ztp_data_url", \
  "opt239-url"           : "/var/run/ztp/dhcp_239-provisioning-script_url", \
  "opt239-v6-url"        : "/var/run/ztp/dhcp6_239-provisioning-script_url", \
  "plugins-dir"          : "/usr/lib/ztp/plugins", \
  "provisioning-script"  : "/host/ztp/provisioning-script", \
  "info-feat-console-logging" : "Display ZTP logs over serial console", \
  "info-feat-inband" : "ZTP over In-Band interfaces", \
  "info-feat-ipv4" : "ZTP using IPv4 DHCP discovery", \
  "info-feat-ipv6" : "ZTP using IPv6 DHCPv6 discovery", \
  "log-file"             : "/var/log/ztp.log", \
  "log-level"            : "INFO", \
  "monitor-startup-config" : True, \
  "restart-ztp-interval": 300, \
  "reboot-on-success"    : False, \
  "reboot-on-failure"    : False, \
  "restart-ztp-on-failure" : False, \
  "restart-ztp-on-invalid-data" : True, \
  "restart-ztp-no-config" : True, \
  "rsyslog-ztp-log-file-conf" : '/etc/rsyslog.d/10-ztp-log-file.conf', \
  "rsyslog-ztp-consile-log-file-conf" : '/etc/rsyslog.d/10-ztp-console-logging.conf', \
  "section-input-file"   : "input.json", \
  "sighandler-wait-interval" : 60, \
  "test-mode"            : False, \
  "umask"                : "022", \
  "ztp-activity"         : '/var/run/ztp/activity', \
  "ztp-cfg-dir"          : "/host/ztp", \
  "ztp-json"             : "/host/ztp/ztp_data.json", \
  "ztp-json-shadow"      : "/host/ztp/ztp_data_shadow.json", \
  "ztp-json-local"       : "/host/ztp/ztp_data_local.json", \
  "ztp-json-opt59"       : "/var/run/ztp/ztp_data_opt59.json", \
  "ztp-json-opt67"       : "/var/run/ztp/ztp_data_opt67.json", \
  "ztp-json-version" : "1.0", \
  "ztp-lib-dir"          : "/usr/lib/ztp", \
  "ztp-restart-flag"     : "/tmp/pending_ztp_restart", \
  "ztp-run-dir"          : "/var/run/ztp", \
  "ztp-tmp-persistent"   : "/var/lib/ztp/sections", \
  "ztp-tmp"              : "/var/lib/ztp/tmp" \
})

cfg_file = '/host/ztp/ztp_cfg.json'
