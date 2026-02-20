"""Main entry point for the BeerBot Discord bot."""

import logging

from beerbot import BeerBot
from config import load_config


def main() -> None:
    config = load_config()

    logging.basicConfig(
        level=config.log_level,
        format="\033[90m%(asctime)s \033[36m%(name)s \033[35m%(levelname)s \033[0m%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    # This logger will spam us, when we keep it in INFO
    logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)

    client = BeerBot(config)
    client.run(config.client_token)


if __name__ == "__main__":
    main()
