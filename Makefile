VIRTUALENV = virtualenv
PYTHON = local/bin/python
NOSE = local/bin/nosetests -s
FLAKE8 = local/bin/flake8
PIP = local/bin/pip
PIP_CACHE = /tmp/pip-cache.${USER}
BUILD_TMP = /tmp/syncstorage-build.${USER}
PYPI = https://pypi.python.org/simple
INSTALL = $(PIP) install -U -i $(PYPI)

.PHONY: all build test serve clean

all:	build test

build:
	$(VIRTUALENV) --no-site-packages --distribute ./local
	$(INSTALL) --upgrade Distribute
	$(INSTALL) pip
	$(INSTALL) nose
	$(INSTALL) flake8
	$(INSTALL) -r requirements.txt
	$(PYTHON) ./setup.py develop

test:
	# Basic syntax and sanity checks.
	$(FLAKE8) ./syncserver
	# Testcases from the bundled apps.
	$(NOSE) syncstorage.tests
	$(NOSE) tokenserver.tests
	# Live tests against a running server.
	./local/bin/pserve syncserver/tests.ini & SERVER_PID=$$! ; sleep 2 ; ./local/bin/python -m syncstorage.tests.functional.test_storage --use-token-server http://localhost:5000/token/1.0/sync/1.5 ; kill $$SERVER_PID

serve:
	./local/bin/pserve ./syncserver.ini

clean:
	rm -rf ./local
