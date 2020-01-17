# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from pyramid import httpexceptions

import syncserver.migration


def interpose_migration_state_errors(handler, registry):
    """Tween to send errors from storage endpoint based on migration state.
    
    It's a bit weird to do this in a tween, but it means we can use the existing
    syncstorage app without any changes byt just interposing a bit of code in
    front of it.
    """

    def interpose_migration_state_errors_tween(request):
        if request.path.startswith("/storage/"):
            migration_state = request.registry["MigrationStateManager"].current_state()
            if migration_state == syncserver.migration.MIGRATING:
                # We 503-inate the storage node while migration is in progress.
                return httpexceptions.HTTPServiceUnavailable(body="0")
            elif migration_state == syncserver.migration.POST_MIGRATION:
                # We 401-inate the old storage node after migration.
                if request.path.startswith("/storage/1.5/1/"):
                    return httpexceptions.HTTPUnauthorized(body="0")
            elif migration_state == syncserver.migration.PRE_MIGRATION:
                # We won't do this in production, but for testing locally,
                # 401-inate the new storage node if we haven't migrated yet.
                # this will force clients to refresh their token and go back
                # to the old node.
                if request.path.startswith("/storage/1.5/2/"):
                    return httpexceptions.HTTPUnauthorized(body="0")
        return handler(request)

    return interpose_migration_state_errors_tween


def includeme(config):
    """Include all the SyncServer tweens into the given config."""
    config.add_tween("syncserver.tweens.interpose_migration_state_errors")
