Bot Commands
============
uitabot chat commands that can be used in the Discord client.

Chat commands are prefixed by a single "``.``" (e.g., ``.help``).

.. Search and replace would be really nice for inserting the prefix to every command shown, but
.. rST both doesn't allow for replace terms to be embedded in markup (like ``) and also requires
.. replace terms to be surrounded by whitespace. So we offload this overhead onto the poor person
.. reading these useless docs.

- ``help``, ``?`` Explains bot usage and shows the list of usable commands.
- ``play``, ``p`` Enqueues a provided ``<URL>``.
- ``search``, ``s`` Searches YouTube for a provided ``<QUERY>``.
- ``skip`` Skips the currently playing song.
- ``clear`` Empties the playback queue.
- ``join``, ``j`` Joins the voice channel you are currently in.
- ``leave``, ``l`` Leaves the voice channel.
- ``set-role`` (Admin) Set a ``<ROLE>`` needed to use bot commands. Leave empty for free access.
