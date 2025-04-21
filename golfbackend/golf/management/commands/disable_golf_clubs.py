from django.core.management.base import BaseCommand
import logging
from golf.models import GolfClub
from haversine import haversine

logger = logging.getLogger("default")

OSLO_LAT_LNG = (59.9220295, 10.6053933)


class Command(BaseCommand):
    help = "Disable golf clubs that are further than X kilometers from a location."

    def add_arguments(self, parser):
        parser.add_argument(
            "--distance",
            type=int,
            default=100,
            help="Maximum distance in kilometers (default: 100)",
        )

    def handle(self, *args, **options):
        distance = options["distance"]
        logger.info(f"Started disabling golf clubs further than {distance}km away.")
        disable_golf_clubs_longer_than_x_km_away(distance, OSLO_LAT_LNG)
        logger.info("Finished disabling golf clubs.")


def disable_golf_clubs_longer_than_x_km_away(x: int, location: tuple):
    golf_clubs = GolfClub.objects.all()
    for club in golf_clubs:
        if club.latitude and club.longitude:
            distance = haversine(location, (club.latitude, club.longitude))
            if distance > x:
                club.disabled = True
                club.save()
                logger.info(
                    f"Disabled {club.name} because it is {distance:.1f} km away from {location}."
                )
