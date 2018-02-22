from uita import bot

import logging
log = logging.getLogger(__name__)


@bot.event
async def on_ready():
    log.debug("Bot connected to Discord")
