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

import os
import subprocess
import tempfile
import textwrap

import pytest

SONIC_ZTP_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "src", "usr", "lib", "ztp", "sonic-ztp"
)


class TestSonicZtpWarmBoot:
    """Test that the sonic-ztp wrapper script skips ZTP during warm boot."""

    def _make_test_script(self, tmpdir, warm_boot):
        """Create a test wrapper that overrides /proc/cmdline reading.

        We cannot modify /proc/cmdline in a test environment, so we
        create a wrapper script that:
        1. Overrides 'cat' to return fake /proc/cmdline content
        2. Overrides the ZTP_ENGINE to a no-op (so we don't need the
           real ztp-engine.py or its dependencies)
        3. Sources the start() function from the real sonic-ztp script
        """
        if warm_boot:
            cmdline = "BOOT_IMAGE=/image SONIC_BOOT_TYPE=warm"
        else:
            cmdline = "BOOT_IMAGE=/image"

        test_script = os.path.join(str(tmpdir), "test_sonic_ztp.sh")
        with open(test_script, 'w', newline='\n') as f:
            f.write(textwrap.dedent("""\
                #!/bin/bash
                # Override cat to fake /proc/cmdline
                cat() {{
                    if [ "$1" = "/proc/cmdline" ]; then
                        echo "{cmdline}"
                    else
                        command cat "$@"
                    fi
                }}

                # Override ZTP_ENGINE so we don't need real dependencies
                ZTP_ENGINE="echo ZTP_ENGINE_STARTED"

                # Extract and source just the start() function
                eval "$(sed -n '/^start()/,/^}}/p' {script})"

                start
            """.format(cmdline=cmdline, script=SONIC_ZTP_SCRIPT)))
        os.chmod(test_script, 0o755)
        return test_script

    def test_warm_boot_skips_ztp(self, tmpdir):
        """When SONIC_BOOT_TYPE=warm in cmdline, ZTP should not start."""
        script = self._make_test_script(tmpdir, warm_boot=True)
        result = subprocess.run(
            ["bash", script],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        assert "Warm boot detected" in result.stdout
        assert "ZTP_ENGINE_STARTED" not in result.stdout

    def test_normal_boot_starts_ztp(self, tmpdir):
        """When not warm boot, ZTP engine should be launched."""
        script = self._make_test_script(tmpdir, warm_boot=False)
        result = subprocess.run(
            ["bash", script],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        assert "Warm boot detected" not in result.stdout
        assert "ZTP_ENGINE_STARTED" in result.stdout
