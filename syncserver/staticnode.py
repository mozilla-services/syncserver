# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Simple node-assignment backend using a single, static node.

This is a greatly-simplified node-assignment backend.  It keeps user records
in an SQL database, but does not attempt to do any node management.  All users
are implicitly assigned to a single, static node.

XXX TODO: move this into the tokenserver repo.

"""
import time
import urlparse
from mozsvc.exceptions import BackendError

from sqlalchemy import Column, Integer, String, BigInteger, Index
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import text as sqltext
from sqlalchemy.exc import IntegrityError

from tokenserver.assignment import INodeAssignment
from zope.interface import implements


metadata = MetaData()


users = Table(
    "users",
    metadata,
    Column("uid", Integer(), primary_key=True, autoincrement=True,
           nullable=False),
    Column("service", String(32), nullable=False),
    Column("email", String(255), nullable=False),
    Column("generation", BigInteger(), nullable=False),
    Column("client_state", String(32), nullable=False),
    Column("created_at", BigInteger(), nullable=False),
    Column("replaced_at", BigInteger(), nullable=True),
    Index('lookup_idx', 'email', 'service', 'created_at'),
    Index('clientstate_idx', 'email', 'service', 'client_state', unique=True),
)


_GET_USER_RECORDS = sqltext("""\
select
    uid, generation, client_state
from
    users
where
    email = :email
and
    service = :service
order by
    created_at desc, uid desc
limit
    20
""")


_CREATE_USER_RECORD = sqltext("""\
insert into
    users
    (service, email, generation, client_state, created_at, replaced_at)
values
    (:service, :email, :generation, :client_state, :timestamp, NULL)
""")


_UPDATE_GENERATION_NUMBER = sqltext("""\
update
    users
set
    generation = :generation
where
    service = :service and email = :email and
    generation < :generation and replaced_at is null
""")


_REPLACE_USER_RECORDS = sqltext("""\
update
    users
set
    replaced_at = :timestamp
where
    service = :service and email = :email
    and replaced_at is null and created_at < :timestamp
""")


def get_timestamp():
    """Get current timestamp in milliseconds."""
    return int(time.time() * 1000)


class StaticNodeAssignment(object):
    implements(INodeAssignment)

    def __init__(self, sqluri, node_url, **kw):
        self.sqluri = sqluri
        self.node_url = node_url
        self.driver = urlparse.urlparse(sqluri).scheme.lower()
        sqlkw = {
            "logging_name": "syncserver",
            "connect_args": {},
            "poolclass": QueuePool,
            "pool_reset_on_return": True,
        }
        if self.driver == "sqlite":
            # We must mark it as safe to share sqlite connections between
            # threads.  The pool will ensure there's on race conditions.
            sqlkw["connect_args"]["check_same_thread"] = False
            # If using a :memory: database, we must use a QueuePool of size
            # 1 so that a single connection is shared by all threads.
            if urlparse.urlparse(sqluri).path.lower() in ("/", "/:memory:"):
                sqlkw["pool_size"] = 1
                sqlkw["max_overflow"] = 0
        self._engine = create_engine(sqluri, **sqlkw)
        users.create(self._engine, checkfirst=True)

    def get_user(self, service, email):
        params = {'service': service, 'email': email}
        res = self._engine.execute(_GET_USER_RECORDS, **params)
        try:
            row = res.fetchone()
            if row is None:
                return None
            # The first row is the most up-to-date user record.
            user = {
                'email': email,
                'uid': row.uid,
                'node': self.node_url,
                'generation': row.generation,
                'client_state': row.client_state,
                'old_client_states': {}
            }
            # Any subsequent rows are due to old client-state values.
            row = res.fetchone()
            while row is not None:
                user['old_client_states'][row.client_state] = True
                row = res.fetchone()
            return user
        finally:
            res.close()

    def create_user(self, service, email, generation=0, client_state=''):
        params = {
            'service': service, 'email': email, 'generation': generation,
            'client_state': client_state, 'timestamp': get_timestamp()
        }
        try:
            res = self._engine.execute(_CREATE_USER_RECORD, **params)
        except IntegrityError:
            raise
            return self.get_user(service, email)
        else:
            res.close()
            return {
                'email': email,
                'uid': res.lastrowid,
                'node': self.node_url,
                'generation': generation,
                'client_state': client_state,
                'old_client_states': {}
            }

    def update_user(self, service, user, generation=None, client_state=None):
        if client_state is None:
            # uid can stay the same, just update the generation number.
            if generation is not None:
                params = {
                    'service': service,
                    'email': user['email'],
                    'generation': generation,
                }
                res = self._engine.execute(_UPDATE_GENERATION_NUMBER, **params)
                res.close()
                user['generation'] = max(generation, user['generation'])
        else:
            # reject previously-seen client-state strings.
            if client_state == user['client_state']:
                raise BackendError('previously seen client-state string')
            if client_state in user['old_client_states']:
                raise BackendError('previously seen client-state string')
            # need to create a new record for new client_state.
            if generation is not None:
                generation = max(user['generation'], generation)
            else:
                generation = user['generation']
            now = get_timestamp()
            params = {
                'service': service, 'email': user['email'],
                'generation': generation, 'client_state': client_state,
                'timestamp': now,
            }
            try:
                res = self._engine.execute(_CREATE_USER_RECORD, **params)
            except IntegrityError:
                user.update(self.get_user(service, user['email']))
            else:
                self.get_user(service, user['email'])
                user['uid'] = res.lastrowid
                user['generation'] = generation
                user['old_client_states'][user['client_state']] = True
                user['client_state'] = client_state
                res.close()
            # mark old records as having been replaced.
            # if we crash here, they are unmarked and we may fail to
            # garbage collect them for a while, but the active state
            # will be undamaged.
            params = {
                'service': service, 'email': user['email'], 'timestamp': now
            }
            res = self._engine.execute(_REPLACE_USER_RECORDS, **params)
            res.close()
