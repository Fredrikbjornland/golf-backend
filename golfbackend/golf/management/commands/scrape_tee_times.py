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

    def add_arguments(self, parser):
        parser.add_argument(
            "--number_of_clubs",
            type=int,
            default=None,
            help="Number of clubs to scrape (default: all)",
        )

    def handle(self, *args, **options):
        logger.info("Started tee time scraping.")
        number_of_clubs = options.get("number_of_clubs")
        scrape_tee_times(number_of_clubs=number_of_clubs)
        logger.info("Tee time scraping finished.")


def create_dates(days=7):
    dates = []
    current_date = timezone.now() + timedelta(days=1)
    for _ in range(days):
        date_string = current_date.strftime("%Y%m%d") + "T000000"
        dates.append(date_string)
        current_date += timedelta(days=1)
    return dates


def scrape_tee_times(number_of_clubs=None):
    relevant_dates = create_dates(6)
    clubs_qs = GolfClub.objects.filter(disabled=False).prefetch_related("golf_courses")
    if number_of_clubs is not None:
        clubs_qs = clubs_qs[:number_of_clubs]
    for club in clubs_qs:
        for course in club.golf_courses.all():
            timeslots = get_timeslots_of_course(
                course.course_id, club.club_id, course.name, relevant_dates
            )
            for timeslot in timeslots:
                TeeTime.objects.update_or_create(
                    time=timeslot.get("time"),
                    golf_course=course,
                    defaults={
                        "availability": timeslot.get("availability"),
                        "available_spots": timeslot.get("available_spots"),
                        "expired": timeslot.get("expired"),
                        "price_in_ore": timeslot.get("price_in_ore"),
                    },
                )
        logger.info(f"Scraped {len(timeslots)} tee times for {club.name}")
        time.sleep(1)
