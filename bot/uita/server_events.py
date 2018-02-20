from uita import server

import logging
log = logging.getLogger(__name__)


@server.on_message("play.url")
async def auth_check(event):
    log.debug("play.url event:{}".format(event))
    try:
        import asyncio
        log.debug("sleep start")
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        log.debug("sleep cancelled")
    finally:
        log.debug("sleep end")
