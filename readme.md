# Beerbot
A discord bot, that announces the current terror zone using the d2runewizard api.
For obtaining access to the api please refer to https://d2runewizard.com/integration


# Usage
1. Create a .env file filling the following variables:
> BEERBOT_CLIENT_TOKEN=\<Discord client token\>  
> BEERBOT_API_TOKEN=\<d2runewizard api token\>  
> BEERBOT_ANNOUNCEMENT_GUILD=\<list of comma separated discord servers\>  
> BEERBOT_ANNOUNCEMENT_CHANNEL=\<list of comma separated channels\>  
> BEERBOT_ENDPOINT_TZ=\<endpoint, currently: https://d2runewizard.com/api/terror-zone\>  
> BEERBOT_LOG_FILE=\<name of the log file\>  
> BEERBOT_LOG_LEVEL=\<log level\>  
> BEERBOT_D2R_CONTACT=\<contact information (see fair use poilicy of the d2runewizard api)\>  
> BEERBOT_D2R_PLATFORM=\<Discord, Telegram, Whatsapp, ...  (see fair use poilicy of the d2runewizard api)\>  
> BEERBOT_D2R_REPO=\<link to the public repo of the bot (see fair use poilicy of the d2runewizard api)\>  
> BEERBOT_LAST_ZONE=\<optional, useful to avoid announcing the same tz twice after a restart\>  

2. Create a venv (optional but recommended)
3. Install the requirements
4. Run the bot

# What's up with the name?
The bot was created for personal use on a discord server called beerbaal, so this was the only logical choice