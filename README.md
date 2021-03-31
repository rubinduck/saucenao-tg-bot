# About
Telegram bot to access SauceNAO.com functionality for searching image source

# How to launch
Install dependencies from requrments.txt. Put config variables to enviroment variables or to .json config file. 
Config variables:

- api_key - saucenao api key
- token - telegram bot api token
- download_dir - dir to save temporary image files during work ("" to create new folder automaticly at launch place)
- minimal_similarity - value from 0 to 1 to, all result with sumilari lower than it will not count

Example of .json config is in example_config.json
Launched with `python bot.py` or `python --config-file <path-to-config-file.json>` if json config file is used instead of enviroment variables.

# Usage
To use a bot just send picture you want get source as photo or as file