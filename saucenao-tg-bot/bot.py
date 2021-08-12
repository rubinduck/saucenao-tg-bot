"""
Bot providing ability to search images using saucenao.com inside telegram
"""

import os
import json
from typing import List
from dataclasses import dataclass

from telegram import Bot, Update, InputMediaPhoto
from telegram.ext import CallbackContext, Updater, MessageHandler, Filters
from saucenao_api import SauceNao, BasicSauce


@dataclass
class RequestResult:
    photo_url: str
    text: str


class SauceNaoBot:
    def __init__(self,
                 token: str,
                 api_key: str,
                 save_folder_path: str,
                 minimal_similarity: float):
        self.bot = Bot(token)
        self.updater = Updater(token=token, use_context=True)
        self.download_folder = save_folder_path

        self.init_message_handlers()
        self.request_result_provider = RequestResultProvider(api_key,
                                                             minimal_similarity)

    def init_message_handlers(self):
        photo_handler = MessageHandler(
            Filters.photo,
            self.handle_photo)
        image_file_handler = MessageHandler(
            Filters.document.category("image/"),
            self.handle_image_file)
        self.updater.dispatcher.add_handler(photo_handler)
        self.updater.dispatcher.add_handler(image_file_handler)

    def start(self):
        self.updater.start_polling()

    def stop(self):
        self.updater.stop()

    def handle_photo(self, update: Update, context: CallbackContext):
        """method for images sent compressed"""
        # telegram provides 3 photo versions from most compressed
        # to the most quality one, which is used here for search
        photo_id = update.message.photo[-1].file_id
        file_name = f"{photo_id}.jpg"
        self.process_request(update, photo_id, file_name)

    def handle_image_file(self, update: Update, context: CallbackContext):
        """method for images sent as file"""
        file_dict = update.message.document
        file_id = file_dict.file_id
        # mime_type looks like image/someformat
        file_format = file_dict.mime_type.split('/')[1]
        file_name = f"{file_id}.{file_format}"
        self.process_request(update, file_id, file_name)

    def process_request(self, update: Update, file_id: str, file_name: str):
        """process user requets (photo), send result to user"""
        img_path = self.download_file(file_id, file_name)
        result = self.request_result_provider.provide_response(img_path)
        self.delete_file(img_path)
        chat_id = update.message.chat_id
        self.post_request_results(chat_id, result)

    def download_file(self, file_id: str, file_name: str) -> str:
        """download file with file_id to self.download_folder"""
        file_obj = self.bot.get_file(file_id)
        file_path = os.path.join(self.download_folder, file_name)
        file_obj.download(file_path)
        return file_path

    def delete_file(self, file_path: str):
        os.remove(file_path)

    def post_request_results(self, chat_id: str, results: List[RequestResult]):
        if results == []:
            self.bot.send_message(chat_id=chat_id, text="Nothing found(")
            return
        media = [InputMediaPhoto(r.photo_url) for r in results]
        # caption put to first media becouse tg shows only first caption
        caption = ("\n" + "-" * 50 + "\n").join(r.text for r in results)
        media[0].caption = caption
        self.bot.send_media_group(chat_id=chat_id, media=media)


class RequestResultProvider:
    def __init__(self, api_key: str, minimal_similarity: float):
        self.minimal_similarity = minimal_similarity
        self.sauce_api = SauceNao(api_key=api_key)

    def provide_response(self, path_to_file: str) -> List[RequestResult]:
        with open(path_to_file, "rb") as file:
            request_results = self.sauce_api.from_file(file)

        responses = [self.gen_response_obj(r) for r in request_results
                     if r.similarity >= self.minimal_similarity]
        return responses

    def gen_response_obj(self, response: BasicSauce) -> RequestResult:
        text = f"{response.similarity}\n"
        if response.urls != []:
            text += "\n".join(response.urls)
        else:
            text += f"Title:{response.title}\n" if response.title is not None else ""
            text += f"Author:{response.author}\n" if response.author is not None else ""
        thumbnail_url = response.thumbnail
        return RequestResult(thumbnail_url, text)




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
    from argparse import ArgumentParser

    arg_parser = ArgumentParser()
    arg_parser.add_argument("config-file-path", type=str,
                            help="path to json file with config like example")
    args = arg_parser.parse_args()

    BOT_CONFIGS = {"token": None,
                   "api_key": None,
                   "download_dir": None,
                   "minimal_simularity": None}

    config_file_path = args.config_file_path
    if not os.path.isfile(config_file):
        print("Invalid config file")
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
    except MyValueError:
        print('Your config dont match example one')
        return

    sauce_nao_bot = SauceNaoBot(*BOT_CONFIGS.values())
    sauce_nao_bot.start()

if __name__ == "__main__":
    main()
