import discord
import aiohttp
import logging
import dotenv
import os
import tzinfo
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Lod Config from environment
dotenv.load_dotenv()
CLIENT_TOKEN = os.getenv("BEERBOT_CLIENT_TOKEN")
API_TOKEN = os.getenv("BEERBOT_API_TOKEN")
ANNOUNCEMENT_GUILDS = os.getenv("BEERBOT_ANNOUNCEMENT_GUILD").split(',')
ANNOUNCEMENT_CHANNELS = os.getenv("BEERBOT_ANNOUNCEMENT_CHANNEL").split(',')
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
    cron_trigger = CronTrigger.from_crontab("3,5,7,9 * * * *") # run every hour on minutes 3, 5, 7, 9
    scheduler.add_job(client.dispatch, cron_trigger, ["tz_updated"])
    scheduler.start()


@client.event
async def on_tz_updated():    
    logger.debug(f"Checking for TZ update")
    
    global last_terrorzone
    global zone_announced
    
    await client.wait_until_ready()   
    
    if tzs := await tzinfo.get_current_and_next_tz(ENDPOINT_TZINFO, logger):
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
    

    message = f"The Terrorzone is now: **{zone}** (Act: {act})"
    if next_zone and next_act:
        message += f"\nThe next one probably is: **{next_zone}** (Act: {next_act})"

    if last_terrorzone == zone and zone_announced:
        logger.debug(f"TZ hasn't changed since we last checked. (before: {last_terrorzone}, now: {zone})")
        return
    else:
        logger.debug(f"TZ has changed since we last checked. (before: {last_terrorzone}, now: {zone})")
        last_terrorzone = zone
        zone_announced = False

    if channels := get_announcement_channels():
        zone_announced = True
        for channel in channels:
            logger.info(f'Announcing TZ: {zone} in channel: "{channel.name}"@"{channel.guild.name}"')
            await channel.send(message)
    else:
        logger.error("Found no channel to announce")


def get_announcement_channels() -> list[discord.guild.TextChannel]:
    guilds = [guild for guild in client.guilds if guild.name in ANNOUNCEMENT_GUILDS]
    channels = []
    for guild in guilds:
        channels += [chan for chan in guild.channels if chan.name in ANNOUNCEMENT_CHANNELS]

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
