Run-Your-Own Firefox Sync Server
================================

.. image:: https://circleci.com/gh/mozilla-services/syncserver/tree/master.svg?style=svg
   :target: https://circleci.com/gh/mozilla-services/syncserver/tree/master

.. image:: https://img.shields.io/docker/automated/mozilla-services/syncserver.svg?style=flat-square
   :target: https://hub.docker.com/r/mozilla/syncserver/

**Note that this repository is no longer being maintained**. Use this at your own risk, and
with the understanding that it is not being maintained, work is being done on its replacement,
and that no support or assistance will be offered.

This is an all-in-one package for running a self-hosted Firefox Sync server.
It bundles the "tokenserver" project for authentication and the "syncstorage"
project for storage, to produce a single stand-alone webapp.

Complete installation instructions are available at:

   https://mozilla-services.readthedocs.io/en/latest/howtos/run-sync-1.5.html


Quickstart
----------

The Sync Server software runs using **python 2.7**, and the build
process requires **make** and **virtualenv**.  You will need to have the
following packages (or similar, depending on your operating system) installed:

- python2.7
- python2.7-dev
- python-virtualenv
- gcc and g++
- make
- libstdc++
- libffi-dev
- mysql-dev
- musl-dev
- ncurses-dev
- openssl-dev

Take a checkout of this repository, then run "make build" to pull in the
necessary python package dependencies::

    $ git clone https://github.com/mozilla-services/syncserver
    $ cd syncserver
    $ make build

To sanity-check that things got installed correctly, do the following::

    $ make test

Now you can run the server::

    $ make serve

This should start a server on http://localhost:5000/.

Now go into Firefox's `about:config` page, search for a setting named
"tokenServerURI", and change it to point to your server::

    identity.sync.tokenserver.uri:  http://localhost:5000/token/1.0/sync/1.5

(Prior to Firefox 42, the TokenServer preference name for Firefox Desktop was
"services.sync.tokenServerURI". While the old preference name will work in
Firefox 42 and later, the new preference is recommended as the old preference
name will be reset when the user signs out from Sync causing potential
confusion.)

Firefox should now sync against your local server rather than the default
Mozilla-hosted servers.

For more details on setting up a stable deployment, see:

   https://mozilla-services.readthedocs.io/en/latest/howtos/run-sync-1.5.html


Customization
-------------

All customization of the server can be done by editing the file
"syncserver.ini", which contains lots of comments to help you on
your way.  Things you might like to change include:

    * The client-visible hostname for your server.  Edit the "public_url"
      key under the [syncerver] section.

    * The database in which to store sync data.  Edit the "sqluri" setting
      under the [syncserver] section.

    * The secret key to use for signing auth tokens.  Find the "secret"
      entry under the [syncserver] section and follow the instructions
      in the comment to replace it with a strong random key.


Database Backend Modules
------------------------

If your python installation doesn't provide the "sqlite" module by default,
you may need to install it as a separate package::

    $ ./local/bin/pip install pysqlite2

Similarly, if you want to use a different database backend you will need
to install an appropriate python module, e.g::

    $ ./local/bin/pip install PyMySQL
    $ ./local/bin/pip install psycopg2


Runner under Docker
-------------------

`Dockerhub Page <https://hub.docker.com/r/mozilla/syncserver>`_

There is experimental support for running the server inside a Docker
container. The docker image runs with UID/GID 1001/1001.
Build the image like this::

    $ docker build -t syncserver:latest .

Then you can run the server by passing in configuration options as
environment variables, like this::

    $ docker run --rm \
        -p 5000:5000 \
        -e SYNCSERVER_PUBLIC_URL=http://localhost:5000 \
        -e SYNCSERVER_SECRET=<PUT YOUR SECRET KEY HERE> \
        -e SYNCSERVER_SQLURI=sqlite:////tmp/syncserver.db \
        -e SYNCSERVER_BATCH_UPLOAD_ENABLED=true \
        -e SYNCSERVER_FORCE_WSGI_ENVIRON=false \
        -e SYNCSERVER_DEBUG_ENABLED=true \
        -e PORT=5000 \
        mozilla/syncserver:latest

    or

    $ docker run --rm \
        -p 5000:5000 \
        -e SYNCSERVER_PUBLIC_URL=http://localhost:5000 \
        -e SYNCSERVER_SECRET_FILE=<PUT YOUR SECRET KEY FILE LOCATION HERE> \
        -e SYNCSERVER_SQLURI=sqlite:////tmp/syncserver.db \
        -e SYNCSERVER_BATCH_UPLOAD_ENABLED=true \
        -e SYNCSERVER_FORCE_WSGI_ENVIRON=false \
        -e PORT=5000 \
        -v /secret/file/at/host:<PUT YOUR SECRET KEY FILE LOCATION HERE>  \
        mozilla/syncserver:latest

Don't forget to `generate a random secret key <https://mozilla-services.readthedocs.io/en/latest/howtos/run-sync-1.5.html#further-configuration>`_
to use in the `SYNCSERVER_SECRET` environment variable or mount your secret key file!

And you can test whether it's running correctly by using the builtin
function test suite, like so::

    $ /usr/local/bin/python -m syncstorage.tests.functional.test_storage \
        --use-token-server http://localhost:5000/token/1.0/sync/1.5

If you'd like a persistent setup, you can mount a volume as well::

    $ docker run -d \
        -v /syncserver:/data \
        -p 5000:5000 \
        -e SYNCSERVER_PUBLIC_URL=http://localhost:5000 \
        -e SYNCSERVER_SECRET=<PUT YOUR SECRET KEY HERE> \
        -e SYNCSERVER_SQLURI=sqlite:////data/syncserver.db \
        -e SYNCSERVER_BATCH_UPLOAD_ENABLED=true \
        -e SYNCSERVER_FORCE_WSGI_ENVIRON=false \
        -e PORT=5000 \
        mozilla/syncserver:latest

Make sure that /syncserver is owned by 1001:1001


`Docker Compose <https://docs.docker.com/compose>`_ can also be used for structured deployments::

    version: '3.7'
    services:
        syncserver:
            container_name: syncserver
            image: mozilla/syncserver:latest
            volumes:
                - /syncserver:/data
            ports:
                - 5000:5000
            environment:
                SYNCSERVER_PUBLIC_URL: 'http://localhost:5000'
                SYNCSERVER_SECRET: '<PUT YOUR SECRET KEY HERE>'
                SYNCSERVER_SQLURI: 'sqlite:////data/syncserver.db'
                SYNCSERVER_BATCH_UPLOAD_ENABLED: 'true'
                SYNCSERVER_FORCE_WSGI_ENVIRON: 'false'
                PORT: '5000'
            restart: always

Removing Mozilla-hosted data
----------------------------

If you have previously uploaded Firefox Sync data
to the Mozilla-hosted storage service
and would like to remove it,
you can use the following script to do so::

    $ pip install PyFxA
    $ python ./bin/delete_user_data.py user@example.com


Questions, Feedback
-------------------

- Matrix: https://wiki.mozilla.org/Matrix#Getting_Started
- Mailing list: https://mail.mozilla.org/listinfo/services-dev
