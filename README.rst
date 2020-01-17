The Very Hacky Migration-Testing Sync Server
============================================

This is a hacked-up sync server designed to help test client behaviour
during the migration to old MySQL-backed sync storage nodes to the new
Spanner-backed durable mega-node.

Run the server using `make server`, and it'll bind to http://localhost:5000/.
Open up that URL for an incredibly bare-bones management interface.

Configure your browser to use "http://localhost/token/1.0/sync/1.5" for its
tokenserver URL. Sync it. Use the managment interface to trigger migration
events. See what happens. It'll be fun!