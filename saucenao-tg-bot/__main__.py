import os
import json
from argparse import ArgumentParser


def verify_dict(scheme: dict, dict_to_verify: dict):
    """
    Takes dict example sheme and checks if given dict matches.
    Is not super flexible and doesn't cover edge cases but does the job
    """
    for key, scheme_value in scheme.items():
        if key not in dict_to_verify:
            raise MyValueError(f'Given dict dont have {key} key')
        if type(dict_to_verify[key]) != type(scheme_value):
            raise MyValueError(
                f'{key} has type [{type(dict_to_verify[key]).__name__}] ' +\
                f'insetead of [{type(scheme_value).__name__}]')
        verified_value = dict_to_verify[key]
        if type(scheme_value) == list and len(scheme_value) != 0:
            scheme_list_obj_type = type(scheme_value[0])
            if type(verified_value[0]) != scheme_list_obj_type:
                raise MyValueError(
                    f'{key} list object has type [{type(verified_value[0]).__name__}] ' +\
                    f'instead of [{scheme_list_obj_type.__name__}]')
        elif type(scheme_value) == dict:
            verify_dict(scheme_value, verified_value)

class MyValueError(ValueError):
    message: str
    def __init__(self, *args, **kargs):
        if len(args) != 0:
            self.message = args[0]
        super(*args[1:], **kargs)


def main():
    """
    Launch bot using json config file if
    """
    arg_parser = ArgumentParser()
    arg_parser.add_argument("config_file_path", type=str,
                            help="path to json file with config like example")
    args = arg_parser.parse_args()
    config_file_path = args.config_file_path

    if not os.path.isfile(config_file_path):
        print("Invalid config file path")
        return
    with open(config_file_path, 'r') as file:
        try:
            config = json.load(file)
        except json.JSONDecodeError:
            print('You provided incorrect json file')
    with open('example_config.json', 'r') as file:
        config_scheme = json.load(file)
    try:
        verify_dict(config_scheme, config)
    except MyValueError as exception:
        print('Your config dont match example one:')
        print(exception.message)
        return

    sauce_nao_bot = SauceNaoBot(*BOT_CONFIGS.values())
    sauce_nao_bot.start()

main()
