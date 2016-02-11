ROGRAMS=
SUBDIRS=
LIBRARIES=
ARCHIVES=
HEADERS=

# sdi_sys_v2 - Library that implements SDI API as per new implementation plan
LIBRARIES+= sdi_sys_v2
sdi_sys_v2_SRCS+=sdi_startup.c sdi_entity.c sdi_entity_framework.c
sdi_sys_v2_SRCS+=sdi_thermal.c
sdi_sys_v2_SRCS+=sdi_led.c sdi_media.c
sdi_sys_v2_SRCS+=sdi_fan.c
sdi_sys_v2_SRCS+=sdi_entity_info.c
sdi_sys_v2_SRCS+=sdi_entity_reset.c

sdi_sys_v2_LDFLAGS= -lsdi_framework -levent_log -ldn_common -z defs
sdi_sys_v2_CFLAGS= -Wall -Werror

include ${MAKE_INC}/workspace.mak
