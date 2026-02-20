"""Discord bot for managing beer-related announcements and terror zone notifications."""

import asyncio
import logging
from datetime import timedelta
from typing import Any

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from config import Config
from mongodbstore import MongoDbStore, TerrorZone
from utils import format_german, next_monday


class BeerBot(discord.Client):
    """
    A Discord bot that manages terror zone announcements and speedrun date scheduling.

    This bot monitors terror zones from a MongoDB store and announces them in designated
    Discord channels. It also handles weekly speedrun date announcements with reaction-based
    polling.
    """

    def __init__(self, config: Config, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the BeerBot client.

        Args:
            config: Configuration object containing:
                - mongo_db_connection: MongoDB connection string
                - mongo_db_database: Database name
                - mongo_db_collection: Collection name
                - announcement_guilds_tz: List of guild names for TZ announcements
                - announcement_channels_tz: List of channel names for TZ announcements
                - announcement_guilds_date: List of guild names for date announcements
                - announcement_channels_date: List of channel names for date announcements
            *args: Additional positional arguments for discord.Client
            **kwargs: Additional keyword arguments for discord.Client
        """
        kwargs.setdefault('intents', discord.Intents.default())

        super().__init__(*args, **kwargs)
        self.config = config
        self.tz_store = MongoDbStore(
            config.mongo_db_connection,
            config.mongo_db_database,
            config.mongo_db_collection
        )
        self.scheduler: AsyncIOScheduler | None = None
        self.logger = logging.getLogger('beerbot')
        self.is_updating_zones = False

    async def on_ready(self) -> None:
        """
        Handle the bot ready event.

        Called when the bot has successfully connected to Discord. Initializes the
        scheduler with two jobs:
        - Terror zone check every 15 seconds
        - Speedrun date announcement every Saturday at 20:30
        """
        self.logger.info('%s has connected to Discord', self.user)

        if self.scheduler is not None:
            self.scheduler.remove_all_jobs()
        else:
            self.scheduler = AsyncIOScheduler(timezone="Europe/Berlin")

        cron_trigger_tz = IntervalTrigger(seconds=15)
        self.scheduler.add_job(self.dispatch, cron_trigger_tz, ["tz_updated"])

        cron_trigger_sr_date = CronTrigger.from_crontab(self.config.cron_trigger_sr_date)
        self.scheduler.add_job(self.dispatch, cron_trigger_sr_date, ["speedrun_date_announcement"])

        self.scheduler.start()

    async def on_tz_updated(self) -> None:
        """
        Handle terror zone update events.

        Checks for unannounced terror zones in the database and posts them to
        configured announcement channels. Marks zones as announced after posting.
        This is triggered every 15 seconds by the scheduler.
        """
        if self.is_updating_zones:
            self.logger.debug("Already updating zones, skipping this run")
            return

        try:
            self.is_updating_zones = True
            await self._update_zones()
        finally:
            self.is_updating_zones = False

    async def _update_zones(self) -> None:
        self.logger.debug("Checking for updated zones...")
        await self.wait_until_ready()

        zones = sorted(
            await self.tz_store.get_unnanounced(),
            key=lambda zone: zone.time
        )

        if len(zones) == 0:
            self.logger.debug("No new zones to announce...")
            return

        if channels := self.get_announcement_channels_tz():
            for channel in channels:
                for zone in zones:
                    message = f"<t:{int(zone.time.timestamp())}:f> **{zone.name}**"
                    self.logger.info('Announcing TZ: %s in channel: "%s"@"%s"', message, channel.name, channel.guild.name)
                    await channel.send(message)
                    await self.tz_store.update(TerrorZone(name=zone.name, act=zone.act, time=zone.time, announced=True))
                    await asyncio.sleep(1) # avoid hitting rate limits when announcing multiple zones
        else:
            self.logger.error("no channel to announce the zones in")

    async def on_speedrun_date_announcement(self) -> None:
        """
        Handle speedrun date announcement events.

        Posts 6 consecutive dates starting from next Monday at 20:00 to configured
        announcement channels. Each message gets three reaction options for voting:
        👍 (yes), 👎 (no), and 🤷‍♂️ (maybe).
        This is triggered every Saturday at 20:30.
        """
        start = next_monday() + timedelta(hours=20)
        channels = self.get_announcement_channels_date()

        if len(channels) == 0:
            self.logger.error("no channel to announce the speedrun dates in")
            return

        for i in range(1, 7):
            message = format_german(start + timedelta(days=i))
            self.logger.info("Announcing Speedrun dates")
            for channel in channels:
                msg = await channel.send(message)
                await msg.add_reaction("👍")
                await msg.add_reaction("👎")
                await msg.add_reaction("🤷‍♂️")

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """
        Handle reaction add events.

        Monitors reactions on bot messages and removes the bot's own reactions
        when a reaction reaches more than 3 users. This prevents the bot's vote
        from influencing polls.

        Args:
            payload: Discord reaction event payload containing user, message, and reaction info.
        """
        self.logger.debug("Reaction added")

        if payload.user_id == self.user.id:
            self.logger.debug("Ignore our own reaction")
            return

        chan = await self.fetch_channel(payload.channel_id)
        msg = await chan.fetch_message(payload.message_id)

        for reaction in msg.reactions:
            if reaction.count > 3 and reaction.me:
                self.logger.debug("Removing my own %s", reaction.emoji)
                await reaction.remove(self.user)

    def get_announcement_channels_tz(self) -> list[discord.TextChannel]:
        """
        Get list of Discord channels for terror zone announcements.

        Filters guilds and channels based on configuration settings to find
        all channels where terror zone announcements should be posted.

        Returns:
            List of Discord TextChannel objects for TZ announcements.
        """
        guilds = [guild for guild in self.guilds if guild.name in self.config.announcement_guilds_tz]
        channels = []
        for guild in guilds:
            channels += [chan for chan in guild.channels if chan.name in self.config.announcement_channels_tz]
        return channels

    def get_announcement_channels_date(self) -> list[discord.TextChannel]:
        """
        Get list of Discord channels for speedrun date announcements.

        Filters guilds and channels based on configuration settings to find
        all channels where speedrun date announcements should be posted.

        Returns:
            List of Discord TextChannel objects for date announcements.
        """
        guilds = [guild for guild in self.guilds if guild.name in self.config.announcement_guilds_date]
        channels = []
        for guild in guilds:
            channels += [chan for chan in guild.channels if chan.name in self.config.announcement_channels_date]
        return channels
