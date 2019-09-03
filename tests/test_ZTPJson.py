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
import socket
import shutil
import json
import pytest

from ztp.ZTPLib import getCfg
from ztp.ZTPSections import ConfigSection,ZTPJson
from ztp.JsonReader import JsonReader

class TestClass(object):

    '''!
    \brief This class allow to define unit tests for class ZTPJson

    Examples of class usage:

    \code
    pytest-2.7 -v -x test_ZTPJson.py
    \endcode
    '''

    def __init_json(self):

        content = """{
    "ztp": {
        "0002-test-plugin": {
           "message" : "0002-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : true,
           "ignore-result" : true,
           "halt-on-failure" : true
        },
        "0003-test-plugin": {
           "plugin" : {
             "name" : "test-plugin"
           },
           "message" : "0003-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : false
        },
        "0001-test-plugin": {
           "plugin" : "test-plugin",
           "message" : "0001-test-plugin",
           "message-file" : "/etc/ztp.results",
           "fail" : false,
           "ignore-result" : true
        }
    }
}"""
        f = open(getCfg('ztp-json'), "w")
        f.write(content)
        f.close()

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

    def test_src_dst_file_invalid(self):
        '''!
        Verify that the instanciation of the object return a dictionary object
        '''
        with pytest.raises(ValueError):
            ztpjson = ZTPJson([12])
        with pytest.raises(ValueError):
            ztpjson = ZTPJson(12)
        with pytest.raises(ValueError):
            ztpjson = ZTPJson([12], [23])
        with pytest.raises(ValueError):
            ztpjson = ZTPJson(12, 34)

        def test_constructor1(self):
            ztpjson = ZTPJson()
            assert(type(ztpjson.objJson) == JsonReader)
            assert(type(ztpjson.jsonDict) == dict)

    def test_load_config_file_nexist(self):
        '''!
        Assuming that the key [ztp-json] in ztp_cfg.json
        exist and is a valid json file, verify that the constructor is loading this file.
        '''
        self.__init_json()
        json_src_file = getCfg('ztp-json')
        shutil.move(json_src_file, json_src_file+'.saved')
        with pytest.raises(ValueError):
            ztpjson = ZTPJson()
        shutil.move(json_src_file+'.saved', json_src_file)

    def test_load_config_file_exist(self):
        '''!
        Assuming that the key [ztp-json] in ztp_cfg.json
        exist and is a valid json file, verify that the constructor is loading this file.
        '''
#        json_src_file = getCfg('ztp-json')
#        with open(json_src_file) as json_file:
#            json_dict = json.load(json_file)
        self.__init_json()
        ztpjson = ZTPJson()
        assert(type(ztpjson.objJson) == JsonReader)
        assert(type(ztpjson.jsonDict) == dict)
#        assert(json_dict == ztpjson.jsonDict)

    def test_constructor(self):
        '''!
        Verify that the instanciation of the object return a dictionary object
        '''
        ztpjson = ZTPJson()
        assert(type(ztpjson.objJson) == JsonReader)
        assert(type(ztpjson.jsonDict) == dict)

    def test_getkey(self):
        '''!
        Verify that the section 'ztp' exist in a valid json configuration file
        '''
        ztpjson = ZTPJson()
        ztpcfg = ConfigSection()
        assert(ztpjson.jsonDict['ztp'] == ztpcfg.jsonDict['ztp'])
        assert(ztpjson['ztp'] == None)
        with pytest.raises(TypeError):
            ztpjson.plugin(None)

    def test_setkey_status(self):
        '''!
        Verify that the status can be changed with a valid value.
        Verify that when trying to change the status with in invalid value, the
        TypeError exception ie being raised.
        '''
        ztpjson = ZTPJson()
        ztpjson['foo'] = 'ok'
        ztpjson['status'] = 'ok'
        assert(ztpjson['status'] == 'ok')
        with pytest.raises(TypeError):
            ztpjson['status'] = 123

    def test_no_ztp_in_json(self, tmpdir):
        '''!
        Test when valid json file, but no 'ztp section in it
        '''
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
                "reboot-on-success": "red"
        }
        """)
        with pytest.raises(ValueError):
            ztpjson = ZTPJson(str(fh))

    def test_ztp_dynamic_url_invalid_arg_type(self, tmpdir):
        '''!
        Test a valid input json file, with a plugin described as a dynamic URL, but with an URL
        instead of a Dynamic URL. Load the plugin.
        Verify that this condition happens:
        "DynamicURL provided with invalid argument types"
        '''
        content = """{
    "ztp": {
        "0001-test-provisioning-script": {
            "halt-on-failure": false,
            "ignore-result": false,
            "plugin": {
                "dynamic-url": {
                    "source": "/tmp/test_firmware_%s.json"
                }
            },
            "reboot-on-failure": false,
            "reboot-on-success": false,
            "status": "BOOT",
            "timestamp": "2019-04-18 19:49:49"
        },
        "config-fallback": false,
        "halt-on-failure": false,
        "ignore-result": false,
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "restart-ztp-no-config": true,
        "restart-ztp-on-failure": false,
        "status": "BOOT",
        "timestamp": "2019-04-18 19:49:49",
        "ztp-json-version": "1.0"
    }
}""" % socket.gethostname()
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".json", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "dynamic-url" : {
              "source" : {
               "prefix" : "file:///tmp/test_firmware_",
               "identifier" : "hostname",
               "suffix" : ".json"
              }
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))
        assert(self.__read_file(str(fh2)) == content)

        content = """
        #!/bin/sh

        echo Hello
        exit 2
"""
        self.__write_file("/tmp/test_firmware.txt", content)
        plugin_name = ztpjson.plugin('0001-test-provisioning-script')
        assert(plugin_name == None)

    def test_ztp_invalid_value_dft_obj(self, tmpdir):
        '''!
        Test when there is an invalid value for a default object ("reboot-on-failure")
        '''
        content = """{
    "ztp": {
        "0001-test-provisioning-script": {
            "halt-on-failure": false,
            "ignore-result": false,
            "plugin": {
                "url": {
                    "source": "http://localhost:2000/ztp/scripts/post_install.sh"
                }
            },
            "reboot-on-failure": 123,
            "reboot-on-success": false,
            "status": "BOOT",
            "timestamp": "2019-04-18 19:49:49"
        },
        "config-fallback": false,
        "halt-on-failure": false,
        "ignore-result": false,
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "restart-ztp-no-config": true,
        "restart-ztp-on-failure": false,
        "status": "BOOT",
        "timestamp": "2019-04-18 19:49:49"
    }
}"""
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".json", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "dynamic-url" : {
              "source" : {
               "prefix" : "file:///tmp/test_firmware_",
               "identifier" : "hostname",
               "suffix" : ".json"
              }
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))
        assert(ztpjson != None)

    def test_ztp_non_existent_plugin_section_name(self, tmpdir):
        '''!
        Test when using a non existent section plugin section name.
        Verify that the plugin name returned is None.
        '''
        content = """{
    "ztp": {
        "0001-test-provisioning-script": {
            "halt-on-failure": false,
            "ignore-result": false,
            "plugin": {
                "url": {
                    "source": "http://localhost:2000/ztp/scripts/post_install.sh"
                }
            },
            "reboot-on-failure": false,
            "reboot-on-success": false,
            "status": "BOOT",
            "timestamp": "2019-04-18 19:49:49"
        },
        "config-fallback": false,
        "halt-on-failure": false,
        "ignore-result": false,
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "restart-ztp-no-config": true,
        "restart-ztp-on-failure": false,
        "status": "BOOT",
        "timestamp": "2019-04-18 19:49:49",
        "ztp-json-version": "1.0"
    }
}"""
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".json", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "dynamic-url" : {
              "source" : {
               "prefix" : "file:///tmp/test_firmware_",
               "identifier" : "hostname",
               "suffix" : ".json"
              }
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))
        assert(self.__read_file(str(fh2)) == content)

        content = """
        #!/bin/sh

        echo Hello
        exit 2
"""
        plugin_name = ztpjson.plugin('XYZ')
        assert(plugin_name == None)

    def test_ztp_suspend_exit_timestamp(self, tmpdir):
        '''!
        Validate suspend-exit code: remove 'suspend-exit' if value is invalid.
        Add timestamp if missing.
        '''
        content = """{
    "ztp": {
        "0001-test-provisioning-script": {
            "halt-on-failure": false,
            "ignore-result": false,
            "plugin": {
                "url": {
                    "source": "http://localhost:2000/ztp/scripts/post_install.sh"
                }
            },
            "suspend-exit-code" : -1,
            "ignore-result" : true
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT"
    }
}"""
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".json", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "dynamic-url" : {
              "source" : {
               "prefix" : "file:///tmp/test_firmware_",
               "identifier" : "hostname",
               "suffix" : ".json"
              }
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))

    def test_ztp_no_ztp_section(self, tmpdir):
        '''!
        Test case ztp section not found in JSON data.
        Verify that exception ValueError is raised.
        '''
        content = """{
    "XXztp": {
        "0001-test-provisioning-script": {
            "halt-on-failure": false,
            "ignore-result": false,
            "plugin": {
                "url": {
                    "source": "http://localhost:2000/ztp/scripts/post_install.sh"
                }
            },
            "suspend-exit-code" : true,
            "ignore-result" : true
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-18 19:49:49"
    }
}"""
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".json", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "dynamic-url" : {
              "source" : {
               "prefix" : "file:///tmp/test_firmware_",
               "identifier" : "hostname",
               "suffix" : ".json"
              }
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        with pytest.raises(ValueError):
            ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))

    def test_ztp_url_reusing_plugin(self, tmpdir):
        '''!
        Test using an URL, and not a dynamic URL.
        Test reusing the same plugin when the plugin return SUSPEND.
        '''
        content = """{
    "ztp": {
        "0001-test-provisioning-script": {
            "halt-on-failure": false,
            "ignore-result": false,
            "plugin": {
                "url": {
                    "source": "file:///tmp/test_firmware.sh"
                }
            },
            "reboot-on-failure": false,
            "reboot-on-success": false,
            "status": "BOOT",
            "timestamp": "2019-04-18 19:49:49"
        },
        "config-fallback": false,
        "halt-on-failure": false,
        "ignore-result": false,
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "restart-ztp-no-config": true,
        "restart-ztp-on-failure": false,
        "status": "BOOT",
        "timestamp": "2019-04-18 19:49:49",
        "ztp-json-version": "1.0"
    }
}"""
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".json", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "dynamic-url" : {
              "source" : {
               "prefix" : "file:///tmp/test_firmware_",
               "identifier" : "hostname",
               "suffix" : ".json"
              }
            }
          }
        }
        """)
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".json", content)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))
        assert(self.__read_file(str(fh2)) == content)

        content = """
        #!/bin/sh

        echo Hello
        exit -1
"""
        self.__write_file("/tmp/test_firmware.sh", content)
        plugin1_name = ztpjson.plugin('0001-test-provisioning-script')
        assert(self.__read_file(plugin1_name) == content)
        plugin2_name = ztpjson.plugin('0001-test-provisioning-script')
        assert(self.__read_file(plugin2_name) == content)

    def test_ztp_url_reusing_plugin_2(self, tmpdir):
        '''!
        Test using an URL, and not a dynamic URL.
        Test reusing the same plugin when the plugin return SUSPEND.
        '''
        content = """{
    "ztp": {
        "0001-test-provisioning-script": {
            "halt-on-failure": false,
            "ignore-result": false,
            "plugin": {
                "url": {
                    "source": "file:///tmp/test_firmware.sh",
                    "destination": "/tmp/firmware_check.sh"
                }
            },
            "reboot-on-failure": false,
            "reboot-on-success": false,
            "status": "BOOT",
            "timestamp": "2019-04-18 19:49:49"
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-18 19:49:49"
    }
}"""
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".json", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "dynamic-url" : {
              "source" : {
               "prefix" : "file:///tmp/test_firmware_",
               "identifier" : "hostname",
               "suffix" : ".json"
              }
            }
          }
        }
        """)
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".sh", content)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))

        content = """
        #!/bin/sh

        echo Hello
        exit -1
"""
        self.__write_file("/tmp/test_firmware.sh", content)
        plugin1_name = ztpjson.plugin('0001-test-provisioning-script')
        assert(self.__read_file(plugin1_name) == content)
        plugin2_name = ztpjson.plugin('0001-test-provisioning-script')
        assert(self.__read_file(plugin2_name) == content)

    def test_ztp_firmware_plugin(self, tmpdir):
        '''!
        Test case with a plugin name such as "firmware".
        Use "firmware" as plugin name, and verify that the script name return is
        "/usr/lib/ztp/plugins/firmware"
        '''
        content = """{
    "ztp": {
        "04-connectivity-tests-2": {
          "plugin": {
            "name": "firmware"
          }
        },
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-18 19:49:49"
    }
}"""
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".json", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "dynamic-url" : {
              "source" : {
               "prefix" : "file:///tmp/test_firmware_",
               "identifier" : "hostname",
               "suffix" : ".json"
              }
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))

        content = """
        #!/bin/sh

        echo Hello
        exit -1
"""
        plugin_name = ztpjson.plugin('04-connectivity-tests-2')

    def test_ztp_invalid_plugin_type(self, tmpdir):
        '''!
        Test when the plugin is neither a URL, Dynamic URL or Name type.
        Verify that the plugin name return is None.
        '''
        content = """{
    "ztp": {
        "04-connectivity-tests-2": {
          "plugin": {
            "nothing": "firmware"
          }
        },
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-18 19:49:49"
    }
}"""
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".json", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "dynamic-url" : {
              "source" : {
               "prefix" : "file:///tmp/test_firmware_",
               "identifier" : "hostname",
               "suffix" : ".json"
              }
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))

        content = """
        #!/bin/sh

        echo Hello
        exit -1
"""
        plugin_name = ztpjson.plugin('04-connectivity-tests-2')
        assert(plugin_name == None)

    def test_ztp_url_could_not_interpreted(self, tmpdir):
        '''!
        Verify that when an URL section is invalid, it shows
        "url/dynamic-url sections provided in ztp section could not be interpreted"
        and the ValueError exception is being raised.
        '''
        content = """{
    "ztp": {
        "0001-test-provisioning-script": {
            "halt-on-failure": false,
            "ignore-result": false,
            "plugin": {
                "url": {
                    "source": "http://localhost:2000/ztp/scripts/post_install.sh"
                }
            },
            "reboot-on-failure": false,
            "reboot-on-success": false,
            "status": "BOOT",
            "timestamp": "2019-04-18 19:49:49"
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": None,
    }
}"""
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".json", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "url" : {
              "source" : {
               "prefix" : "file:///tmp/test_firmware_",
               "identifier" : "hostname",
               "suffix" : ".json"
              }
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        with pytest.raises(ValueError):
            ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))

    def test_ztp_return_invalid_url_section(self, tmpdir):
        '''!
        Verify that when the plugin return an invalid url section a ValueError
        exception is raised.
        '''
        content = """{
  "ztp": {
    "01-firmware": {
      "install": {
        "url": {
          "source": "file:///tmp/test_firmware.json"
        },
        "set-default": true
      }
    },
  }
}"""
        self.__write_file("/tmp/test_firmware.json", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "url" : {
              "source" : "file:///tmp/test_firmware.json"
              }
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        with pytest.raises(ValueError):
            ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))

    def test_ztp_return_another_invalid_url_section(self, tmpdir):
        '''!
        Verify that when the plugin return an invalid url section a ValueError
        exception is raised.
        '''
        content = """{
    "ztp": {
        "0001-test-provisioning-script": {
            "halt-on-failure": false,
            "ignore-result": false,
            "plugin": {
                "url": {
                    "source": "http://localhost:2000/ztp/scripts/post_install.sh"
                }
            },
            "reboot-on-failure": false,
            "reboot-on-success": false,
            "status": "BOOT",
            "timestamp": "2019-04-18 19:49:49"
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": None,
    }
}"""
        self.__write_file("/tmp/test_firmware.json", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "url" : {
              "source" : "file://"
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        with pytest.raises(ValueError):
            ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))

    def test_ztp_dynamic_url_download(self, tmpdir):
        '''!
        Verify that it can download a script provided by a dynamic URL
        '''
        content = """{
    "ztp": {
        "0001-test-provisioning-script": {
            "halt-on-failure": false,
            "ignore-result": false,
            "plugin": {
                "dynamic-url": {
                      "destination": "/tmp/firmware_check.sh",
                      "source" : {
                       "prefix" : "file:///tmp/test_firmware_",
                       "identifier" : "hostname",
                       "suffix" : ".sh"
                      }
                }
            },
            "reboot-on-failure": false,
            "reboot-on-success": false,
            "status": "BOOT",
            "timestamp": "2019-04-18 19:49:49"
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-18 19:49:49"
    }
}"""
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".json", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "dynamic-url" : {
               "source" : {
                 "prefix" : "file:///tmp/test_firmware_",
                 "identifier" : "hostname",
                 "suffix" : ".json"
              }
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))

        content = """
        #!/bin/sh

        echo Hello
        exit 2
"""
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".sh", content)
        plugin_name = ztpjson.plugin('0001-test-provisioning-script')
        assert(plugin_name == '/tmp/firmware_check.sh')

    def test_ztp_dynamic_url_download_2(self, tmpdir):
        '''!
        Verify that it can download a script provided by a dynamic URL
        '''
        content = """{
    "ztp": {
        "0001-test-provisioning-script": {
            "halt-on-failure": false,
            "ignore-result": false,
            "plugin": {
                "dynamic-url": {
                      "source" : {
                       "prefix" : "file:///tmp/test_firmware_post_install_",
                       "identifier" : "hostname",
                       "suffix" : ".sh"
                      }
                }
            },
            "reboot-on-failure": false,
            "reboot-on-success": false,
            "status": "BOOT",
            "timestamp": "2019-04-18 19:49:49"
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-18 19:49:49"
    }
}"""
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".json", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "dynamic-url" : {
               "source" : {
                 "prefix" : "file:///tmp/test_firmware_",
                 "identifier" : "hostname",
                 "suffix" : ".json"
              }
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))

        content = """
        #!/bin/sh

        echo Hello
        exit 2
"""
        self.__write_file("/tmp/test_firmware_post_install_"+socket.gethostname()+".sh", content)
        plugin_name = ztpjson.plugin('0001-test-provisioning-script')
        assert(plugin_name == '/var/lib/ztp/sections/0001-test-provisioning-script/plugin')

    def test_ztp_graphservice_do_not_exist(self, tmpdir):
        '''!
        Test when the plugin is a graphservice and does not exist.
        '''
        content = """{
    "ztp": {
        "0001-test-provisioning-script": {
            "halt-on-failure": false,
            "ignore-result": false,
            "plugin": "graphservice",
            "reboot-on-failure": false,
            "reboot-on-success": false,
            "status": "BOOT",
            "timestamp": "2019-04-18 19:49:49"
        },
        "config-fallback": false,
        "halt-on-failure": false,
        "ignore-result": false,
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "restart-ztp-no-config": true,
        "restart-ztp-on-failure": false,
        "status": "BOOT",
        "timestamp": "2019-04-18 19:49:49",
        "ztp-json-version": "1.0"
    }
}"""
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".json", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "dynamic-url" : {
              "source" : {
               "prefix" : "file:///tmp/test_firmware_",
               "identifier" : "hostname",
               "suffix" : ".json"
              }
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))
        assert(self.__read_file(str(fh2)) == content)

        content = """
        #!/bin/sh

        echo Hello
        exit 2
"""
        plugin_name = ztpjson.plugin('0001-test-provisioning-script')
        assert(plugin_name == getCfg('plugins-dir')+'/graphservice')


    def test_ztp_plugin_data_invalid(self, tmpdir):
        '''!
        Verify that when the plugin data is invalid, the plugin return None
        '''
        content = """{
    "ztp": {
        "0001-test-provisioning-script": {
            "halt-on-failure": false,
            "ignore-result": false,
            "plugin": [12],
            "reboot-on-failure": false,
            "reboot-on-success": false,
            "status": "BOOT",
            "timestamp": "2019-04-18 19:49:49"
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-18 19:49:49"
    }
}"""
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".sh", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "dynamic-url" : {
              "source" : {
               "prefix" : "file:////tmp/test_firmware_",
               "identifier" : "hostname",
               "suffix" : ".sh"
              }
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))

        content = """
        #!/bin/sh

        echo Hello
        exit 2
"""
        plugin_name = ztpjson.plugin('0001-test-provisioning-script')
        assert(plugin_name == None)

    def test_ztp_use_section_name_for_plugin_name_seqnum(self, tmpdir):
        '''!
        Verify that when no plugin data is provided, the script name is derived from the section name.
        Verify that the sequence number in front of the section name is removed.
        '''
        content = """{
    "ztp": {
        "0001-test-provisioning-script": {
            "halt-on-failure": false,
            "ignore-result": false,
            "reboot-on-failure": false,
            "reboot-on-success": false,
            "status": "BOOT",
            "timestamp": "2019-04-18 19:49:49"
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-18 19:49:49"
    }
}"""
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".sh", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "dynamic-url" : {
              "source" : {
               "prefix" : "file:///tmp/test_firmware_",
               "identifier" : "hostname",
               "suffix" : ".sh"
              }
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))

        content = """
        #!/bin/sh

        echo Hello
        exit 2
"""
        self.__write_file("/tmp/test_firmware.json", content)
        os.system('touch '+ getCfg('plugins-dir') + '/' + 'test-provisioning-script')
        plugin_name = ztpjson.plugin('0001-test-provisioning-script')
        os.system('rm -f ' + getCfg('plugins-dir') + '/' + 'test-provisioning-script')
        assert(plugin_name == getCfg('plugins-dir') + '/test-provisioning-script')

    def test_ztp_use_section_name_for_plugin_name(self, tmpdir):
        '''!
        Verify that when no plugin data is provided, the script name is derived from the section name.
        Test case when there is no sequence number in front of the section name.
        '''
        content = """{
    "ztp": {
        "test-provisioning-script": {
            "halt-on-failure": false,
            "ignore-result": false,
            "reboot-on-failure": false,
            "reboot-on-success": false,
            "status": "BOOT",
            "timestamp": "2019-04-18 19:49:49"
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-18 19:49:49"
    }
}"""
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".sh", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "dynamic-url" : {
              "source" : {
               "prefix" : "file:////tmp/test_firmware_",
               "identifier" : "hostname",
               "suffix" : ".sh"
              }
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))

        content = """
        #!/bin/sh

        echo Hello
        exit 2
"""
        os.system('touch ' +  getCfg('plugins-dir') + '/test-provisioning-script')
        plugin_name = ztpjson.plugin('test-provisioning-script')
        os.system('rm -f ' + getCfg('plugins-dir') + '/test-provisioning-script')
        assert(plugin_name == getCfg('plugins-dir') + '/test-provisioning-script')

    def test_ztp_use_section_name_for_plugin_name_notfound(self, tmpdir):
        '''!
        Verify that when no plugin data is provided, the script name is derived from the section name.
        Verify that if plugin does not exist, None is returned.
        '''
        content = """{
    "ztp": {
        "0001-test-provisioning-script": {
            "halt-on-failure": false,
            "ignore-result": false,
            "reboot-on-failure": false,
            "reboot-on-success": false,
            "status": "BOOT",
            "timestamp": "2019-04-18 19:49:49"
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-18 19:49:49"
    }
}"""
        self.__write_file("/tmp/test_firmware_"+socket.gethostname()+".sh", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "dynamic-url" : {
              "source" : {
               "prefix" : "file:////tmp/test_firmware_",
               "identifier" : "hostname",
               "suffix" : ".sh"
              }
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))

        content = """
        #!/bin/sh

        echo Hello
        exit 2
"""
        os.system('touch '+ getCfg('plugins-dir') + '/test-provisioning-script')
        plugin_name = ztpjson.plugin('0001-test-provisioning-script')
        os.system('rm -f ' + getCfg('plugins-dir') + '/test-provisioning-script')
        assert(plugin_name == getCfg('plugins-dir') + '/test-provisioning-script')

    def test_ztp_use_section_name_for_plugin_name(self, tmpdir):
        '''!
        Verify that when no plugin data is provided, the script name is derived from the section name.
        Test case when there is no sequence number in front of the section name.
        '''
        content = """{
    "ztp": {
        "test-provisioning-script": {
            "halt-on-failure": false,
            "ignore-result": false,
            "reboot-on-failure": false,
            "reboot-on-success": false,
            "status": "BOOT",
            "timestamp": "2019-04-18 19:49:49"
        },
        "halt-on-failure": false,
        "ignore-result": false,
        "reboot-on-failure": false,
        "reboot-on-success": false,
        "status": "BOOT",
        "timestamp": "2019-04-18 19:49:49"
    }
}"""
        self.__write_file("/tmp/ztp_"+socket.gethostname()+".json", content)
        d = tmpdir.mkdir("valid")
        fh = d.join("test.json")
        fh.write("""
        {
          "ztp" : {
            "dynamic-url" : {
              "source" : {
               "prefix" : "file:///tmp/ztp_",
               "identifier" : "hostname",
               "suffix" : ".json"
              }
            }
          }
        }
        """)
        d2 = tmpdir.mkdir("dest")
        fh2 = d2.join("dest_file")
        ztpjson = ZTPJson(str(fh), json_dst_file=str(fh2))

        plugin_name = ztpjson.plugin('test-provisioning-script')
        assert(plugin_name == None)
