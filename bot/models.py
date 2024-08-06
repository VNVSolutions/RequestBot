from django.db import models
from django.utils import timezone


class Channel(models.Model):
    name = models.CharField(max_length=255)
    channel_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class User(models.Model):
    channels = models.ManyToManyField(Channel, related_name='users')
    username = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255)

    def __str__(self):
        return self.username


class Message(models.Model):
    text = models.TextField(blank=True)

    def __str__(self):
        return self.text


class ScheduledMessage(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField(blank=True)
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    video = models.FileField(upload_to='videos/', null=True, blank=True)
    scheduled_time = models.DateTimeField()

    def __str__(self):
        return f"Message for {self.channel.name} at {self.scheduled_time}"