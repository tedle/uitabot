try:
    import asyncio
    import sys
    import websockets

    import uita
    import uita.config
    import uita.utils

    import logging
    log = logging.getLogger("uita")
except KeyboardInterrupt:
    import sys
    sys.exit(0)


def initialize_logging(level: int = logging.DEBUG) -> None:
    # Websockets uses the logging.lastResort handler which by default prints
    # all of its uncatchable and unpreventable exception warnings to stderr
    logging.getLogger("websockets").addHandler(logging.NullHandler())

    log_handler = logging.StreamHandler(stream=sys.stdout)
    log_handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
    log.setLevel(level)
    log.addHandler(log_handler)
    log.info("uitabot@{}".format(uita.__version__))


def check_ffmpeg() -> None:
    try:
        version = uita.utils.ffmpeg_version()
        if version is None:
            log.error("FFmpeg version is unknown, may affect audio streaming")
        elif version[0] < 4:
            log.warn("FFmpeg version is older than 4.0, may affect audio streaming")
    except FileNotFoundError:
        log.fatal("FFmpeg not found, must be installed to stream audio")
        sys.exit(0)


if __name__ == "__main__":
    try:
        # Initialization
        config = uita.config.load(uita.utils.config_file())
        initialize_logging(level=logging.INFO if not config.bot.verbose_logging else logging.DEBUG)
        check_ffmpeg()
        # Main loop
        uita.loop.create_task(uita.server.start(
            config.bot.database,
            config,
            origins=[websockets.Origin(uita.utils.build_client_url(config))],
            loop=uita.loop
        ))
        uita.loop.create_task(uita.bot.start(config.discord.token))
        uita.loop.run_forever()
    except KeyboardInterrupt:
        pass
    except uita.exceptions.MalformedConfig:
        log.fatal("Expected config structure did not match {}".format(uita.utils.config_file()))
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
        finally:
            # Additional cleanup to handle buggy asyncio cleanup
            for task in task_list:
                del task
        # Clear cache folder
        uita.loop.run_until_complete(uita.utils.prune_cache_dir())
        # Finalize shutdown
        uita.loop.close()
