# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
"""

Fake node-assignment backend and control interface.

In addition to hosting a simple storage node, this server hosts a fake tokenserver
node-assignent interface and a little management page that can toggle its behaviour
to simulate the storage node migration.  It supports the following states:

* Pre-migration:  all requests to the tokenserver endpoint are assigned uid 1 and
                  are allowed to proceed through to accessing the storage backend.

* Migrating:  all requests to the tokenserver endpoint are assigned uid 1, but when
              they try to acces the storage node they get a 503 error.

* Post-migration:  all requests to the tokenserver endpoint are assigned uid 2 and
                   are allowed to proceed through to accessing the storage backend;
                   a tween enforces that storage requests for uid 1 will receive a
                   401 error in this state.

This broadly simulates the different states we expect to move the servers through
during the production deployment.

"""

import os

from cornice import Service
from pyramid import httpexceptions
from pyramid.response import Response
from pyramid.interfaces import IAuthenticationPolicy

import syncserver.migration

# A GET on / returns a simple management interface,
# while POST requests control the state of the server.

management = Service(name='management', path='/')

@management.get(renderer="string")
def _management(request):
    """HTML for the server management interface."""
    src = os.path.join(os.path.dirname(__file__), 'management.html')
    with open(src) as f:
        content = f.read()
    content = content.format(
        migration_state=request.registry["MigrationStateManager"].current_state_name()
    )
    return Response(content, content_type="text/html")

@management.post()
def _management(request):
    """Command handler for the server management interface."""
    mgr = request.registry["MigrationStateManager"]
    cmd = request.POST["cmd"]
    if cmd == "begin_migration":
        mgr.begin_migration()
    elif cmd == "complete_migration":
        mgr.complete_migration()
    elif cmd == "reset":
        mgr.reset_to_pre_migration_state()
    else:
        return httpexceptions.HTTPBadRequest(body="Unknown cmd: {}".format(cmd))
    return httpexceptions.HTTPFound(request.relative_url("/", to_application=True))


# The fake tokenserver endpoint is hosted at /token/1.0/sync/1.5

token = Service(name='token', path='/token/1.0/sync/1.5')

@token.get()
def _token(request):
    """Fake tokenserver endpoint.
    
    This endpoint ignoreds all auth and just assigns the caller a uid or 1 or 2
    depending on what state the server is currently in.
    """
    migration_state = request.registry["MigrationStateManager"].current_state()
    if migration_state != syncserver.migration.POST_MIGRATION:
        uid = 1
    else:
        uid = 2

    endpoint = request.relative_url("/storage/1.5/{}".format(uid), to_application=True)

    # Sign a token using the fixed uid, for the storage backend to accept.
    auth_policy = request.registry.getUtility(IAuthenticationPolicy) 
    token, key = auth_policy.encode_hawk_id(request, uid)

    return {
        'id': token,
        'key': key,
        'uid': uid,
        'api_endpoint': endpoint,
        'duration': 60,
        'hashalg': 'sha256',
        'hashed_fxa_uid': '0' * 64,
    }
