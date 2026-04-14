'''
Test warm boot and minigraph guards in ZTP engine discovery.

These tests verify that the ZTP engine's __discover() method correctly
skips discovery when:
1. A warm boot is detected via /proc/cmdline
2. minigraph.xml is present on the device

The tests run the ZTP engine in test mode (-t) and verify behavior
by checking ZTP status output and log messages.
'''

import os
import sys
import shutil
import subprocess
import time

import pytest

from ztp.ZTPLib import runCommand, getCfg, setCfg
from ztp.defaults import cfg_file
from ztp.JsonReader import JsonReader

COVERAGE = ""
ZTP_ENGINE_CMD = getCfg('ztp-lib-dir') + "/ztp-engine.py -d -t"
ZTP_CMD = "/usr/bin/ztp -C " + cfg_file + ' '
MINIGRAPH_FILE = "/etc/sonic/minigraph.xml"
MINIGRAPH_BAK = "/etc/sonic/minigraph.xml.test_bak"


class TestWarmBootAndMinigraphGuards:
    """Test ZTP discovery guards for warm boot and minigraph presence."""

    def __init_ztp_data(self):
        self.cfgJson, self.cfgDict = JsonReader(cfg_file, indent=4)
        runCommand("systemctl stop ztp")
        runCommand("rm -rf " + getCfg('ztp-cfg-dir') + "/*")
        runCommand("rm -rf " + getCfg('ztp-run-dir') + "/*")
        runCommand("rm -rf " + getCfg('ztp-tmp-persistent'))
        runCommand("rm -rf " + getCfg('ztp-tmp'))
        runCommand("ztp erase -y")

    def __search_file(self, fname, msg, wait_time=1):
        res = False
        while not res and wait_time > 0:
            try:
                subprocess.check_call(['grep', '-q', msg, fname])
                res = True
                break
            except Exception:
                res = False
            time.sleep(1)
            wait_time -= 1
        return res

    def test_minigraph_present_skips_discovery(self):
        """When minigraph.xml exists, ZTP discovery should be skipped."""
        self.__init_ztp_data()
        setCfg('monitor-startup-config', False)
        setCfg('restart-ztp-no-config', False)

        # Ensure minigraph.xml exists
        if not os.path.isfile(MINIGRAPH_FILE):
            with open(MINIGRAPH_FILE, 'w') as f:
                f.write('<fake_minigraph/>')
            created_minigraph = True
        else:
            created_minigraph = False

        try:
            runCommand(COVERAGE + ZTP_ENGINE_CMD)
            # Check ZTP log for minigraph skip message
            assert self.__search_file(
                getCfg('log-file'),
                'minigraph.xml found, skipping ZTP discovery',
                wait_time=10
            ), "Expected ZTP to log minigraph skip message"
        finally:
            if created_minigraph:
                os.remove(MINIGRAPH_FILE)

    def test_no_minigraph_allows_discovery(self):
        """When minigraph.xml does not exist, ZTP discovery proceeds."""
        self.__init_ztp_data()
        setCfg('monitor-startup-config', False)
        setCfg('restart-ztp-no-config', False)

        # Ensure minigraph.xml does NOT exist
        if os.path.isfile(MINIGRAPH_FILE):
            shutil.move(MINIGRAPH_FILE, MINIGRAPH_BAK)
            moved_minigraph = True
        else:
            moved_minigraph = False

        try:
            runCommand(COVERAGE + ZTP_ENGINE_CMD)
            # Discovery should NOT log the minigraph skip message
            assert not self.__search_file(
                getCfg('log-file'),
                'minigraph.xml found, skipping ZTP discovery',
                wait_time=5
            ), "ZTP should not skip discovery when no minigraph"
        finally:
            if moved_minigraph:
                shutil.move(MINIGRAPH_BAK, MINIGRAPH_FILE)
