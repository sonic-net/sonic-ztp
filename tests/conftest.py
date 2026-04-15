"""
conftest.py — test environment setup for sonic-ztp unit tests.

Creates temporary directories to replace SONiC-specific system paths
(/host/ztp, /etc/rsyslog.d) so tests can run on a bare host without
a SONiC container.
"""

import os
import sys
import tempfile
import pytest

# ---------------------------------------------------------------------------
# Bootstrap: patch system paths BEFORE any ztp module is imported.
# ZTPCfg.py and Logger.py run module-level code at import time that touches
# /host/ztp and /etc/rsyslog.d, so the patches must be in place first.
# ---------------------------------------------------------------------------

# Create a single persistent temp dir for the whole test session.
_tmp_root = tempfile.mkdtemp(prefix="ztp_test_")
_fake_host_ztp = os.path.join(_tmp_root, "host", "ztp")
_fake_rsyslog_d = os.path.join(_tmp_root, "etc", "rsyslog.d")
_fake_sonic_dir = os.path.join(_tmp_root, "etc", "sonic")

os.makedirs(_fake_host_ztp, exist_ok=True)
os.makedirs(_fake_rsyslog_d, exist_ok=True)
os.makedirs(_fake_sonic_dir, exist_ok=True)

# Add ztp package to path so `from ztp.X import Y` works.
_ztp_pkg_dir = os.path.join(
    os.path.dirname(__file__),
    "..", "src", "usr", "lib", "python3", "dist-packages"
)
if _ztp_pkg_dir not in sys.path:
    sys.path.insert(0, os.path.abspath(_ztp_pkg_dir))

# Patch defaults BEFORE importing any ztp submodule.
import ztp.defaults as _defaults

_defaults.cfg_file = os.path.join(_fake_host_ztp, "ztp_cfg.json")
_defaults.defaultCfg["ztp-cfg-dir"]                    = _fake_host_ztp
_defaults.defaultCfg["ztp-json"]                       = os.path.join(_fake_host_ztp, "ztp_data.json")
_defaults.defaultCfg["ztp-json-shadow"]                = os.path.join(_fake_host_ztp, "ztp_data_shadow.json")
_defaults.defaultCfg["ztp-json-local"]                 = os.path.join(_fake_host_ztp, "ztp_data_local.json")
_defaults.defaultCfg["provisioning-script"]            = os.path.join(_fake_host_ztp, "provisioning-script")
_defaults.defaultCfg["rsyslog-ztp-log-file-conf"]      = os.path.join(_fake_rsyslog_d, "10-ztp-log-file.conf")
_defaults.defaultCfg["rsyslog-ztp-consile-log-file-conf"] = os.path.join(_fake_rsyslog_d, "10-ztp-console-logging.conf")
_defaults.defaultCfg["log-file"]                       = os.path.join(_tmp_root, "ztp.log")
_defaults.defaultCfg["ztp-tmp"]                        = os.path.join(_tmp_root, "tmp")

os.makedirs(_defaults.defaultCfg["ztp-tmp"], exist_ok=True)
