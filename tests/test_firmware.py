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

import sys
import os
import multiprocessing
import json
import socket
import pytest

from .testlib import createPySymlink
from ztp.ZTPLib import runCommand, getCfg

sys.path.append(getCfg('plugins-dir'))
createPySymlink(getCfg('plugins-dir') + '/firmware')
from firmware import Firmware

class TestClass(object):

    '''!
    This class allow to define unit tests for class Firmware
    \endcode
    '''

    def __read_file(self, fname):
        try:
            f = open(fname, 'r')
            return f.read()
        except:
            return None

    def __write_file(self, fname, data):
        try:
            f = open(fname, 'w+')
            f.write(data)
        except Exception as e:
            pass

    def test_download_image_nfound(self, tmpdir):
        '''!
        Test case when "install" option not able to download the image file
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "01-firmware": {
                "halt-on-failure": false,
                "ignore-result": false,
                "install": {
                    "url": {
                        "source": "http://localhost:2000/content/ztp/SONiC.int_odm_hwq_sonic_v201811.0-bc110ac.bin"
                    }
                },
                "plugin": "firmware",
                "reboot-on-failure": false,
                "reboot-on-success": false,
                "status": "BOOT",
                "timestamp": "2019-04-25 00:34:10"
            }
        }
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_download_image_found_but_invalid(self, tmpdir):
        '''!
        Test case when plugin "install" option not able to download the image file
        '''
        content = """
            Foo
        """
        self.__write_file("/tmp/test_firmware.txt", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "01-firmware": {
                "halt-on-failure": false,
                "ignore-result": false,
                "install": {
                    "url": {
                        "source": "file:///tmp/test_firmware.txt"
                    }
                },
                "plugin": "firmware",
                "reboot-on-failure": false,
                "reboot-on-success": false,
                "status": "BOOT",
                "timestamp": "2019-04-25 00:34:10"
            }
        }
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_runCommand(self):
        '''!
        Test the runCommand function
        '''
        with pytest.raises(TypeError):
            (rc, cmd_stdout, cmd_stderr) = runCommand([12])
        (rc, cmd_stdout, cmd_stderr) = runCommand('/abc/xyz/foo')
        assert((rc, cmd_stdout, cmd_stderr) == (1, None, None))
        (rc, cmd_stdout, cmd_stderr) = runCommand('ps FOO')
        assert(rc == 1)
        (rc, cmd_stdout, cmd_stderr) = runCommand('[12]')

    def test_data_input_case1(self, tmpdir):
        ''''!
        Test case of an invalid json data input: json syntax error
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "01-firmware": {
                "install": {
                    "pre-check": {
                        "url": {
                            "destination": "/tmp/firmware_check.sh",
                            "source": "http://localhost:2000/content/ztp/firmware_check.sh"
                        }
                    },
                    "set-default": false,,
                    "set-next-boot": true,
                    "url": {
                        "source": "http://localhost:2000/content/ztp/SONiC.int_odm_hwq_sonic_v201811.0-bc110ac.bin"
                    }
                },
                "plugin": "firmware",
                "reboot-on-failure": false,
                "reboot-on-success": false,
                "status": "BOOT",
                "timestamp": "2019-04-25 19:01:25"
            }
        }
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_data_input_case2(self, tmpdir):
        ''''!
        Test case of an incorrect json data input:
        parameter of wrong type
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "01-firmware": {
                "install": {
                    "set-default": 123,
                    "set-next-boot": true,
                    "url": {
                        "source": "http://localhost:2000/content/ztp/SONiC.int_odm_hwq_sonic_v201811.0-bc110ac.bin"
                    }
                },
                "plugin": "firmware",
                "reboot-on-failure": false,
                "reboot-on-success": false,
                "status": "BOOT",
                "timestamp": "2019-04-25 19:01:25"
            }
        }
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_data_input_case3(self, tmpdir):
        ''''!
        Test case of an incorrect json data input:
        parameter "container-name" needs to be specified
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "01-firmware": {
                "upgrade-docker": {
                    "cleanup-image": false,
                    "enforce-check": true,
                    "url": {
                        "source": "http://localhost:2000/content/ztp/docker-snmp-sv2.gz"
                    }
                },
                "halt-on-failure": false,
                "ignore-result": false,
                "plugin": "firmware",
                "reboot-on-failure": false,
                "reboot-on-success": false,
                "status": "BOOT",
                "timestamp": "2019-04-25 19:34:39"
            }
        }
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_data_input_case4(self, tmpdir):
        ''''!
        Test case of pre-check script returning an error
        Exec format error] encountered while processing the pre-check command
        '''
        content = """
        #!/bin/sh
        exit 1
        """
        self.__write_file("/tmp/test_firmware.txt", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "01-firmware": {
                "install": {
                    "pre-check": {
                        "url": {
                            "source": "file:///tmp/test_firmware.txt",
                            "destination": "/tmp/firmware_check.sh"
                        }
                    },
                    "set-default": false,
                    "set-next-boot": true,
                    "Xurl": {
                        "source": "http://localhost:2001/content/ztp/SONiC.int_odm_hwq_sonic_v201811.0-bc110ac.bin"
                    }
                },
                "plugin": "firmware",
                "reboot-on-failure": false,
                "reboot-on-success": false,
                "status": "BOOT",
                "timestamp": "2019-04-25 19:01:25"
            }
        }
        """)
        firmware = Firmware(str(fh))
        firmware.main()

    def test_data_input_case5(self, tmpdir):
        ''''!
        Test case when the image file does not include neither a URL or a dynamic URL
        '''
        content = """#!/bin/sh
        exit 0
        """
        self.__write_file("/tmp/test_firmware.txt", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "01-firmware": {
                "install": {
                    "pre-check": {
                        "url": {
                            "source": "file:///tmp/test_firmware.txt",
                            "destination": "/tmp/firmware_check.sh"
                        }
                    },
                    "set-default": false,
                    "set-next-boot": true,
                    "Xurl": {
                        "source": "http://localhost:2001/content/ztp/SONiC.int_odm_hwq_sonic_v201811.0-bc110ac.bin"
                    }
                },
                "plugin": "firmware",
                "reboot-on-failure": false,
                "reboot-on-success": false,
                "status": "BOOT",
                "timestamp": "2019-04-25 19:01:25"
            }
        }
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1


    def test_no_section(self, tmpdir):
        ''''!
        Test case when there is no section in the json input data
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
        }
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_no_valid_section(self, tmpdir):
        ''''!
        Test case when there is not a valid section in the json input data
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "01-firmware": {
            }
        }
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_remove_image_nexist(self, tmpdir):
        ''''!
        Test case when the image given with "remove" option does not exist
        '''
        content = """#!/bin/sh
        exit 0
        """
        self.__write_file("/tmp/test_firmware.txt", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
{
    "01-firmware": {
        "remove": {
            "version": "SONiC-OS-int_odm_hwq_sonic_v201811.0-bc110ac",
            "pre-check": {
                "url": {
                    "destination": "/tmp/firmware_check.sh",
                    "source": "file:///tmp/test_firmware.txt"
                }
            }
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "plugin": "firmware",
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-25 21:16:23"
    }
}
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_remove_image_nexist_also_install(self, tmpdir):
        ''''!
        Test when the image given with "remove" option does not exist,
        and there is also an "install" option in the json file
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
{
    "01-firmware": {
        "remove": {
            "Xversion": "SONiC-OS-int_odm_hwq_sonic_v201811.0-bc110ac"
        },
        "install": {
            "url": {
                "source": "/tmp/abc/xyz/foo"
            }
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "plugin": "firmware",
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-25 21:16:23"
    }
}
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_remove_image_nexist_also_install_case2(self, tmpdir):
        ''''!
        Test when the image given with "remove" option does not exist,
        and there is also an "install" option in the json file
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
{
    "01-firmware": {
        "remove": {
            "version": "foo"
        },
        "install": {
            "url": {
                "source": "file:///abc/xyz/foo"
            }
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "plugin": "firmware",
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-25 21:16:23"
    }
}
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_remove_image_with_dynurl(self, tmpdir):
        ''''!
        Test case when the the dynamic URL is provided with invalid argument types
        '''
        content = """#!/bin/sh
        exit 0
        """
        self.__write_file("/tmp/test_firmware.txt", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
{
    "01-firmware": {
        "remove": {
            "version": "SONiC-OS-int_odm_hwq_sonic_v201811.0-bc110ac",
            "pre-check": {
                "dynamic-url": {
                    "source": "file:///tmp/test_firmware.txt"
                }
            }
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "plugin": "firmware",
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-25 21:16:23"
    }
}
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_remove_pre_check_failed(self, tmpdir):
        ''''!
        Test case when the pre-check script is failing on "Remove" action
        '''
        content = """#!/bin/sh
        exit 1
        """
        self.__write_file("/tmp/test_firmware.txt", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
{
    "01-firmware": {
        "remove": {
            "version": "SONiC-OS-int_odm_hwq_sonic_v201811.0-bc110ac",
            "pre-check": {
                "url": {
                    "destination": "/tmp/firmware_check.sh",
                    "source": "file:///tmp/test_firmware.txt"
                }
            }
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "plugin": "firmware",
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-25 21:16:23"
    }
}
        """)
        firmware = Firmware(str(fh))
        firmware.main()

    def test_remove_image_failed(self, tmpdir):
        ''''!
        Test case when removing a SONiC image fail
        '''
        content = """#!/bin/sh
        exit 0
        """
        self.__write_file("/tmp/test_firmware.txt", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
{
    "01-firmware": {
        "remove": {
            "version": "SONiC-OS-int_odm_hwq_sonic_v201811.0-bc110ac"
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "plugin": "firmware",
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-25 21:16:23"
    }
}
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_neither_url_or_dynurl(self, tmpdir):
        ''''!
        Test case when there is neither "url" or "dynamic-url" for a pre-check script
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
{
    "01-firmware": {
        "remove": {
            "version": "SONiC-OS-int_odm_hwq_sonic_v201811.0-bc110ac",
            "pre-check": {
                "abc": {
                    "source": "http://localhost:2000/content/ztp/firmware_check.sh"
                }
            }
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "plugin": "firmware",
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-25 21:16:23"
    }
}
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_remove_no_image_given(self, tmpdir):
        ''''!
        Test case when there is no "image" with "remove" action
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
{
    "01-firmware": {
        "remove": {
            "XXversion": "SONiC-OS-int_odm_hwq_sonic_v201811.0-bc110ac"
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "plugin": "firmware",
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-25 21:16:23"
    }
}
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_install_image_with_dynurl(self, tmpdir):
        ''''!
        Test case to install a new image using a dyamic URL
        '''
        content = """#!/bin/sh
        exit 0
        """
        self.__write_file("/tmp/test_firmware.txt", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
{
    "01-firmware": {
        "halt-on-failure": false,
        "ignore-result": false,
        "install": {
            "pre-check": {
                "dynamic-url" : {
                  "source" : {
                   "prefix" : "file:///tmp/test_firmware.txt",
                   "identifier" : "hostname",
                   "suffix" : ".json"
                  }
                }
            },
            "set-default": false,
            "set-next-boot": true,
            "url": {
                "source": "http://localhost:2000/content/ztp/SONiC.int_odm_hwq_sonic_v201811.0-bc110ac.bin"
            }
        },
        "plugin": "firmware",
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-25 21:36:15"
    }
}
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_install_image_precheck_nfound(self, tmpdir):
        ''''!
        Test case when the pre-check script can not be found
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
{
    "01-firmware": {
        "halt-on-failure": false,
        "ignore-result": false,
        "install": {
            "pre-check": {
                "dynamic-url" : {
                  "source" : {
                   "prefix" : "file:///abc/xyz/foo",
                   "identifier" : "hostname",
                   "suffix" : ".json"
                  }
                }
            },
            "set-default": false,
            "set-next-boot": true,
            "url": {
                "source": "file:///abc/xyz/foo"
            }
        },
        "plugin": "firmware",
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-25 21:36:15"
    }
}
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1


    def test_install_image_dynurl(self, tmpdir):
        ''''!
        Test case when the install SONiC image can not be found using a dynamic URL
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
{
    "01-firmware": {
        "halt-on-failure": false,
        "ignore-result": false,
        "install": {
            "set-default": false,
            "set-next-boot": true,
            "dynamic-url" : {
              "source" : {
               "prefix" : "file:///abc/xyz/foo",
               "identifier" : "hostname",
               "suffix" : ".json"
              }
            }
        },
        "plugin": "firmware",
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-25 21:36:15"
    }
}
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_upgrade_docker_failed(self, tmpdir):
        ''''!
        Test case when the upgrade docker fails
        '''
        content = """#!/bin/sh
        exit 0
        """
        self.__write_file("/tmp/test_firmware.txt", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
{
    "01-firmware": {
          "upgrade-docker": {
            "container-name" : "foo",
            "url": {
              "source": "file:///tmp/test_firmware.txt"
            },
            "cleanup-image": false,
            "enforce-check" : true
          },
        "halt-on-failure": false,
        "ignore-result": false,
        "plugin": "firmware",
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-25 21:16:23"
    }
}
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_upgrade_docker_pre_check_failed(self, tmpdir):
        ''''!
        Test case when the pre-check script is failing on "upgrade-docker" action
        '''
        content = """#!/bin/sh
        exit 1
        """
        self.__write_file("/tmp/test_firmware.txt", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
{
    "01-firmware": {
          "upgrade-docker": {
            "container-name" : "snmp",
            "url": {
              "source": "file:///tmp/test_firmware.txt"
            },
            "pre-check": {
              "url": {
                "source": "file:///tmp/test_firmware.txt",
              }
            },
            "cleanup-image": false,
            "enforce-check" : true
          },
        "halt-on-failure": false,
        "ignore-result": false,
        "plugin": "firmware",
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-25 21:16:23"
    }
}
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def Ztest_upgrade_docker_failed_enforced(self, tmpdir):
        ''''!
        Test case when the 'upgrade'docker' operation is failing with enforcing the check
        '''
        content = """#!/bin/sh
        exit 0
        """
        self.__write_file("/tmp/test_firmware.txt", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
{
    "01-firmware": {
          "upgrade-docker": {
            "container-name" : "snmp",
                "dynamic-url" : {
                  "source" : {
                   "prefix" : "file:///tmp/test_firmware.txt",
                   "identifier" : "hostname",
                   "suffix" : ".json"
                  }
                },
            "cleanup-image": false,
            "enforce-check" : true
          },
        "halt-on-failure": false,
        "ignore-result": false,
        "plugin": "firmware",
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-25 21:16:23"
    }
}
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def Ztest_upgrade_docker_failed_enforced_case2(self, tmpdir):
        ''''!
        Test case when the 'upgrade'docker' operation is failing with enforcing the check
        '''
        content = """#!/bin/sh
        exit 0
        """
        http = HttpServer()
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
{
    "01-firmware": {
          "upgrade-docker": {
            "container-name" : "snmp",
                "dynamic-url" : {
                  "source" : {
                   "prefix" : "http://localhost:2000/ztp/json/ztp_",
                   "identifier" : "hostname",
                   "suffix" : ".json"
                  }
                },
            "cleanup-image": true,
            "enforce-check" : true,
            "tag" : "foo"
          },
        "halt-on-failure": false,
        "ignore-result": false,
        "plugin": "firmware",
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-25 21:16:23"
    }
}
        """)
        http.start(text=content)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1
        http.stop()

    def test_upgrade_docker_pre_check_failed_case2(self, tmpdir):
        ''''!
        Test case when the pre-check script does not include either "url" or "dynamic-url"
        '''
        content = """#!/bin/sh
        exit 0
        """
        self.__write_file("/tmp/test_firmware.txt", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
{
    "01-firmware": {
          "upgrade-docker": {
            "pre-check": {
                "dynamic-url" : {
                  "source" : {
                   "prefix" : "file:///tmp/test_firmware.txt",
                   "identifier" : "hostname",
                   "suffix" : ".json"
                  }
                }
            },
            "container-name" : "snmp",
            "cleanup-image": true,
            "enforce-check" : false
          },
        "halt-on-failure": false,
        "ignore-result": false,
        "plugin": "firmware",
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-25 21:16:23"
    }
}
        """)
        firmware = Firmware(str(fh))
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware.main()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_upgrade_docker_pre_check_failed_case3(self, tmpdir):
        ''''!
        Test case when the pre-check script does not include either "url" or "dynamic-url"
        '''
        content = """#!/bin/sh
        exit 1
        """
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".json", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
{
    "01-firmware": {
          "upgrade-docker": {
            "pre-check": {
                "dynamic-url" : {
                  "source" : {
                   "prefix" : "file:///tmp/test_firmware_",
                   "identifier" : "hostname",
                   "suffix" : ".json"
                  }
                }
            },
            "container-name" : "snmp",
            "cleanup-image": true,
            "enforce-check" : false
          },
        "halt-on-failure": false,
        "ignore-result": false,
        "plugin": "firmware",
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-25 21:16:23"
    }
}
        """)
        firmware = Firmware(str(fh))
        firmware.main()

    def test_binary_version(self, tmpdir):
        ''''!
        Test the functions __which_current_image and __binary_version
        '''
        content = """#!/bin/sh

        exit 0
        """
        self.__write_file("/tmp/test_firmware", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("input.json")
        fh.write("""
        {
            "01-firmware": {
                "halt-on-failure": false,
                "ignore-result": false,
                "install": {
                    "url": {
                        "source": "file:///tmp/test_firmware"
                    }
                },
                "plugin": "firmware",
                "reboot-on-failure": false,
                "reboot-on-success": false,
                "status": "BOOT",
                "timestamp": "2019-04-25 00:34:10"
            }
        }
        """)
        firmware = Firmware(str(fh))
        current_image = firmware._Firmware__which_current_image()
        assert(current_image != '')
        v = firmware._Firmware__binary_version("foo")
        assert(v == '')
        v = firmware._Firmware__binary_version(current_image)
        assert(v == '')
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware._Firmware__set_default_image('Foo')
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

        with pytest.raises(SystemExit) as pytest_wrapped_e:
            firmware._Firmware__set_next_boot_image('Foo')
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1
