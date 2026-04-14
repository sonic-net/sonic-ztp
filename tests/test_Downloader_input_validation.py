'''
Input validation tests for curl command construction in Downloader.py

Tests verify that url, dst_file, and curl_args are handled correctly
when DHCP-supplied values are used.  runCommand is mocked so no real curl
or network is required.
'''

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

from ztp.Downloader import Downloader


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_downloader(**kwargs):
    """Return a Downloader with safe defaults for unit testing."""
    return Downloader(
        is_secure=False,
        timeout=30,
        retry=0,
        incl_http_headers=False,
        **kwargs,
    )


def _capture_cmd(tmp_path, url, **dl_kwargs):
    """
    Call Downloader.getUrl() with a mocked runCommand that records the argv
    list it receives.  Returns the captured cmd list.
    """
    dst = str(tmp_path / "out.txt")
    captured = {}

    def fake_run(cmd, **kwargs):
        captured['cmd'] = list(cmd)
        # Simulate a successful curl: create the output file.
        open(dst, 'w').close()
        return (0, [], [])

    dn = _make_downloader(**dl_kwargs)
    with patch('ztp.Downloader.runCommand', side_effect=fake_run):
        rc, fname = dn.getUrl(url, dst_file=dst)

    return captured.get('cmd', [])


# ---------------------------------------------------------------------------
# URL handling tests
# ---------------------------------------------------------------------------

class TestUrlHandling:
    """Verify that spaces/flags in the URL do not become extra curl arguments."""

    def test_url_with_space_is_single_arg(self, tmp_path):
        """A URL containing a space must not split into multiple curl tokens."""
        url = 'http://example.com/file --output /tmp/evil'
        cmd = _capture_cmd(tmp_path, url)
        # The injected flag must not appear as a standalone token.
        assert '--output' not in cmd
        # The full URL string must appear as one argument (after '--').
        assert url in cmd

    def test_url_with_flag_after_dashdash(self, tmp_path):
        """'--' must appear before the URL so curl treats it as a positional arg."""
        url = 'http://example.com/file'
        cmd = _capture_cmd(tmp_path, url)
        assert '--' in cmd
        dashdash_idx = cmd.index('--')
        url_idx = cmd.index(url)
        assert url_idx == dashdash_idx + 1, "'--' must immediately precede the URL"

    def test_url_with_leading_dash(self, tmp_path):
        """A URL that looks like a flag (leading dash) must be safe.

        The URL string '-o /tmp/evil http://example.com/' must appear as a
        single positional argument after '--', not be split so that '-o'
        injects an extra output path.
        """
        url = '-o /tmp/evil http://example.com/'
        cmd = _capture_cmd(tmp_path, url)
        # '--' must exist and the full URL string must appear after it.
        assert '--' in cmd
        dashdash_idx = cmd.index('--')
        url_idx = cmd.index(url)
        assert url_idx > dashdash_idx, \
            f"URL must appear after '--', but cmd={cmd}"
        # '/tmp/evil' must NOT appear as a standalone token (injected path).
        assert '/tmp/evil' not in cmd, \
            f"Injected path '/tmp/evil' appeared as a standalone token: {cmd}"

    def test_url_with_config_flag(self, tmp_path):
        """'--config' in URL must not reach curl as a real flag."""
        url = 'http://example.com/ --config /tmp/evil.conf'
        cmd = _capture_cmd(tmp_path, url)
        assert '--config' not in cmd[:cmd.index('--')]
        assert url in cmd


# ---------------------------------------------------------------------------
# curl_args handling tests
# ---------------------------------------------------------------------------

class TestCurlArgsHandling:
    """Verify that curl_args is split safely and merged into the argv list."""

    def test_curl_args_legitimate(self, tmp_path):
        """Legitimate curl_args like '--max-time 5' must be forwarded."""
        url = 'http://example.com/file'
        cmd = _capture_cmd(tmp_path, url, curl_args='--max-time 5')
        assert '--max-time' in cmd
        assert '5' in cmd

    def test_curl_args_multiple_flags(self, tmp_path):
        """Multiple legitimate curl_args must all appear."""
        url = 'http://example.com/file'
        cmd = _capture_cmd(tmp_path, url, curl_args='--compressed --max-time 10')
        assert '--compressed' in cmd
        assert '--max-time' in cmd
        assert '10' in cmd

    def test_curl_args_does_not_override_url(self, tmp_path):
        """curl_args must be inserted before '--', not after."""
        url = 'http://example.com/file'
        cmd = _capture_cmd(tmp_path, url, curl_args='--max-time 5')
        dashdash_idx = cmd.index('--')
        url_idx = cmd.index(url)
        # '--' must still immediately precede url
        assert url_idx == dashdash_idx + 1

    def test_cmd_is_list_not_string(self, tmp_path):
        """runCommand must receive a list, never a string."""
        url = 'http://example.com/file'
        dst = str(tmp_path / "out.txt")
        captured = {}

        def fake_run(cmd, **kwargs):
            captured['type'] = type(cmd)
            captured['cmd'] = cmd
            open(dst, 'w').close()
            return (0, [], [])

        dn = _make_downloader()
        with patch('ztp.Downloader.runCommand', side_effect=fake_run):
            dn.getUrl(url, dst_file=dst)

        assert captured['type'] is list, \
            f"runCommand must receive a list, got {captured['type']}"


# ---------------------------------------------------------------------------
# dst_file handling test
# ---------------------------------------------------------------------------

class TestDstFileHandling:
    """Verify that dst_file value is treated as a single path, not shell tokens."""

    def test_dst_file_with_space_is_single_arg(self, tmp_path):
        """dst_file with a space must be passed as one -o argument."""
        # Use a path with a space in the directory name
        spacedir = tmp_path / "my dir"
        spacedir.mkdir()
        dst = str(spacedir / "out.txt")
        url = 'http://example.com/file'
        captured = {}

        def fake_run(cmd, **kwargs):
            captured['cmd'] = list(cmd)
            open(dst, 'w').close()
            return (0, [], [])

        dn = _make_downloader()
        with patch('ztp.Downloader.runCommand', side_effect=fake_run):
            rc, fname = dn.getUrl(url, dst_file=dst)

        cmd = captured.get('cmd', [])
        # '-o' must be followed by the full dst path as one token
        assert '-o' in cmd
        o_idx = cmd.index('-o')
        assert cmd[o_idx + 1] == dst, \
            f"Expected dst as single token after -o, got: {cmd[o_idx+1:]}"
