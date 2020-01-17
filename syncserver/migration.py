# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Helpers for fiddling with the migration state of the server.
We allow the server to be in one of three states:

* Pre-migration: the user is syncing as normal to the old backend.

* Migrating:  we're actively moving the user's data to the new backend.

* Post-migration:  we've finished moving the user's data to the new backend.

You can use the functions exposed by this module to move the server between
the different states.
"""

from sqlalchemy import Column, Integer
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.sql import text as sqltext

PRE_MIGRATION = 1
MIGRATING = 2
POST_MIGRATION = 3

# A very simple db table in which to store the migration state.

_metadata = MetaData()

_migration = Table(
    "migration",
    _metadata,
    Column("state", Integer(), nullable=False),
)


class MigrationStateManager(object):

    def __init__(self, sqluri):
        self.sqluri = sqluri
        self._engine = create_engine(sqluri, pool_reset_on_return=True)
        _migration.create(self._engine, checkfirst=True)
    
    def _query(self, q, **kwds):
        return self._engine.execute(sqltext(q), **kwds)

    def current_state(self):
        row = self._query("""
          SELECT state FROM migration
        """).fetchone()
        if row is None:
            return PRE_MIGRATION
        return row[0]
 
    def current_state_name(self):
        state = self.current_state()
        if state == PRE_MIGRATION:
            return "PRE_MIGRATION"
        if state == MIGRATING:
            return "MIGRATING"
        if state == POST_MIGRATION:
            return "POST_MIGRATION"
        return "WTF?"

    def begin_migration(self):
        self._set_current_state(MIGRATING)

    def complete_migration(self):
        self._migrate_data()
        self._set_current_state(POST_MIGRATION)
        
    def reset_to_pre_migration_state(self):
        self._clear_storage()
        self._set_current_state(PRE_MIGRATION)

    def _set_current_state(self, state):
        r = self._query("""
          UPDATE migration SET state=:state
        """, state=state)
        if r.rowcount == 0:
          self._query("""
            INSERT INTO migration (state) VALUES (:state)
          """, state=state)

    def _migrate_data(self):
        # Migrating data is remarkably easy when it's already in the same db!
        self._query("""
          UPDATE bso SET userid=2 WHERE userid=1;
        """)
        self._query("""
          UPDATE user_collections SET userid=2 WHERE userid=1;
        """)

    def _clear_storage(self):
        self._query("""
          DELETE FROM batch_upload_items;
        """)
        self._query("""
          DELETE FROM batch_uploads;
        """)
        self._query("""
          DELETE FROM bso;
        """)
        self._query("""
          DELETE FROM collections;
        """)
        self._query("""
          DELETE FROM user_collections;
        """)

def includeme(config):
    sqluri = config.registry.settings["sqluri"]
    config.registry["MigrationStateManager"] = MigrationStateManager(sqluri)