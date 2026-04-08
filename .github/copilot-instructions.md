# Copilot Instructions for sonic-ztp

## Project Overview

sonic-ztp (Zero Touch Provisioning) enables SONiC switches to be automatically configured when they boot for the first time on a network. It discovers provisioning data via DHCP options, downloads configuration files and firmware from remote servers, and applies them without manual intervention. ZTP supports multiple provisioning plugins including config-db JSON loading, firmware installation, SNMP configuration, and connectivity checks.

## Architecture

```
sonic-ztp/
├── src/                          # Source code root
│   ├── usr/
│   │   ├── lib/
│   │   │   ├── ztp/              # Core ZTP engine and utilities
│   │   │   │   ├── ztp-engine.py          # Main ZTP orchestration engine
│   │   │   │   ├── ztp-profile.sh         # ZTP profile shell script
│   │   │   │   ├── sonic-ztp              # ZTP service entry point
│   │   │   │   ├── templates/             # Configuration templates
│   │   │   │   ├── dhcp/                  # DHCP hook scripts
│   │   │   │   └── plugins/              # Provisioning plugins
│   │   │   │       ├── configdb-json      # Apply config_db.json
│   │   │   │       ├── firmware           # Install firmware/images
│   │   │   │       ├── snmp               # Configure SNMP
│   │   │   │       ├── connectivity-check # Verify network connectivity
│   │   │   │       ├── download           # Generic file downloader
│   │   │   │       ├── graphservice       # Microsoft Graph service
│   │   │   │       └── test-plugin        # Example/test plugin
│   │   │   └── python3/
│   │   │       └── dist-packages/
│   │   │           └── ztp/              # ZTP Python library
│   │   └── bin/                  # CLI tools (ztp command)
│   └── etc/                      # System configuration files
├── tests/                        # Unit and integration tests
│   ├── test_ZTPJson.py           # ZTP JSON parsing tests
│   ├── test_ZTPCfg.py            # ZTP configuration tests
│   ├── test_ZTPLib.py            # ZTP library tests
│   ├── test_ztp_engine.py        # Engine integration tests
│   ├── test_Downloader.py        # Download functionality tests
│   ├── test_DynamicURL.py        # Dynamic URL resolution tests
│   ├── test_ConfigSection.py     # Config section tests
│   ├── test_Identifier.py        # Device identifier tests
│   ├── test_Logger.py            # Logging tests
│   ├── test_URL.py               # URL handling tests
│   ├── test_JsonReader.py        # JSON reader tests
│   ├── test_configdb-json.py     # configdb-json plugin tests
│   ├── test_connectivity-check.py # Connectivity check tests
│   ├── test_firmware.py          # Firmware plugin tests
│   ├── test_snmp.py              # SNMP plugin tests
│   ├── test_DecodeSysEeprom.py   # System EEPROM tests
│   └── testlib.py                # Shared test utilities
├── doc/                          # Documentation
│   ├── sonic-ztp.md              # ZTP documentation
│   └── Doxyfile                  # Doxygen configuration
├── debian/                       # Debian packaging
├── Makefile                      # Build orchestration
└── .github/                      # CI workflows
```

### Key Concepts
- **ZTP engine**: Python-based orchestrator that reads a ZTP JSON profile and executes provisioning sections in order
- **Plugins**: Modular provisioning tasks (config-db, firmware, SNMP, etc.) — each is a standalone executable
- **DHCP discovery**: ZTP data URL is obtained via DHCP options (Option 67 / Option 239)
- **ZTP JSON**: A JSON profile that defines provisioning sections, each mapped to a plugin
- **Provisioning lifecycle**: DHCP → Download ZTP JSON → Execute plugins sequentially → Mark complete

## Language & Style

- **Primary language**: Python 3
- **Secondary**: Shell/Bash (DHCP hooks, profile scripts, plugins)
- **Python conventions**:
  - PEP 8 compliant
  - 4 spaces indentation
  - Classes: `PascalCase` (e.g., `ZTPJson`, `ConfigSection`)
  - Functions/methods: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
- **Shell conventions**:
  - Use `#!/bin/bash` shebang
  - Quote variables properly
  - Use `set -e` for error handling where appropriate
- **Plugin convention**: Each plugin is an executable file in `plugins/` — can be Python or shell

## Build Instructions

```bash
# Build Debian package
dpkg-buildpackage -us -uc -b

# Or using make
make

# Install locally (for development)
sudo cp -r src/usr/lib/ztp /usr/lib/
sudo cp -r src/usr/lib/python3/dist-packages/ztp /usr/lib/python3/dist-packages/
sudo cp src/usr/bin/* /usr/bin/

# The package installs:
#   - ZTP engine and plugins to /usr/lib/ztp/
#   - ZTP Python library to python3 dist-packages
#   - ztp CLI command to /usr/bin/
#   - DHCP hooks and systemd service files
```

## Testing

```bash
# Run all tests
cd tests
python3 -m pytest -v

# Run specific test modules
python3 -m pytest test_ZTPJson.py -v
python3 -m pytest test_ztp_engine.py -v
python3 -m pytest test_configdb-json.py -v

# Run tests with coverage
python3 -m pytest --cov=ztp -v

# Tests use testlib.py for shared fixtures and utilities
```

### Test Structure
- Each major component has a corresponding `test_*.py` file
- Plugin tests verify plugin execution behavior
- Library tests cover URL handling, JSON parsing, configuration, etc.
- Tests may mock DHCP, network, and SONiC system dependencies

## PR Guidelines

- **Signed-off-by**: REQUIRED on all commits (`git commit -s`)
- **CLA**: Sign the Linux Foundation EasyCLA
- **Single commit per PR**: Squash commits before merge
- **Plugin changes**: Include plugin script and corresponding test
- **Reference**: Link to [SONiC ZTP HLD](https://github.com/Azure/SONiC/blob/master/doc/ztp/ztp.md) for design context
- **Test coverage**: New features and plugins must have test coverage

## Dependencies

- **sonic-py-swsssdk**: SONiC Python SDK for CONFIG_DB access
- **sonic-utilities**: SONiC CLI utilities (used by some plugins)
- **sonic-installer**: Firmware installation (used by firmware plugin)
- **curl / wget**: HTTP downloads for provisioning data
- **DHCP client**: ISC DHCP client with hook scripts
- **Jinja2**: Template rendering for configuration files
- **systemd**: Service management for ZTP daemon

## Gotchas

- **DHCP hook timing**: ZTP DHCP hooks must execute at the right phase of the DHCP client lifecycle; incorrect hook placement causes missed provisioning
- **Plugin execution order**: Plugins execute in the order defined in ZTP JSON; dependencies between plugins are not automatically resolved
- **Plugin exit codes**: Plugins must return proper exit codes (0 = success) — non-zero marks the section as failed
- **File permissions**: Plugin scripts must be executable; packaging must preserve permissions
- **Network dependency**: ZTP requires network connectivity before most plugins can run; use connectivity-check plugin early in the sequence
- **Config-db ordering**: The configdb-json plugin replaces the running config — order matters if other plugins depend on existing configuration
- **Firmware plugin**: Installing new firmware triggers a reboot; ensure it's the last plugin or ZTP state is persisted
- **Testing without switch**: Tests must mock SONiC system calls, DHCP, and network access
- **systemd integration**: ZTP runs as a systemd service; changes to service files require careful testing
- **Dynamic URLs**: ZTP JSON supports dynamic URL resolution with device-specific variables (serial number, MAC, etc.)
