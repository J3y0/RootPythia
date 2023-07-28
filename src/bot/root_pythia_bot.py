"""The bot module, which handles discord interface"""

from os import getenv
import sys
import logging

import discord
from discord.ext import commands

from api.rootme_api import RootMeAPIManager
from api.rate_limiter import RateLimiter
from bot.root_pythia_cogs import RootPythiaCommands
from bot.dummy_db_manager import DummyDBManager


CHANNEL_ID = getenv("CHANNEL_ID")


def craft_intents():
    """Function that enables necessary intents for the bot"""

    # Disable everything
    intents = discord.Intents.none()
    # enable guild related events
    # More info: https://docs.pycord.dev/en/stable/api/data_classes.html#discord.Intents.guilds
    intents.guilds = True

    # Warning: message_content is a privileged intents
    # you must authorize it in the discord dev portal https://discord.com/developers/applications
    # enbale message_content privilegied intent to enable commands
    # More info: https://docs.pycord.dev/en/stable/api/data_classes.html#discord.Intents.message_content
    intents.message_content = True

    # enable guild messages related events
    # More info: https://docs.pycord.dev/en/stable/api/data_classes.html#discord.Intents.guild_messages
    intents.guild_messages = True
    
    return intents


########### Create bot object #################
_DESCRIPTION = (
    "RootPythia is a Discord bot fetching RootMe API to notify everyone"
    "when a user solves a new challenge!"
)
_PREFIX = "!"
_INTENTS = craft_intents()

BOT = commands.Bot(command_prefix=_PREFIX, description=_DESCRIPTION, intents=_INTENTS, help_command=commands.DefaultHelpCommand())

# Create Bot own logger, each Cog will also have its own
BOT.logger = logging.getLogger(__name__)


########### Setup bot events response ###############


@BOT.event
async def on_ready():
    # is this call secure??
    logging.debug("channel id: %s", CHANNEL_ID)

    # Create Rate Limiter, API Manager, and DB Manager objects
    rate_limiter = RateLimiter()
    api_manager = RootMeAPIManager(rate_limiter)
    db_manager = DummyDBManager(api_manager)

    # Fetch main channel and send initialization message
    BOT.channel = await BOT.fetch_channel(CHANNEL_ID)
    await BOT.channel.send("Channel initliazed")

    # Register cogs
    await BOT.add_cog(RootPythiaCommands(BOT, db_manager))


@BOT.event
async def on_error(event, *args, **kwargs):
    if event == "on_ready":
        BOT.logger.error(
            "Event '%s' failed (probably from invalid channel ID), close connection and exit...",
            event,
        )
        await BOT.close()
        sys.exit(1)
    else:
        # maybe this call is too intrusive/verbose...
        await BOT.channel.send(f"{event} event failed, please check logs for more details")

        BOT.logger.exception("Unhandled exception in '%s' event", event)
