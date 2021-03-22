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
    """
    Class incapsulating logic and objects
    for work of telegram sausenao search bot
    """
    def __init__(self, token: str,
                 api_key: str,
                 save_folder_path: str,
                 minimal_similarity: float):
        self.bot = Bot(token)
        self.updater = Updater(token=token, use_context=True)
        self.download_folder = save_folder_path

        self.init_handlers()
        self.request_result_provider = RequestResultProvider(api_key,
                                                             minimal_similarity)

    def init_handlers(self):
        """
        method creates handlers for message types we are interested in
        """
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
        """
        method for photos send compressed
        """
        # telegram provides 3 photo versions from most compressed
        # to the most quality one, which is used here for search
        photo_id = update.message.photo[-1].file_id
        file_name = f"{photo_id}.jpg"
        self.process_request(update, photo_id, file_name)

    def handle_image_file(self, update: Update, context: CallbackContext):
        """
        method for images sent as file
        """
        file_dict = update.message.document
        file_id = file_dict.file_id
        # mime_type looks like image/someformat
        file_format = file_dict.mime_type.split('/')[1]
        file_name = f"{file_id}.{file_format}"
        self.process_request(update, file_id, file_name)

    def process_request(self, update: Update, file_id: str, file_name: str):
        """
        process user requets (photo), send result to user
        """
        img_path = self.download_file(file_id, file_name)
        result = self.request_result_provider.provide_response(img_path)
        os.remove(img_path)
        chat_id = update.message.chat_id
        self.post_request_resutls(chat_id, result)

    def download_file(self, file_id: str, file_name: str) -> str:
        """
        download file with certain id using telegram api and save to folder
        mathced on class initialization
        """
        file_obj = self.bot.get_file(file_id)
        file_path = os.path.join(self.download_folder, file_name)
        file_obj.download(file_path)
        return file_path

    def post_request_resutls(self, chat_id: str,
                             request_results: List[RequestResult]):
        """
        send results to user throught bot
        """
        if request_results != []:
            media = [InputMediaPhoto(r.photo_url)
                     for r in request_results]
            # caption put to first media becouse tg shows only first caption
            caption = ("\n" + "-" * 50 + "\n").join(
                       r.text for r in request_results)
            media[0].caption = caption

            self.bot.send_media_group(chat_id=chat_id, media=media)
        else:
            self.bot.send_message(chat_id=chat_id, text="Nothing found(")



class RequestResultProvider:
    def __init__(self, api_key, minimal_similarity):
        self.MINIMUM_SIMULARITY = minimal_similarity
        self.sauce_api = SauceNao(api_key=api_key)

    def provide_response(self, path_to_file: str) -> List[RequestResult]:
        """
        method providing saucenao results for given image file
        """
        with open(path_to_file, "rb") as file:
            request_results = self.sauce_api.from_file(file)

        responses = [self.gen_response_obj(r) for r in request_results
                     if r.similarity >= self.MINIMUM_SIMULARITY]
        return responses

    def gen_response_obj(self, response: BasicSauce) -> RequestResult:
        """
        method generating RequestResult, suitable to be sent by bot from api-
        provided data
        """
        text = f"{response.similarity}\n"
        if response.urls != []:
            text += "\n".join(response.urls)
        else:
            text += f"Title:{response.title}\n" if response.title is not None else ""
            text += f"Author:{response.author}\n" if response.author is not None else ""

        thumbnail_url = response.thumbnail
        return RequestResult(thumbnail_url, text)

def main():
    """
    Launch bot using enviroment variables as config or json config file if
    it is specified as command line arg
    """
    from argparse import ArgumentParser

    arg_parser = ArgumentParser()
    arg_parser.add_argument("--config-file", type=str,
                            help="path to json file with config like example")
    args = arg_parser.parse_args()

    BOT_CONFIGS = {"TOKEN": None,
                   "API_KEY": None,
                   "DOWNLOAD_DIR": None,
                   "MINIMUM_SIMULARITY": None}

    config_file = args.config_file
    if config_file:
        if not os.path.isfile(config_file):
            print("Invalid config file")
            return
        with open(config_file, "r") as file:
            configs = json.load(file)
            for confg_name in BOT_CONFIGS:
                BOT_CONFIGS[confg_name] = configs[confg_name]
    else:
        for confg_name in BOT_CONFIGS:
            BOT_CONFIGS[confg_name] = os.environ.get(confg_name)
        BOT_CONFIGS["MINIMUM_SIMULARITY"] = float(BOT_CONFIGS["MINIMUM_SIMULARITY"])

    if BOT_CONFIGS["DOWNLOAD_DIR"] == "":
        if not os.path.exists("images"):
            os.makedirs("images")
        BOT_CONFIGS["DOWNLOAD_DIR"] = "images"
    sauce_nao_bot = SauceNaoBot(*BOT_CONFIGS.values())
    sauce_nao_bot.start()


if __name__ == "__main__":
    main()
