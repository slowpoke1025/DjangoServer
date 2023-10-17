
from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session

class Command(BaseCommand):
    help = 'Clears all session data.'

    def handle(self, *args, **options):
        # Delete all sessions
        Session.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Successfully cleared all session data.'))

# python manage.py clearsessions ----> clear the expired sessions only
# python manage.py clearAllSession ----> clear All sessions