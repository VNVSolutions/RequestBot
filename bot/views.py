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


@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name

    args = message.text.split()[1:]

    if args:
        action, channel_id = args[0].split('_')
        if action == 'channel':
            channel, created = Channel.objects.get_or_create(channel_id=channel_id, defaults={'name': f'Channel {channel_id}'})

            try:
                user, created = User.objects.update_or_create(user_id=chat_id, defaults={'username': first_name})
                user.channels.add(channel)

                bot.approve_chat_join_request(channel_id, message.from_user.id)
                logger.info(f"Запит на приєднання від {first_name} до каналу {channel_id} успішно прийнятий")
            except Exception as e:
                logger.error(f"Error approving join request or adding user to the database: {str(e)}")
        else:
            bot.send_message(chat_id, "Предоставлена недействительная ссылка.")
    else:
        bot.send_message(chat_id, "Hello Telegram! Use the provided link to subscribe to specific channels.")

@bot.chat_join_request_handler(func=lambda request: True)
def handle_join_request(request):
    chat_id = request.user_chat_id
    first_name = request.from_user.first_name
    channel_id = request.chat.id

    logger.info(f"Received join request from {first_name} for channel {channel_id}")

    try:
        keyboard = types.InlineKeyboardMarkup()
        callback_data = f"confirm_channel_{channel_id}"
        callback_button = types.InlineKeyboardButton(text="Подтвердить", callback_data=callback_data)
        keyboard.add(callback_button)

        bot.send_message(chat_id, f"Привет {first_name}, я антиспам бот!\nПодтвердите, что вы человек, чтобы получить доступ к контенту:", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Error sending message to user: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_channel_"))
def handle_confirmation(call):
    chat_id = call.message.chat.id
    first_name = call.from_user.first_name
    channel_id = call.data.split("_")[2]

    channel, created = Channel.objects.get_or_create(channel_id=channel_id, defaults={'name': f'Channel {channel_id}'})

    try:
        user, created = User.objects.update_or_create(user_id=chat_id, defaults={'username': first_name})
        user.channels.add(channel)

        bot.send_message(chat_id, f"Спасибо, ваш запрос принят!")

        message = Message.objects.first()
        if message:
            bot.send_message(chat_id, message.text)

        bot.approve_chat_join_request(channel_id, call.from_user.id)
        logger.info(f"Запит на приєднання від {first_name} до каналу {channel_id} успішно прийнятий")
    except Exception as e:
        logger.error(f"Error approving join request or adding user to the database: {str(e)}")

    bot.answer_callback_query(call.id)
