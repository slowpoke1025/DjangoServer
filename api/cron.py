from firebase_admin.messaging import Message, Notification
from fcm_django.models import FCMDevice
from django_cron import CronJobBase, Schedule
from models import *
from ..accounts.models import User


class SendFCMNotificationJob(CronJobBase):
    RUN_EVERY_MINS = 24*60
    schedule = Schedule(RUN_EVERY_MINS)
    code = 'api.cron.SendFCMNotificationJob'

    def do(self):
        # pass
        # Select users to send MSG
        devices = FCMDevice.objects.all()
        devices.send_message(
            # Message(
            #    data={
            #        "title": "title",
            #        "body": "body",
            #        "Nick": "1",
            #        "Room": "123",
            #    },
            # ),
            Message(
                notification=Notification(
                    title="From DREAM", body="It's time to workout!")
            ),
        )
