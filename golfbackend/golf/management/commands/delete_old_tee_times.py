from django.core.management.base import BaseCommand
from golf.models import TeeTime
from datetime import date
import logging

logger = logging.getLogger("default")


class Command(BaseCommand):
    help = "Delete all tee times older than today"

    def handle(self, *args, **options):
        today = date.today()
        old_tee_times = TeeTime.objects.filter(time__date__lt=today)
        count = old_tee_times.count()

        if count > 0:
            old_tee_times.delete()
            self.stdout.write(
                self.style.SUCCESS(f"Successfully deleted {count} old tee times")
            )
            logger.info(f"Deleted {count} old tee times")
        else:
            self.stdout.write(self.style.SUCCESS("No old tee times found"))
            logger.info("No old tee times found to delete")
