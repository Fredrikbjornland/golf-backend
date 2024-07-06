
from django.core.management.base import (
    BaseCommand,
)
import logging
from golf.models import GolfClub
from haversine import haversine

logger = logging.getLogger("default")

OSLO_LAT_LNG = (59.9220295, 10.6053933)


class Command(BaseCommand):
    help = "Scrape golf box for golf courses."

    def handle(self, *args, **options):
        logger.info("Started golf course scraping.")
        disable_golf_clubs_longer_than_x_km_away(100, OSLO_LAT_LNG)
        logger.info("Ended golf course scraping.")


def disable_golf_clubs_longer_than_x_km_away(x: int, location: dict):
    golf_clubs = GolfClub.objects.all()
    for club in golf_clubs:
        if club.latitude and club.longitude:
            distance = haversine(location, (club.latitude,  club.longitude))
            if distance > x:
                club.disabled = True
                club.save()
                logger.info(f"Disabled {club.name} because it is {distance} km away from {OSLO_LAT_LNG}.")
