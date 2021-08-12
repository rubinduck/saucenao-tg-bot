#!/bin/bash
# move to script location
cd "$(dirname "$0")"
# kill bot if it is running
pkill --full "python saucenao-tg-bot"
# set up venv
if [ -d "venv" ]; then
	rm -r venv
fi
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# if config file path is not passed, use default name
if [ -z "$1" ]; then
	config_path="config.json"
else
	config_path="$1"
fi
python saucenao-tg-bot "$config_path" &
