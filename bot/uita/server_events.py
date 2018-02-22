from uita import bot, server
import uita.message
import uita.types

import logging
log = logging.getLogger(__name__)


@server.on_message("server.list.get")
async def server_list_get(event):
    log.debug("server list get")
    discord_servers = list()
    for discord_server in bot.servers:
        discord_servers.append(uita.types.DiscordServer(discord_server.id, discord_server.name))
    discord_servers.append(uita.types.DiscordServer(
        "incredibly_fake", "FAKE SERVER - REMINDER TO CROSS REFERENCE USER SERVERS"
    ))
    await event.connection.socket.send(str(uita.message.ServerListSendMessage(discord_servers)))


@server.on_message("play.url")
async def play_url(event):
    log.debug("play.url event:{}".format(event))
    try:
        import asyncio
        log.debug("sleep start")
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        log.debug("sleep cancelled")
    finally:
        log.debug("sleep end")
