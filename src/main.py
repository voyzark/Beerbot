import sys
import discord
import logging
import os
from mongodbstore import MongoDbStore, TerrorZone
from utils import next_monday, format_german
from datetime import timedelta
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Lod Config from environment
# dotenv.load_dotenv()
CLIENT_TOKEN = os.getenv("CLIENT_TOKEN")
ANNOUNCEMENT_GUILDS_TZ = os.getenv("ANNOUNCEMENT_GUILD").split(',')
ANNOUNCEMENT_CHANNELS_TZ = os.getenv("ANNOUNCEMENT_CHANNEL").split(',')
ANNOUNCEMENT_GUILDS_DATE = os.getenv("ANNOUNCEMENT_GUILD_DATE").split(',')
ANNOUNCEMENT_CHANNELS_DATE = os.getenv("ANNOUNCEMENT_CHANNEL_DATE").split(',')
LOG_LEVEL = os.getenv("LOG_LEVEL")

MONGO_DB_CONNECTION = os.getenv("MONGO_DB_CONNECTION", "mongodb://localhost:27017/")
MONGO_DB_DATABASE = os.getenv("MONGO_DB_DATABASE", "d2tz")
MONGO_DB_COLLECTION = os.getenv("MONGO_DB_COLLECTION", "tz-history")


# Logging
logging.basicConfig(
        stream=sys.stdout,
        level=LOG_LEVEL,
        format="[%(asctime)s] :: %(name)s :: %(levelname)s :: %(message)s", 
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# Global Variables
logger = logging.getLogger('beerbot')
intents = discord.Intents.default()
client = discord.Client(intents=intents)
last_terrorzone = os.getenv('BEERBOT_LAST_ZONE') or None
zone_announced = last_terrorzone is not None

tz_store = MongoDbStore(MONGO_DB_CONNECTION, MONGO_DB_DATABASE, MONGO_DB_COLLECTION)


@client.event
async def on_ready():
    logger.info(f'{client.user} has connected to Discord')
    
    scheduler = AsyncIOScheduler(timezone="Europe/Berlin")
    
    cron_trigger_tz = IntervalTrigger(seconds=30)
    scheduler.add_job(client.dispatch, cron_trigger_tz, ["tz_updated"])
    
    cron_trigger_sr_date = CronTrigger.from_crontab("30 20 * * 5") # run every thursday at 20:30
    scheduler.add_job(client.dispatch, cron_trigger_sr_date, ["speedrun_date_announcement"])
    
    scheduler.start()


@client.event
async def on_tz_updated():    
    logger.debug("Checking for updated zones")    
    await client.wait_until_ready()
    
    zones = sorted(
        await tz_store.get_unnanounced(),
        key=lambda zone: zone.time
    )
    
    # if len(messages) == 0:
    #     logger.info("No new zones to announce")
    #     return
    
    if channels := get_announcement_channels_tz():
        for channel in channels:
            for zone in zones:
                message = f"<t:{int(zone.time.timestamp())}:f> **{zone.name}**"
                logger.info(f'Announcing TZ: {message} in channel: "{channel.name}"@"{channel.guild.name}"')
                await channel.send(message)
                await tz_store.update(TerrorZone(name=zone.name, act=zone.act, time=zone.time, announced=True))
    else:
        logger.error("Found no channel to announce")


@client.event
async def on_speedrun_date_announcement():
    start = next_monday() + timedelta(hours=20)
    channels = get_announcement_channels_date()
    
    for i in range(1, 7):
        message = format_german(start + timedelta(days=i))
        logger.info("Announcing Speedrun dates")
        for channel in channels:
            msg = await channel.send(message)
            await msg.add_reaction("👍")
            await msg.add_reaction("👎")
            await msg.add_reaction("🤷‍♂️")


@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    logger.debug("Reaction added")
    
    if payload.user_id == client.user.id:
        logger.debug("Ignore our own reaction")
        return
    
    chan = await client.fetch_channel(payload.channel_id)
    msg = await chan.fetch_message(payload.message_id)    
    
    for reaction in msg.reactions:
        if reaction.count > 3 and reaction.me:
            logger.debug(f"Removing my own {reaction.emoji}")
            await reaction.remove(client.user)


def get_announcement_channels_tz() -> list[discord.guild.TextChannel]:
    guilds = [guild for guild in client.guilds if guild.name in ANNOUNCEMENT_GUILDS_TZ]
    channels = []
    for guild in guilds:
        channels += [chan for chan in guild.channels if chan.name in ANNOUNCEMENT_CHANNELS_TZ]

    return channels


def get_announcement_channels_date() -> list[discord.guild.TextChannel]:
    guilds = [guild for guild in client.guilds if guild.name in ANNOUNCEMENT_GUILDS_DATE]
    channels = []
    for guild in guilds:
        channels += [chan for chan in guild.channels if chan.name in ANNOUNCEMENT_CHANNELS_DATE]

    return channels


client.run(CLIENT_TOKEN)
