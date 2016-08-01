sonic-sdi-sys
-------------
An implementation of the SONiC's SDI API for Dell branded hardware (S6000, S4000 and S3000 series of switches) based on XML and driver configuration files.
The sonic-sdi-sys repo drives the initialization of the sonic-sdi-framework (mostly library functions) and the sonic-sdi-device-drivers (actual device communication).

Description
-----------

This repo along with the sdi-framework and the sdi-device-drivers provides a complete SDI implementation.  As you probably know, the PAS uses the SDI API to drive/understand the behaviour of the platform.

Building
--------
Please see the instructions in the sonic-nas-manifest repo for more details on the common build tools.  [Sonic-nas-manifest](https://github.com/Azure/sonic-nas-manifest)

Development Dependencies:

 - sonic-logging
 - sonic-common-utils
 - sonic-sdi-api
 - sonic-sdi-framework

Dependent Packages:

 - libsonic-logging1 libsonic-logging-dev libsonic-common1 libsonic-common-dev libsonic-sdi-framework1 libsonic-sdi-framework-dev sonic-sdi-api-dev

BUILD CMD: sonic_build --dpkg libsonic-logging1 libsonic-logging-dev libsonic-common1 libsonic-common-dev libsonic-sdi-framework1 libsonic-sdi-framework-dev sonic-sdi-api-dev -- clean binary

(c) Dell 2016
