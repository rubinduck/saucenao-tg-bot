import os
import logging
from argparse import ArgumentParser

import yaml

from bot import SauceNaoBot


def is_config_right(config: dict, config_scheme: dict) -> bool:
    """checks if config mathes config_scheme"""
    if config.keys() != config_scheme.keys():
        return False
    for key in config_scheme:
        if type(config_scheme[key]) != type(config[key]):
            return False
    return True

def main():
    """Launch bot using config parametrs from provided file"""
    logging.basicConfig(filename='logs.log', level=logging.INFO)
    arg_parser = ArgumentParser()
    arg_parser.add_argument("config_file_path", type=str,
                            help="path to yaml file with config like example")
    args = arg_parser.parse_args()
    config_file_path = args.config_file_path

    if not os.path.isfile(config_file_path):
        print('Invalid config file path')
        return
    with open(config_file_path, 'r') as file:
        try:
            config = yaml.safe_load(file)
        except yaml.YAMLError:
            print('You provided incorrect yaml file')
    with open('example_config.yaml', 'r') as file:
        config_scheme = yaml.safe_load(file)
    if not is_config_right(config, config_scheme):
        print('Provided config file dont match example one')
        return

    sauce_nao_bot = SauceNaoBot(*config.values())
    sauce_nao_bot.start()

main()
