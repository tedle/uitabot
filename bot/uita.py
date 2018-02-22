import asyncio

import uita
import uita.config
import uita.database

import logging


def initialize_logging(level=logging.DEBUG):
    log = logging.getLogger("uita")
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(logging.Formatter("[%(asctime)s](%(name)s)%(message)s"))
    log.setLevel(level)
    log.addHandler(log_handler)


if __name__ == "__main__":
    try:
        initialize_logging()
        config = uita.config.load("../config.json")
        database = uita.database.Database(":memory:")
        uita.loop.run_until_complete(uita.server.start(
            config.bot.domain, config.bot.port, database,
            ssl_cert_file=config.ssl.cert_file, ssl_key_file=config.ssl.key_file,
            loop=uita.loop
        ))
        uita.loop.create_task(uita.bot.start(config.discord.token))
        uita.loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        uita.loop.run_until_complete(asyncio.gather(
            uita.server.stop(),
            uita.bot.logout()
        ))
        task_list = asyncio.Task.all_tasks(loop=uita.loop)
        task_list_future = asyncio.gather(*task_list, loop=uita.loop)
        try:
            task_list_future.cancel()
            uita.loop.run_until_complete(task_list_future)
        except asyncio.CancelledError:
            pass
        uita.loop.close()
