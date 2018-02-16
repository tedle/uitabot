import asyncio

import uita.config
import uita.database
import uita.ui_server

import logging


def initialize_logging(level=logging.DEBUG):
    log = logging.getLogger("uita")
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(logging.Formatter("[%(asctime)s](%(name)s)%(message)s"))
    log.setLevel(level)
    log.addHandler(log_handler)


if __name__ == "__main__":
    initialize_logging()
    config = uita.config.load("../config.json")
    database = uita.database.Database(":memory:")
    loop = asyncio.get_event_loop()
    ui_server = uita.ui_server.Server(database, loop=loop)
    loop.run_until_complete(ui_server.serve(
        config.bot.domain, config.bot.port,
        ssl_cert_file=config.ssl.cert_file, ssl_key_file=config.ssl.key_file
    ))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(ui_server.close())
        loop.close()
