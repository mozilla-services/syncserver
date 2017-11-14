# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import logging
from urlparse import urlparse, urlunparse

from pyramid.response import Response
from pyramid.events import NewRequest, subscriber

try:
    import requests.packages.urllib3.contrib.pyopenssl
    HAS_PYOPENSSL = True
except ImportError:
    HAS_PYOPENSSL = False

import mozsvc.config

from tokenserver.util import _JSONError

logger = logging.getLogger("syncserver")


DEFAULT_TOKENSERVER_BACKEND = "syncserver.staticnode.StaticNodeAssignment"


def includeme(config):
    """Install SyncServer application into the given Pyramid configurator."""
    # Set the umask so that files are created with secure permissions.
    # Necessary for e.g. created-on-demand sqlite database files.
    os.umask(0077)

    # If PyOpenSSL is available, configure requests to use it.
    # This helps improve security on older python versions.
    if HAS_PYOPENSSL:
        requests.packages.urllib3.contrib.pyopenssl.inject_into_urllib3()

    settings = config.registry.settings
    import_settings_from_environment_variables(settings)

    # Sanity-check the deployment settings and provide sensible defaults.
    public_url = settings.get("syncserver.public_url")
    if public_url is None:
        raise RuntimeError("you must configure syncserver.public_url")
    public_url = public_url.rstrip("/")
    settings["syncserver.public_url"] = public_url

    secret = settings.get("syncserver.secret")
    if secret is None:
        secret = os.urandom(32).encode("hex")
    sqluri = settings.get("syncserver.sqluri")
    if sqluri is None:
        rootdir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        sqluri = "sqlite:///" + os.path.join(rootdir, "syncserver.db")

    # Configure app-specific defaults based on top-level configuration.
    settings.pop("config", None)
    if "tokenserver.backend" not in settings:
        # Default to our simple static node-assignment backend
        settings["tokenserver.backend"] = DEFAULT_TOKENSERVER_BACKEND
    if settings["tokenserver.backend"] == DEFAULT_TOKENSERVER_BACKEND:
        # Provide some additional defaults for the default backend,
        # unless overridden in the config.
        if "tokenserver.sqluri" not in settings:
            settings["tokenserver.sqluri"] = sqluri
        if "tokenserver.node_url" not in settings:
            settings["tokenserver.node_url"] = public_url
        if "endpoints.sync-1.5" not in settings:
            settings["endpoints.sync-1.5"] = "{node}/storage/1.5/{uid}"
    if "tokenserver.monkey_patch_gevent" not in settings:
        # Default to no gevent monkey-patching
        settings["tokenserver.monkey_patch_gevent"] = False
    if "tokenserver.applications" not in settings:
        # Default to just the sync-1.5 application
        settings["tokenserver.applications"] = "sync-1.5"
    if "tokenserver.secrets.backend" not in settings:
        # Default to a single fixed signing secret
        settings["tokenserver.secrets.backend"] = "mozsvc.secrets.FixedSecrets"
        settings["tokenserver.secrets.secrets"] = [secret]
    if "tokenserver.allow_new_users" not in settings:
        allow_new_users = settings.get("syncserver.allow_new_users")
        if allow_new_users is not None:
            settings["tokenserver.allow_new_users"] = allow_new_users
    if "hawkauth.secrets.backend" not in settings:
        # Default to the same secrets backend as the tokenserver
        for key in settings.keys():
            if key.startswith("tokenserver.secrets."):
                newkey = "hawkauth" + key[len("tokenserver"):]
                settings[newkey] = settings[key]
    if "storage.backend" not in settings:
        # Default to sql syncstorage backend
        settings["storage.backend"] = "syncstorage.storage.sql.SQLStorage"
        settings["storage.sqluri"] = sqluri
        settings["storage.create_tables"] = True
    # The batch-upload API is not yet stable in production.
    if "storage.batch_upload_enabled" not in settings:
        settings["storage.batch_upload_enabled"] = False
    if "browserid.backend" not in settings:
        # Default to local verifier to reduce external dependencies.
        # Use base of public_url as only audience
        audience = urlunparse(urlparse(public_url)._replace(path=""))
        settings["browserid.backend"] = "tokenserver.verifiers.LocalVerifier"
        settings["browserid.audiences"] = audience
    if "loggers" not in settings:
        # Default to basic logging config.
        root_logger = logging.getLogger("")
        if not root_logger.handlers:
            logging.basicConfig(level=logging.WARN)
    if "fxa.metrics_uid_secret_key" not in settings:
        # Default to a randomly-generated secret.
        # This setting isn't useful in a self-hosted setup
        # and setting a default avoids scary-sounding warnings.
        settings["fxa.metrics_uid_secret_key"] = os.urandom(16).encode("hex")

    # Include the relevant sub-packages.
    config.scan("syncserver", ignore=["syncserver.wsgi_app"])
    config.include("syncstorage", route_prefix="/storage")
    config.include("tokenserver", route_prefix="/token")

    # Add a top-level "it works!" view.
    def itworks(request):
        return Response("it works!")

    config.add_route('itworks', '/')
    config.add_view(itworks, route_name='itworks')


def import_settings_from_environment_variables(settings, environ=None):
    """Helper function to import settings from environment variables.

    This helper exists to allow the most commonly-changed settings to be
    configured via environment variables, which is useful when deploying
    with docker.  For more complex configuration needs you should write
    a .ini config file.
    """
    if environ is None:
        environ = os.environ
    SETTINGS_FROM_ENVIRON = (
        ("SYNCSERVER_PUBLIC_URL", "syncserver.public_url", str),
        ("SYNCSERVER_SECRET", "syncserver.secret", str),
        ("SYNCSERVER_SQLURI", "syncserver.sqluri", str),
        ("SYNCSERVER_ALLOW_NEW_USERS",
         "syncserver.allow_new_users",
         str_to_bool),
        ("SYNCSERVER_FORCE_WSGI_ENVIRON",
         "syncserver.force_wsgi_environ",
         str_to_bool),
        ("SYNCSERVER_BATCH_UPLOAD_ENABLED",
         "storage.batch_upload_enabled",
         str_to_bool),
    )
    for key, name, convert in SETTINGS_FROM_ENVIRON:
        try:
            settings[name] = convert(environ[key])
        except KeyError:
            pass


def str_to_bool(value):
    """Helper to convert textual boolean strings to actual booleans."""
    if value.lower() in ("true", "on", "1", "yes"):
        return True
    if value.lower() in ("false", "off", "0", "no"):
        return True
    raise ValueError("unable to parse boolean from %r" % (value,))


@subscriber(NewRequest)
def reconcile_wsgi_environ_with_public_url(event):
    """Event-listener that checks and tweaks WSGI environ based on public_url.

    This is a simple trick to help ensure that the configured public_url
    matches the actual deployed address.  It fixes fixes parts of the WSGI
    environ where it makes sense (e.g. SCRIPT_NAME) and warns about any parts
    that seem obviously mis-configured (e.g. http:// versus https://).

    It's very important to get public_url and WSGI environ matching exactly,
    since they're used for browserid audience checking and HAWK signature
    validation, so mismatches can easily cause strange and cryptic errors.
    """
    request = event.request
    public_url = request.registry.settings["syncserver.public_url"]
    p_public_url = urlparse(public_url)
    # If we don't have a SCRIPT_NAME, take it from the public_url.
    # This is often the case if we're behind e.g. an nginx proxy that
    # is serving us at some sub-path.
    if not request.script_name:
        request.script_name = p_public_url.path.rstrip("/")
    # If the environ does not match public_url, requests are almost certainly
    # going to fail due to auth errors.  We can either bail out early, or we
    # can forcibly clobber the WSGI environ with the values from public_url.
    # This is a security risk if you've e.g. mis-configured the server, so
    # it's not enabled by default.
    application_url = request.application_url
    if public_url != application_url:
        if not request.registry.settings.get("syncserver.force_wsgi_environ"):
            msg = "\n".join((
                "The public_url setting doesn't match the application url.",
                "This will almost certainly cause authentication failures!",
                "    public_url setting is: %s" % (public_url,),
                "    application url is:    %s" % (application_url,),
                "You can disable this check by setting the force_wsgi_environ",
                "option in your config file, but do so at your own risk.",
            ))
            logger.error(msg)
            raise _JSONError([msg], status_code=500)
        request.scheme = p_public_url.scheme
        request.host = p_public_url.netloc
        request.script_name = p_public_url.path.rstrip("/")


def get_configurator(global_config, **settings):
    """Load a SyncStorge configurator object from deployment settings."""
    config = mozsvc.config.get_configurator(global_config, **settings)
    config.begin()
    try:
        config.include(includeme)
    finally:
        config.end()
    return config


def main(global_config={}, **settings):
    """Load a SyncStorage WSGI app from deployment settings."""
    config = get_configurator(global_config, **settings)
    return config.make_wsgi_app()
