import json
import aiohttp
import logging
from datetime import datetime, timedelta

with open('TerrorZones.json', 'r') as f:
    tzs = {z['d2tz']: z for z in json.load(f)}


class Zone:
    time: datetime
    zone: str
    act: str

    def __init__(self, d: dict) -> None:
        self.time = datetime.fromtimestamp(d['time'])
        self.zone = tzs[d['zone']]['name']
        self.act = tzs[d['zone']]['act']

    def __str__(self) -> str:
        return f'{self.time} :: {self.zone}'
    
    def __repr__(self) -> str:
        return self.__str__()


async def get_all_zones(url: str, logger: logging.Logger) -> list[Zone]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                content = await response.text()
                data = json.loads(content)
                if data['status'] == 'ok':
                    return [Zone(i) for i in data['data']]
                else:
                    logger.error("tzinfo api appears to be down (Status: NOK)")
                    return None
    except Exception as e:
        logger.error(f"Error in tzinfo.get_all_zones: {e}")
        return None


async def get_current_and_next_tz(url: str, logger: logging.Logger):
    try:
        zones = await get_all_zones(url, logger)
        
        timestamp_current = datetime.now().replace(second=0, microsecond=0, minute=0)
        timestamp_next = timestamp_current + timedelta(hours=1)
        
        current_zone: Zone = next( filter(lambda z: z.time == timestamp_current, zones) )
        next_zone: Zone = next( filter(lambda z: z.time == timestamp_next, zones) )
        
        return current_zone, next_zone
    except Exception as e:
        logger.error(f"Error in tzinfo.get_current_and_next_tz: {e}")
        return None
