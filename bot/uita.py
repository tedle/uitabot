import asyncio

import uita
import uita.config

import logging
import sys


def initialize_logging(level=logging.DEBUG):
    # Websockets uses the logging.lastResort handler which by default prints
    # all of its uncatchable and unpreventable exception warnings to stderr
    logging.getLogger("websockets").addHandler(logging.NullHandler())

    log = logging.getLogger("uita")
    log_handler = logging.StreamHandler(stream=sys.stdout)
    log_handler.setFormatter(logging.Formatter("[%(asctime)s](%(name)s)%(message)s"))
    log.setLevel(level)
    log.addHandler(log_handler)


if __name__ == "__main__":
    try:
        # Initialization
        initialize_logging()
        config = uita.config.load("../config.json")
        uita.loop.create_task(uita.server.start(":memory:", config, loop=uita.loop))
        uita.loop.create_task(uita.bot.start(config.discord.token))
        # Main loop
        uita.loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        # Stop running services
        uita.loop.run_until_complete(uita.server.stop())
        uita.loop.run_until_complete(uita.bot.logout())
        # Find and cancel all remaining tasks (spawned by discord.py)
        task_list = asyncio.Task.all_tasks(loop=uita.loop)
        task_list_future = asyncio.gather(*task_list, loop=uita.loop, return_exceptions=True)
        try:
            task_list_future.cancel()
            uita.loop.run_until_complete(task_list_future)
        except asyncio.CancelledError:
            pass
        # Finalize shutdown
        uita.loop.close()
