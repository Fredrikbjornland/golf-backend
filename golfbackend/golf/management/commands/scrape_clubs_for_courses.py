from django.core.management.base import (
    BaseCommand,
)
from django.db import IntegrityError
from golf.utils.scraping import parse_golf_courses_of_club
import logging
from golf.models import GolfClub, GolfCourse

logger = logging.getLogger("default")


class Command(BaseCommand):
    help = "Scrape golf box for golf courses."

    def handle(self, *args, **options):
        logger.info("Started golf course scraping.")
        scrape_clubs_for_courses()
        logger.info("Ended golf course scraping.")


def scrape_clubs_for_courses():
    golf_clubs = GolfClub.objects.filter(golf_courses__isnull=True, disabled=False)
    for club in golf_clubs:
        courses = parse_golf_courses_of_club(club.club_id)
        if courses:
            for name, course_id in courses.items():
                try:
                    GolfCourse.objects.create(
                        name=name, golf_club=club, course_id=course_id
                    )
                except IntegrityError as e:
                    logger.error(f"Failed to add {name}: {e}")
        else:
            logger.error(f"Failed to scrape golf courses for {club.name}.")
