import logging
import telebot
import string
import os
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from django.utils import timezone
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files import File
from django.dispatch import receiver
from django.db.models import Q
from django.db.models.signals import post_save
from django.shortcuts import get_object_or_404
from datetime import datetime
from itertools import zip_longest
from .models import Channel
from .models import User
from .models import Message
from .tasks import process_telegram_update
from .conf import bot


logger = logging.getLogger(__name__)

user_context = {}


@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        try:
            update_data = request.body.decode('utf-8')
            process_telegram_update.delay(update_data)
            logger.info(f"Отримане оновлення з webhook: {update_data}")
            return HttpResponse('')
        except Exception as e:
            logger.error(f"Помилка обробки вебхуку: {str(e)}")


pending_join_requests = {}

@bot.chat_join_request_handler(func=lambda request: True)
def handle_join_request(request):
    chat_id = request.user_chat_id
    first_name = request.from_user.first_name
    channel_id = request.chat.id  # Отримати ідентифікатор каналу з запиту

    logger.info(f"Received join request from {first_name} for channel {channel_id}")

    pending_join_requests[chat_id] = channel_id

    try:
        channel, created = Channel.objects.get_or_create(channel_id=channel_id,
                                                         defaults={'name': f'Channel {channel_id}'})

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        confirm_button = types.KeyboardButton("/start")
        keyboard.add(confirm_button)

        bot.send_message(chat_id, f"Привет {first_name}, я антиспам бот нажмите '/start', чтобы присоединиться к каналу:",
                         reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error sending confirmation message: {str(e)}")

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name

    try:
        channel_id = pending_join_requests.get(chat_id)

        if channel_id:
            user, created = User.objects.update_or_create(user_id=chat_id, defaults={'username': first_name})

            channel = Channel.objects.get(channel_id=channel_id)
            user.channels.add(channel)

            bot.approve_chat_join_request(chat_id=channel_id, user_id=chat_id)
            logger.info(f"Користувач {first_name} успішно приєднався до каналу {channel_id}")

            bot.send_message(chat_id, f"Спасибо, {first_name}, вы успешно присоединились к каналу!")

            message = Message.objects.first()
            if message:
                bot.send_message(chat_id, message.text)

            del pending_join_requests[chat_id]
        else:
            bot.send_message(chat_id, "Не удалось найти канал для подключения.")
    except Exception as e:
        logger.error(f"Error adding user to the database or approving join request: {str(e)}")


