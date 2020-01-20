# Once there is Python 3 support in this package and it's dependencies
# the detection of the used Python version should be changed.
# The following line prefers `python` as this will allow this to work
# in CI (e.g. Travis CI) and put up the configured Python version:
# SYSTEMPYTHON = `which python python3 python2 | head -n 1`
SYSTEMPYTHON = `which python2 python | head -n 1`
VIRTUALENV = $(SYSTEMPYTHON) -m virtualenv --python=$(SYSTEMPYTHON)
ENV = ./local
TOOLS := $(addprefix $(ENV)/bin/,flake8 nosetests)

# Hackety-hack around OSX system python bustage.
# The need for this should go away with a future osx/xcode update.
ARCHFLAGS = -Wno-error=unused-command-line-argument-hard-error-in-future

# Hackety-hack around errors duing compile of ultramemcached.
CFLAGS = "-Wno-error -Wno-error=format-security"

INSTALL = CFLAGS=$(CFLAGS) ARCHFLAGS=$(ARCHFLAGS) $(ENV)/bin/pip install

.PHONY: all
all: build

.PHONY: build
build: | $(ENV)/COMPLETE
$(ENV)/COMPLETE: requirements.txt
	$(VIRTUALENV) --no-site-packages $(ENV)
	$(INSTALL) -i https://pypi.python.org/simple -U pip
	$(INSTALL) -r requirements.txt
	$(ENV)/bin/python ./setup.py develop
	touch $(ENV)/COMPLETE


.PHONY: serve
serve: | $(ENV)/COMPLETE
	$(ENV)/bin/gunicorn --paste ./syncserver.ini --workers 1

.PHONY: clean
clean:
	rm -rf $(ENV)
