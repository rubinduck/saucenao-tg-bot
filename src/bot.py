"""
Bot providing ability to search images using saucenao.com inside telegram
"""

import os
import json
from typing import List


from telegram import Bot, Update
from telegram.ext import CallbackContext, Updater, MessageHandler, Filters

from saucenao_api import SauceNao, BasicSauce


class RequestResult:
    def __init__(self, photo_url: str, text: str):
        self.photo_url = photo_url
        self.text = text

    def __str__(self):
        return f"{self.text}\n{str(self.photo)}"


class SauceNaoBot:
    """
    Class incapsulating logic and objects
    for work of telegram sausenao search bot
    """
    def __init__(self, token: str,
                 save_folder_path: str,
                 minimal_similarity: float):
        self.bot = Bot(token)
        self.updater = Updater(token=token, use_context=True)
        self.download_folder = save_folder_path

        self.init_handlers()
        self.request_result_provider = RequestResultProvider(minimal_similarity)

    def init_handlers(self):
        """
        method creates handlers for message types we are interested in
        """
        photo_handler = MessageHandler(
            Filters.photo,
            self.download_photo)
        image_file_handler = MessageHandler(
            Filters.document.category("image/"),
            self.download_image_file)
        self.updater.dispatcher.add_handler(photo_handler)
        self.updater.dispatcher.add_handler(image_file_handler)

    def start(self):
        self.updater.start_polling()

    def stop(self):
        self.updater.stop()


    def download_photo(self, update: Update, context: CallbackContext):
        """
        method for photos send compressed
        """
        # telegram provides 3 photo versions from most compressed to most
        # the most quality one, which is used here for search
        photo_dict = update.message.photo[-1]
        photo_id = photo_dict.file_id
        file_name = f"{photo_dict.file_unique_id}.jpg"
        file_path = self.download_file(photo_id, file_name)
        self.process_request(update, file_path)

    def download_image_file(self, update: Update, context: CallbackContext):
        """
        method for images sent as file
        """
        file_dict = update.message.document
        file_id = file_dict.file_id
        # mime_type looks like image/someformat
        file_format = file_dict.mime_type.split('/')[1]
        file_name = f"{file_dict.file_unique_id}.{file_format}"
        file_path = self.download_file(file_id, file_name)
        self.process_request(update, file_path)

    def download_file(self, file_id: str, file_name: str) -> str:
        """
        download file with certain id using telegram api and save to folder
        mathced on class initialization
        """
        file_obj = self.bot.get_file(file_id)
        file_path = os.path.join(self.download_folder, file_name)
        file_obj.download(file_path)
        return file_path

    def process_request(self, update: Update, img_path: str):
        """
        process user requets (photo), send result to user
        """
        result = self.request_result_provider.provide_response(img_path)
        os.remove(img_path)
        chat_id = update.message.chat_id
        self.post_request_resutls(chat_id, result)


    def post_request_resutls(self, chat_id: str,
                             request_results: List[RequestResult]):
        """
        send results to user throught bot
        """
        if request_results == []:
            self.bot.send_message(chat_id=chat_id, text="Nothing found(")
        for res in request_results:
            self.bot.send_photo(
                chat_id=chat_id,
                photo=res.photo_url,
                caption=res.text)





class RequestResultProvider:
    def __init__(self, minimal_similarity):
        self.MINIMUM_SIMULARITY = minimal_similarity
        self.sauce_api = SauceNao()

    def provide_response(self, path_to_file: str) -> List[RequestResult]:
        """
        method providing saucenao results for given file
        """
        with open(path_to_file, "rb") as file:
            request_results = self.sauce_api.from_file(file)
        responses = []
        for result in request_results:
            if result.similarity >= self.MINIMUM_SIMULARITY:
                responses.append(self.gen_response_obj(result))

        return responses

    def gen_response_obj(self, response: BasicSauce) -> RequestResult:
        """
        method generating RequestResult, suitable to be sent by bot from api-
        provided data
        """
        text = f"{response.similarity}\n"
        if response.url is not None:
            text += "\n".join(response.url)
        else:
            text += response.index_name
            text += response.author if response.author is not None else ""

        thumbnail_url = response.thumbnail
        return RequestResult(thumbnail_url, text)


def main():
    with open("real_config.json", "r") as file:
        configs = json.load(file)
    TOKEN = configs["token"]
    MINIMUM_SIMULARITY = configs["minimal_similarity"]
    DIR = configs["download_dir"]
    if DIR == "":
        if not os.path.exists("images"):
            os.makedirs("images")
        DIR = "images"

    sauce_nao_bot = SauceNaoBot(TOKEN, DIR, MINIMUM_SIMULARITY)
    sauce_nao_bot.start()


if __name__ == "__main__":
    main()
