import os
from dataclasses import dataclass


def load_config() -> 'Config':
    client_token = os.getenv("CLIENT_TOKEN")
    announcement_guilds_tz = os.getenv("ANNOUNCEMENT_GUILD", "").split(',')
    announcement_channels_tz = os.getenv("ANNOUNCEMENT_CHANNEL", "").split(',')
    announcement_guilds_date = os.getenv("ANNOUNCEMENT_GUILD_DATE", "").split(',')
    announcement_channels_date = os.getenv("ANNOUNCEMENT_CHANNEL_DATE", "").split(',')
    log_level = os.getenv("LOG_LEVEL", "INFO")
    mongo_db_connection = os.getenv("MONGO_DB_CONNECTION", "mongodb://localhost:27017/")
    mongo_db_database = os.getenv("MONGO_DB_DATABASE", "d2tz")
    mongo_db_collection = os.getenv("MONGO_DB_COLLECTION", "tz-history")
    cron_trigger_sr_date = os.getenv("CRON_TRIGGER_SR_DATE", "30 20 * * 6")  # every saturday at 20:30

    return Config(
        client_token=client_token,
        announcement_guilds_tz=announcement_guilds_tz,
        announcement_channels_tz=announcement_channels_tz,
        announcement_guilds_date=announcement_guilds_date,
        announcement_channels_date=announcement_channels_date,
        log_level=log_level,
        mongo_db_connection=mongo_db_connection,
        mongo_db_database=mongo_db_database,
        mongo_db_collection=mongo_db_collection,
        cron_trigger_sr_date=cron_trigger_sr_date
    )


@dataclass(frozen=True)
class Config:
    client_token: str
    announcement_guilds_tz: list[str]
    announcement_channels_tz: list[str]
    announcement_guilds_date: list[str]
    announcement_channels_date: list[str]
    log_level: str
    mongo_db_connection: str
    mongo_db_database: str
    mongo_db_collection: str
    cron_trigger_sr_date: str
