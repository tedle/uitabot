from uita import server

import logging
log = logging.getLogger(__name__)


@server.on_message("play.url")
async def auth_check(event):
    log.debug("play.url event:{}".format(event))
