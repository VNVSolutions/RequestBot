import logging
from django.utils import timezone
from celery import shared_task
from telebot import types
from RequestBot.celery import app
from .conf import bot
from .models import ScheduledMessage, User

logger = logging.getLogger(__name__)


@app.task(ignore_result=True)
def process_telegram_update(update_data):
    logger.info("Обробка оновлення Telegram")
    update = types.Update.de_json(update_data)
    logger.info(f"Отримане оновлення: {update}")
    bot.process_new_updates([update])


@shared_task
def send_scheduled_messages():
    now = timezone.now()
    messages = ScheduledMessage.objects.filter(scheduled_time__lte=now)

    for message in messages:
        if message.user:
            send_message_to_user(message)
        else:
            users = User.objects.filter(channels=message.channel)
            for user in users:
                send_message_to_user(message, user)

        message.delete()

def send_message_to_user(message, user=None):
    try:
        if user:
            chat_id = user.user_id
        else:
            chat_id = message.user.user_id

        media_group = []
        if message.image:
            media_group.append(types.InputMediaPhoto(open(message.image.path, 'rb')))
        if message.video:
            media_group.append(types.InputMediaVideo(open(message.video.path, 'rb')))

        if media_group:
            if message.text:
                media_group[-1].caption = message.text
                media_group[-1].parse_mode = 'HTML'
            bot.send_media_group(chat_id, media_group)
        elif message.text:
            bot.send_message(chat_id, message.text)

        logger.info(f"Message sent to user {chat_id}")

    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
