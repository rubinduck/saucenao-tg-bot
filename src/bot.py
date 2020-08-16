import os
import json

from telegram import Bot, Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext


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

    def download_file(self, file_id: str, file_name: str):
        """
        download file with certain id using telegram api and save to folder
        mathced on class initialization
        """
        file_obj = self.bot.get_file(file_id)
        file_path = os.path.join(self.download_folder, file_name)
        file_obj.download(file_path)


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
