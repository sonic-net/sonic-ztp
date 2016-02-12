PROGRAMS=
SUBDIRS=src utils
LIBRARIES=
ARCHIVES=
HEADERS=

SYSROOT_PREFIX=../platform-root/opt/ngos
DEVKIT_HEADER=${SYSROOT_PREFIX}/inc
INC_CFLAGS=-I${DEVKIT_HEADER}

DEVKIT_LIB=${SYSROOT_PREFIX}/lib
INSTALL_LIB=${DEVKIT_LIB}

all: install devkit

libsdi_sys_v2.so: $(wildcard src/*.c) $(wildcard inc/*.h)
	gcc -shared -fPIC $(wildcard src/*.c) $(INC_CFLAGS) -Iinc/ -L$(DEVKIT_LIB) -o $@ -lsdi_framework -levent_log -ldn_common  -z defs

LIB_PATH=.

install: libsdi_sys_v2.so
	cp $< $(INSTALL_LIB)

devkit: libsdi_sys_v2.so
	cp libsdi_sys_v2.so $(DEVKIT_LIB)

.PHONY: all clean devkit install
