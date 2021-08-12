# About
Telegram bot to access SauceNAO.com functionality for searching image source

# How to launch
Requires python 3.7+\
Launch steps:
1. Put config variables (listed below and in exampel .json) to config.json file
2. Run `launch.sh` or `launch.sh <path-to-config-file>` if your config file
name is not default "config.json". If you are on windows or want to launch
manually follow next steps
3. Install dependencies from requirments.txt
4. run `python saucenao-tg-bot <path-to-config-file>` here

Config variables:
- api_key - saucenao api key
- token - telegram bot api token
- download_dir - dir to save temporary image files during work ("" to create new folder automaticly at launch place)
- minimal_similarity - value from 0 to 1 to, all result with sumilari lower than it will not count


# Usage
To use a bot just send picture you want get source as photo or as file