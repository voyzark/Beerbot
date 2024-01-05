import discord
import aiohttp
import logging
import dotenv
import os
import tzinfo
import asyncio
import dateutil
from datetime import datetime, timedelta
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Lod Config from environment
dotenv.load_dotenv()
CLIENT_TOKEN = os.getenv("BEERBOT_CLIENT_TOKEN")
API_TOKEN = os.getenv("BEERBOT_API_TOKEN")
ANNOUNCEMENT_GUILDS_TZ = os.getenv("BEERBOT_ANNOUNCEMENT_GUILD").split(',')
ANNOUNCEMENT_CHANNELS_TZ = os.getenv("BEERBOT_ANNOUNCEMENT_CHANNEL").split(',')
ANNOUNCEMENT_GUILDS_DATE = os.getenv("BEERBOT_ANNOUNCEMENT_GUILD_DATE").split(',')
ANNOUNCEMENT_CHANNELS_DATE = os.getenv("BEERBOT_ANNOUNCEMENT_CHANNEL_DATE").split(',')
ENDPOINT_TZ = os.getenv("BEERBOT_ENDPOINT_TZ")
ENDPOINT_TZINFO = os.getenv("BEERBOT_ENDPOINT_TZINFO")
LOG_FILE = os.getenv("BEERBOT_LOG_FILE")
LOG_LEVEL = os.getenv("BEERBOT_LOG_LEVEL")
D2R_CONTACT = os.getenv("BEERBOT_D2R_CONTACT")
D2R_PLATFORM = os.getenv("BEERBOT_D2R_PLATFORM")
D2R_REPO = os.getenv("BEERBOT_D2R_REPO")


# Logging
logging.basicConfig(
    filename=LOG_FILE, 
    filemode='a', 
    format='[%(asctime)s] %(levelname)8s | %(name)-22s :: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=LOG_LEVEL)

# Global Variables
logger = logging.getLogger('beerbot')
intents = discord.Intents.default()
client = discord.Client(intents=intents)
last_terrorzone = os.getenv('BEERBOT_LAST_ZONE') or None
zone_announced = last_terrorzone is not None


@client.event
async def on_ready():
    logger.info(f'{client.user} has connected to Discord')
    
    scheduler = AsyncIOScheduler(timezone="Europe/Berlin")
    
    cron_trigger_tz = CronTrigger.from_crontab("0,2,4,6,8 * * * *") # run every hour on minutes 0, 2, 4, 6, 8
    scheduler.add_job(client.dispatch, cron_trigger_tz, ["tz_updated"])
    
    cron_trigger_sr_date = CronTrigger.from_crontab("30 20 * * 3") # run every thursday at 20:30
    scheduler.add_job(client.dispatch, cron_trigger_sr_date, ["speedrun_date_announcement"])
    
    scheduler.start()


@client.event
async def on_tz_updated():    
    await asyncio.sleep(30)
    
    logger.debug(f"Checking for TZ update")
    
    global last_terrorzone
    global zone_announced
    
    zone, act, next_zone, next_act = None, None, None, None
    
    await client.wait_until_ready()   
    
    if tzs := await tzinfo.get_current_and_next_tz(ENDPOINT_TZINFO, logger):
        logger.debug(f"success using tzinfo: {tzs}")
        zone, act = tzs[0].zone, tzs[0].act
        next_zone, next_act = tzs[1].zone, tzs[1].act
    elif tz := await get_current_tz():
        try:
            zone = tz['terrorZone']['highestProbabilityZone']['zone']
            act = tz['terrorZone']['highestProbabilityZone']['act'][-1]
        except Exception as e:
            logger.error(f"error getting tz from runewizard api: {e}")
            return
    else:
        logger.error(f"could not get tz from any api")
        return
    

    message = f"Current TZ: **{zone}** (Act: {act})"
    if next_zone and next_act:
        message += f"\n> Next: `{next_zone} (Act: {next_act})`"

    if last_terrorzone == zone and zone_announced:
        logger.debug(f"TZ hasn't changed since we last checked. (before: {last_terrorzone}, now: {zone})")
        return
    else:
        logger.debug(f"TZ has changed since we last checked. (before: {last_terrorzone}, now: {zone})")
        last_terrorzone = zone
        zone_announced = False

    if channels := get_announcement_channels_tz():
        zone_announced = True
        for channel in channels:
            logger.info(f'Announcing TZ: {zone} in channel: "{channel.name}"@"{channel.guild.name}"')
            await channel.send(message)
    else:
        logger.error("Found no channel to announce")


@client.event
async def on_speedrun_date_announcement():
    start = dateutil.next_monday() + timedelta(hours=20)
    channels = get_announcement_channels_date()
    
    for i in range(1, 7):
        message = dateutil.format_german(start + timedelta(days=i))
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


async def get_current_tz():
    async with aiohttp.ClientSession() as session:
        async with session.get(ENDPOINT_TZ, 
                               params={"token": API_TOKEN}, 
                               headers={"D2R-Contact": D2R_CONTACT, "D2R-Platform": D2R_PLATFORM, "D2R-Repo": D2R_REPO}) as resp:
            if not resp.ok:
                logger.error(f"Failed to get current TZ! Response from api: {await resp.text()}")
                return None
            
            return await resp.json()


client.run(CLIENT_TOKEN)
