Run-Your-Own Firefox Sync Server
================================

.. image:: https://circleci.com/gh/mozilla-services/syncserver/tree/master.svg?style=svg 
   :target: https://circleci.com/gh/mozilla-services/syncserver/tree/master 

.. image:: https://img.shields.io/docker/automated/mozilla-services/syncserver.svg?style=flat-square 
   :target: https://hub.docker.com/r/mozilla/syncserver/ 

This is an all-in-one package for running a self-hosted Firefox Sync server.
It bundles the "tokenserver" project for authentication and the "syncstorage"
project for storage, to produce a single stand-alone webapp.

Complete installation instructions are available at:

   https://docs.services.mozilla.com/howtos/run-sync-1.5.html


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

   https://docs.services.mozilla.com/howtos/run-sync-1.5.html


Customization
-------------

All customization of the server can be done by editing the file
"syncserver.ini", which contains lots of comments to help you on
your way.  Things you might like to change include:

    * The client-visible hostname for your server.  Edit the "public_url"
      key under the [syncstorage] section.

    * The database in which to store sync data.  Edit the "sqluri" setting
      under the [syncstorage] section.


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

There is experimental support for running the server inside a Docker
container.  Build the image like this::

    $ docker build -t syncserver:latest .

Then you can run the server by passing in configuration options as
environmet variables, like this::

    $ docker run --rm \
        -p 631:631 \
        -p 5000:5000 \
        -e SYNCSERVER_PUBLIC_URL=http://localhost:5000 \
        -e SYNCSERVER_SECRET=5up3rS3kr1t \
        -e SYNCSERVER_SQLURI=sqlite:////tmp/syncserver.db \
        -e SYNCSERVER_BATCH_UPLOAD_ENABLED=true \
        -e SYNCSERVER_FORCE_WSGI_ENVIRON=false \
        syncserver:latest \
        /usr/local/bin/gunicorn --bind localhost:5000 \
        syncserver.wsgi_app

And you can test whether it's running correctly by using the builtin
function test suite, like so::

    $ /local/bin/python -m syncstorage.tests.functional.test_storage \
        --use-token-server http://localhost:5000/token/1.0/sync/1.5



Questions, Feedback
-------------------

- IRC channel: #sync. See http://irc.mozilla.org/
- Mailing list: https://mail.mozilla.org/listinfo/services-dev
