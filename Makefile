PKG := sonic-ztp
all: $(PKG)

.PHONY: doc

doc:
	@doxygen doc/Doxyfile

$(PKG):
	@fakeroot debian/rules clean
	@fakeroot debian/rules binary-indep

clean:
	@rm -rf debian/$(PKG)
	@rm -f debian/$(PKG).debhelper.log
	@rm -f debian/$(PKG).postinst.debhelper
	@rm -f debian/$(PKG).postrm.debhelper
	@rm -f debian/$(PKG).prerm.debhelper
	@rm -f debian/$(PKG).substvars
	@rm -f debian/debhelper-build-stamp
	@rm -f debian/files
	@rm -rf doc/html
	@rm -f $(PKG)_*_all.deb










