Run-Your-Own Firefox Sync Server
================================

This is an all-in-one package for running a self-hosted Firefox Sync server.
If bundles the "tokenserver" project for authentication and the "syncstorage"
project for storage, produce a single stand-alone webapp.

Complete installation instructions are available at:

   https://docs.services.mozilla.com/howtos/run-sync-1.5.html


Quickstart
----------

The Sync Server software runs using **python 2.6** or later, and the build
process requires **make** and **virtualenv**.  You will need to have the
following packages (or similar, depending on your operating system) installed:

- python2.7
- python2.7-dev
- python-virtualenv
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

    services.sync.tokenServerURI:  http://localhost:5000/token/1.0/sync/1.5

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


Questions, Feedback
-------------------

- IRC channel: #sync. See http://irc.mozilla.org/
- Mailing list: https://mail.mozilla.org/listinfo/services-dev
