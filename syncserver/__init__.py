# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import binascii
import os
import logging
try:
    from urlparse import urlparse, urlunparse, urljoin
except ImportError:
    from urllib.parse import urlparse, urlunparse, urljoin

import requests

from pyramid.response import Response


import mozsvc.config


logger = logging.getLogger("syncserver")


def includeme(config):
    """Install SyncServer application into the given Pyramid configurator."""
    # Set the umask so that files are created with secure permissions.
    # Necessary for e.g. created-on-demand sqlite database files.
    os.umask(0o077)

    settings = config.registry.settings

    sqluri = settings.get("syncserver.sqluri")
    if sqluri is None:
        rootdir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        sqluri = "sqlite:///" + os.path.join(rootdir, "syncserver.db")
        settings["sqluri"] = sqluri

    if "storage.backend" not in settings:
        # Default to sql syncstorage backend
        settings["storage.backend"] = "syncstorage.storage.sql.SQLStorage"
        settings["storage.sqluri"] = sqluri
        settings["storage.create_tables"] = True
    if "storage.batch_upload_enabled" not in settings:
        settings["storage.batch_upload_enabled"] = True
        
    if "loggers" not in settings:
        # Default to basic logging config.
        root_logger = logging.getLogger("")
        if not root_logger.handlers:
            logging.basicConfig(level=logging.INFO)

    if "hawkauth.secrets.backend" not in settings:
        # Default to a secret that's not really that secret...
        settings["hawkauth.secrets.backend"] = "mozsvc.secrets.FixedSecrets"
        settings["hawkauth.secrets.secrets"] = ["secret!!"]

    config.include("cornice")
    config.include("syncserver.migration")
    config.include("syncserver.tweens")
    config.scan("syncserver.views")
    config.include("syncstorage", route_prefix="/storage")


def get_configurator(global_config, **settings):
    """Load a mozsvc configurator object from deployment settings."""
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
