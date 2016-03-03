
#All exported headers
nobase_include_HEADERS = sonic/sdi_register_common_api.h sonic/sdi_register_eeprom_api.h \
                        sonic/sdi_register_fantray_api.h sonic/util.h


#The sdi-sys library
lib_LTLIBRARIES = libsonic_sdi_sys.la

libsonic_sdi_sys_la_SOURCES = src/sdi_entity.c src/sdi_entity_framework.c \
                              src/sdi_entity_info.c src/sdi_entity_reset.c \
                              src/sdi_fan.c src/sdi_led.c src/sdi_media.c src/sdi_startup.c \
                              src/sdi_thermal.c


libsonic_sdi_sys_la_LDFLAGS = -lsonic_sdi_framework -lsonic_common -lsonic_logging -lpthread -lrt
libsonic_sdi_sys_la_CFLAGS = -I$(top_srcdir)/sonic  -I$(includedir)/sonic  -I$(includedir)/sonic/private


