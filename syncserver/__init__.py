# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from pyramid.response import Response
import mozsvc.config


def includeme(config):
    """Install SyncServer application into the given Pyramid configurator."""
    # Set the umask so that files are created with secure permissions.
    # Necessary for e.g. created-on-demand sqlite database files.
    os.umask(0077)

    # Sanity-check the deployment settings and provide sensible defaults.
    settings = config.registry.settings
    public_url = settings.get("syncserver.public_url")
    if public_url is None:
        raise RuntimeError("you much configure syncserver.public_url")
    secret = settings.get("syncserver.secret")
    if secret is None:
        secret = os.urandom(32).encode("hex")
    sqluri = settings.get("syncserver.sqluri")
    if sqluri is None:
        sqluri = "sqlite:///:memory:"

    # Configure app-specific defaults based on top-level configuration.
    settings.pop("config", None)
    if "tokenserver.backend" not in settings:
        # Default to sql node-assignment backend
        settings["tokenserver.backend"] =\
            "tokenserver.assignment.sqlnode.SQLNodeAssignment"
        settings["tokenserver.sqluri"] = sqluri
    if "tokenserver.applications" not in settings:
        # Default to just the sync-1.5 application
        settings["tokenserver.applications"] = "sync-1.5"
    if "tokenserver.secrets.backend" not in settings:
        # Default to a single fixed signing secret
        settings["tokenserver.secrets.backend"] = "mozsvc.secrets.FixedSecrets"
        settings["tokenserver.secrets.secrets"] = [secret]
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
    if "browserid.backend" not in settings:
        # Default to remote verifier, with public_url as only audience
        settings["browserid.backend"] = "tokenserver.verifiers.RemoteVerifier"
        settings["browserid.audiences"] = public_url
    if "metlog.backend" not in settings:
        # Default to logging to stdout
        settings["metlog.backend"] = "mozsvc.metrics.MetlogPlugin"
        settings["metlog.enabled"] = True
        settings["metlog.sender_class"] = "metlog.senders.StdOutSender"
    if "cef.use" not in settings:
        # Default to no CEF logging
        settings["cef.use"] = False

    # Include the relevant sub-packages.
    config.include("syncstorage", route_prefix="/storage")
    config.include("tokenserver", route_prefix="/token")

    # Add a top-level "it works!" view.
    def itworks(request):
        return Response("it works!")

    config.add_route('itworks', '/')
    config.add_view(itworks, route_name='itworks')


def get_configurator(global_config, **settings):
    """Load a SyncStorge configurator object from deployment settings."""
    config = mozsvc.config.get_configurator(global_config, **settings)
    config.begin()
    try:
        config.include(includeme)
    finally:
        config.end()
    return config


def main(global_config, **settings):
    """Load a SyncStorage WSGI app from deployment settings."""
    config = get_configurator(global_config, **settings)
    return config.make_wsgi_app()
