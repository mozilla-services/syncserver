SYSTEMPYTHON = `which python2 python | head -n 1`
VIRTUALENV = virtualenv --python=$(SYSTEMPYTHON)
ENV = ./local
TOOLS := $(addprefix $(ENV)/bin/,flake8 nosetests)

.PHONY: all
all: build

.PHONY: build
build: | $(ENV)
$(ENV):
	$(VIRTUALENV) --no-site-packages $(ENV)
	$(ENV)/bin/pip install -r requirements.txt
	$(ENV)/bin/python ./setup.py develop

.PHONY: test
test: | $(TOOLS)
	$(ENV)/bin/flake8 ./syncserver
	$(ENV)/bin/nosetests -s syncstorage.tests
	# Tokenserver tests currently broken due to incorrect file paths
	# $(ENV)/bin/nosetests -s tokenserver.tests
	
	# Test against a running server
	$(ENV)/bin/pserve syncserver/tests.ini & SERVER_PID=$$!; \
	sleep 2; \
	$(ENV)/bin/python -m syncstorage.tests.functional.test_storage \
		--use-token-server http://localhost:5000/token/1.0/sync/1.5; \
	kill $$SERVER_PID

$(TOOLS): | $(ENV)
	$(ENV)/bin/pip install nose flake8

.PHONY: serve
serve: | $(ENV)
	$(ENV)/bin/pserve ./syncserver.ini

.PHONY: clean
clean:
	rm -rf $(ENV)
