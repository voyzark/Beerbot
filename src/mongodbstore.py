from dataclasses import dataclass
from datetime import datetime

import pymongo
import pymongo.collection
import pymongo.database

from utils import round_down_half_hour


@dataclass(frozen=True)
class TerrorZone:
    name: str
    act: int
    time: datetime
    announced: bool

    def __str__(self) -> str:
        return f"TZ :: {self.time.strftime('%Y-%m-%d %H:%M')} :: {self.name}"

    def __repr__(self) -> str:
        return self.__str__()


class MongoDbStore():
    connection_string: str
    database_name: str
    collection_name: str
    mongo_client: pymongo.MongoClient
    mongo_database: pymongo.database.Database
    mongo_collection: pymongo.collection.Collection

    def __init__(self, db_connection: str, database: str, collection: str) -> None:
        super().__init__()
        self.connection_string = db_connection
        self.database_name = database
        self.collection_name = collection

        self.mongo_client = pymongo.MongoClient(self.connection_string)
        self.mongo_database = self.mongo_client[self.database_name]
        self.mongo_collection = self.mongo_database[self.collection_name]

    async def get_by_time(self, time: datetime) -> TerrorZone:
        time = round_down_half_hour(time)
        tz = self.mongo_collection.find_one({"time": time})
        if tz is None:
            return None
        return TerrorZone(name=tz["name"], act=tz["act"], time=tz["time"], announced=tz["announced"])

    async def update(self, zone: TerrorZone) -> None:
        self.mongo_collection.update_one({"time": zone.time, "name": zone.name}, {"$set": zone.__dict__})

    async def set(self, zone: TerrorZone) -> None:
        if self.mongo_collection.find_one({"time": zone.time, "name": zone.name}) is None:
            return self.mongo_collection.insert_one(zone.__dict__)
        else:
            return self.mongo_collection.update_one({"time": zone.time, "name": zone.name}, {"$set": zone.__dict__})

    async def set_if_unset(self, zone: TerrorZone) -> bool:
        if self.mongo_collection.find_one({"time": zone.time, "name": zone.name}) is None:
            self.mongo_collection.insert_one(zone.__dict__)
            return True
        else:
            return False

    async def get_unnanounced(self) -> list[TerrorZone]:
        tzs = self.mongo_collection.find({"announced": False})
        return [TerrorZone(name=tz["name"], act=tz["act"], time=tz["time"], announced=tz["announced"]) for tz in tzs]
