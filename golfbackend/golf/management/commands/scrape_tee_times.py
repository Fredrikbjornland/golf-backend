from django.core.management.base import (
    BaseCommand,
)
import logging
from datetime import timedelta
from django.utils import timezone
from golf.models import GolfClub, TeeTime
from golf.utils.scraping import get_timeslots_of_course
import time

logger = logging.getLogger("default")


class Command(BaseCommand):
    help = "Scrape golf box for golf courses and tee times."

    def handle(self, *args, **options):
        logger.info("Started tee time scraping.")
        scrape_tee_times()
        logger.info("Tee time scraping finished.")


def create_dates(days=7):
    dates = []
    current_date = timezone.now() + timedelta(days=1)
    for _ in range(days):
        date_string = current_date.strftime("%Y%m%d") + "T000000"
        dates.append(date_string)
        current_date += timedelta(days=1)
    return dates


def scrape_tee_times():
    relevant_dates = create_dates(4)
    clubs = GolfClub.objects.filter(disabled=False).prefetch_related("golf_courses")
    for club in clubs:
        for course in club.golf_courses.all():
            timeslots = get_timeslots_of_course(
                course.course_id, club.club_id, course.name, relevant_dates
            )
            for timeslot in timeslots:
                TeeTime.objects.create(
                    time=timeslot.get("time"),
                    golf_course=course,
                    availability=timeslot.get("availability"),
                    available_spots=timeslot.get("available_spots"),
                    expired=timeslot.get("expired"),
                    price_in_ore=timeslot.get("price_in_ore"),
                )
        time.sleep(1)
