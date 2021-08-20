"""
Bot providing ability to search images using saucenao.com inside telegram
"""

import os
import logging
import traceback
from typing import List
from dataclasses import dataclass
from datetime import datetime

from telegram import Bot, Update, InputMediaPhoto
from telegram.ext import CallbackContext, Updater, MessageHandler, Filters
from saucenao_api import SauceNao, BasicSauce


@dataclass
class RequestResult:
    photo_url: str
    text: str


def catch_exceptions(message_handler):
    """universal error catcher for any new message hanlder"""
    def decorated_method(self, update: Update, context: CallbackContext):
        try:
            message_handler(self, update, context)
        except Exception as ex:
            logging.error(to_str(ex))
            chat_id = update.message.chat_id
            self.bot.send_message(chat_id=chat_id, text='Something went wrong on server')
    return decorated_method

def to_str(ex: Exception) -> str:
    return ''.join(traceback.format_exception(type(ex), ex, ex.__traceback__))

# TODO make logging better
def log_requests(message_handler):
    def decorated_method(self, update: Update, context: CallbackContext):
        message = update.message
        if message.forward_date:
            msg_time = message.forward_date
        else:
            msg_time = message.date
        logging.info(msg_time.isoformat())
        message_handler(self, update, context)
    return decorated_method

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
        logging.info('Launched bot')

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

    @log_requests
    @catch_exceptions
    def handle_photo(self, update: Update, context: CallbackContext):
        """method for images sent compressed"""
        # telegram provides 3 photo versions from most compressed
        # to the most quality one, which is used here for search
        photo_id = update.message.photo[-1].file_id
        file_name = f"{photo_id}.jpg"
        self.process_request(update, photo_id, file_name)

    @log_requests
    @catch_exceptions
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
