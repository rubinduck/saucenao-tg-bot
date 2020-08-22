import io
import os
import json
import urllib
from typing import List

from PIL import Image

from telegram import Bot, Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

from saucenao_api import SauceNao, BasicSauce

MINIMUM_SIMULARITY = 50

class SauceNaoBot:
    """
    Class incapsulating logic and objects
    for work of telegram sausenao search bot
    """
    def __init__(self, token: str, save_folder_path: str):
        self.bot = Bot(token)
        self.updater = Updater(token=token, use_context=True)
        self.download_folder = save_folder_path
        self.init_handlers()

    def init_handlers(self):
        """
        create handlers for message types we are interested in
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
        # the most quality one is getted here
        photo_dict = update.message.photo[-1]
        photo_id = photo_dict.file_id
        file_name = f"{photo_dict.file_unique_id}.jpg"
        self.download_file(photo_id, file_name)

    def download_image_file(self, update: Update, context: CallbackContext):
        """
        method for images sent as file
        """
        file_dict = update.message.document
        file_id = file_dict.file_id
        # mime_type looks like image/someformat
        file_format = file_dict.mime_type.split('/')[1]
        file_name = f"{file_dict.file_unique_id}.{file_format}"
        self.download_file(file_id, file_name)

    def download_file(self, file_id: str, file_name: str) -> str:
        """
        download file with certain id using telegram api and save to folder
        mathced on class initialization
        """
        file_obj = self.bot.get_file(file_id)
        file_path = os.path.join(self.download_folder, file_name)
        file_obj.download(file_path)
        return file_path



class RequestResult:
    def __init__(self, photo: Image, text: str):
        self.photo = photo
        self.text = text

    def __str__(self):
        return f"{self.text}\n{str(self.photo)}"


class RequestResultProvider:
    def __init__(self):
        self.sauce_api = SauceNao()

    def provide_response(self, path_to_file: str) -> List[RequestResult]:
        """
        method provide saucenao results for file
        """
        with open(path_to_file, "rb") as file:
            request_results = self.sauce_api.from_file(file)
        responses = []
        for result in request_results:
            if result.similarity >= MINIMUM_SIMULARITY:
                responses.append(self.gen_response_obj(result))

        return responses

    def gen_response_obj(response: BasicSauce) -> RequestResult:
        """
        method generating RequestResult, suitable to be sent by bot from api-
        provided data
        """
        text = f"\n{response.similarity}"
        if response.url is not None:
            text += "\n".join(response.url)
        else:
            text += response.index_name
            text += response.author if response.author is not None else ""

        thumbnail_url = response.thumbnail
        thumbnail_path = io.BytesIO(urllib.request.urlopen(thumbnail_url).read())
        thumbnail_object = Image.open(thumbnail_path)
        return RequestResult(thumbnail_object, text)


def main():
    with open("real_config.json", "r") as file:
        configs = json.load(file)
    TOKEN = configs["token"]
    DIR = configs["download_dir"]
    if DIR == "":
        if not os.path.exists("images"):
            os.makedirs("images")
        DIR = "images"

    sauce_nao_bot = SauceNaoBot(TOKEN, DIR)
    sauce_nao_bot.start()


if __name__ == "__main__":
    main()
