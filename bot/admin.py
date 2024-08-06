from django.contrib import admin
from .models import Channel, User, ScheduledMessage, Message


admin.site.register(Channel)
admin.site.register(User)
admin.site.register(ScheduledMessage)
admin.site.register(Message)
