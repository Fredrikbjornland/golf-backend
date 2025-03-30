
from django.core.management.base import (
    BaseCommand,
)
import logging
from golf.models import GolfClub
from geopy.geocoders import GoogleV3
from django.conf import settings

logger = logging.getLogger("default")


class Command(BaseCommand):
    help = "Set location of golf clubs."

    def handle(self, *args, **options):
        logger.info("Started setting location of golf clubs.")
        set_location_of_golf_clubs()
        logger.info("Ended setting location of golf clubs.")


def get_location(address: str, geolocator):
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    else:
        return None


clubs_with_no_location = {
    "Haugaland Golfklubb": {"lat": 59.4722184, "lng": 5.1973387},
    "Høken golfklubb": {"lat": 0, "lng": 0},
    "Voss Golfklubb": {"lat": 60.6818829, "lng": 6.4834398},
    "Norges Golfforbund": {"lat": 0, "lng": 0},
    "Frosta Golfklubb": {"lat": 63.583193012253375, "lng": 10.803398413858403},
}


def set_location_of_golf_clubs():
    geolocator = GoogleV3(api_key=settings.GOOGLE_MAPS_API_TOKEN)
    golf_clubs = GolfClub.objects.filter(disabled=False).all()
    for club in golf_clubs:
        try:
            if club.latitude and club.longitude:
                continue
            location = get_location(club.name, geolocator)
            if location:
                club.latitude, club.longitude = location
                club.save()
            else:
                logger.error(f"Failed to get location for {club.name}.")
        except Exception as e:
            logger.error(f"Failed to set location for {club.name}: {e}")
    for club_name, location in clubs_with_no_location.items():
        club = GolfClub.objects.filter(name=club_name).first()
        if club:
            club.latitude = location["lat"]
            club.longitude = location["lng"]
            club.save()
        else:
            logger.error(f"Failed to find {club_name} in database.")
