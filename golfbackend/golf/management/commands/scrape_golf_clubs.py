
from django.core.management.base import (
    BaseCommand,
)
from django.db import IntegrityError
from golf.utils.scraping import parse_golf_clubs
import logging
from golf.models import GolfClub

logger = logging.getLogger("default")


class Command(BaseCommand):
    help = "Scrape golf box for golf clubs."

    def handle(self, *args, **options):
        logger.info("Started golf club scraping.")
        scrape_golf_clubs()
        logger.info("Ended golf club scraping.")


def scrape_golf_clubs():
    golf_clubs = parse_golf_clubs()
    if golf_clubs:
        for name, club_id in golf_clubs.items():
            try:
                GolfClub.objects.create(
                    name=name,
                    club_id=club_id
                )
            except IntegrityError as e:
                logger.error(f"Failed to add {name}: {e}")
    else:
        logger.error("Failed to scrape golf clubs.")
