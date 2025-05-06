import logging
from django.db.models import F, FloatField, ExpressionWrapper, QuerySet
from django.db.models.functions import Sqrt, Power
from ..models import Location  # Import Location model
from geopy.geocoders import GoogleV3
from django.conf import settings

logger = logging.getLogger("default")


def get_or_geocode_location(location_query: str) -> tuple[float | None, float | None]:
    """
    Tries to find location coordinates in the DB, falls back to Google Geocoding,
    and caches the result back to the DB.

    Args:
        location_query: The location name string to search for.

    Returns:
        A tuple (latitude, longitude) or (None, None) if coordinates cannot be determined.
    """
    target_lat = None
    target_lon = None
    location_name_for_db = location_query  # Use original query for name by default

    # 1. Try DB lookup first
    location_obj = Location.objects.filter(name__icontains=location_query).first()

    if location_obj and location_obj.latitude and location_obj.longitude:
        target_lat = location_obj.latitude
        target_lon = location_obj.longitude
        logger.info(
            f"Found matching location in DB: {location_obj.name} at ({target_lat}, {target_lon})"
        )
        return target_lat, target_lon

    logger.info(
        f"No matching location found in DB for '{location_query}'. Trying Google Geocoding."
    )

    # 2. Fallback to Google Geocoding
    if not settings.GOOGLE_MAPS_API_TOKEN:
        logger.error("GOOGLE_MAPS_API_TOKEN is not configured. Cannot geocode.")
        return None, None

    geolocator = GoogleV3(api_key=settings.GOOGLE_MAPS_API_TOKEN)
    geocoded_location = geolocator.geocode(location_query, timeout=5)
    print(geocoded_location)
    if geocoded_location and geocoded_location.latitude and geocoded_location.longitude:
        target_lat = geocoded_location.latitude
        target_lon = geocoded_location.longitude
        # Consider using geocoded_location.address for location_name_for_db if preferred
        logger.info(
            f"Resolved '{location_query}' via Google Maps to ({target_lat}, {target_lon})."
        )

        new_loc, created = Location.objects.update_or_create(
            # Using exact name match for update_or_create might be better
            # depending on desired behavior vs __icontains lookup.
            name=location_name_for_db,
            defaults={
                "latitude": target_lat,
                "longitude": target_lon,
            },
        )
        if created:
            logger.info(f"Created new Location entry: {new_loc.name}")
        else:
            logger.info(f"Updated existing Location entry for {new_loc.name}")

        return target_lat, target_lon  # Return coords even if DB save failed
    else:
        logger.warning(f"Google Maps could not geocode '{location_query}'.")
        return None, None


def sort_queryset_by_distance(
    queryset: QuerySet, target_lat: float | None, target_lon: float | None
) -> QuerySet:
    """
    Sorts a queryset of TeeTime objects by distance to a target location if coordinates are provided.

    Args:
        queryset: The base TeeTime queryset (already filtered).
        target_lat: The target latitude.
        target_lon: The target longitude.

    Returns:
        The sorted queryset (by distance then time if coordinates provided, otherwise by time).
    """
    if target_lat is not None and target_lon is not None:
        logger.info(f"Attempting to sort by distance to ({target_lat}, {target_lon})")
        # Exclude clubs without coordinates before annotating
        queryset_with_coords = queryset.exclude(
            golf_course__golf_club__latitude__isnull=True
        ).exclude(golf_course__golf_club__longitude__isnull=True)

        if not queryset_with_coords.exists():
            logger.warning(
                "No tee times found with associated golf club coordinates for distance sorting."
            )
            # Fallback to original queryset sorted by time if no results have coordinates
            return queryset.order_by("time")

        # Approximate distance calculation (Euclidean distance in degrees, ignoring curvature)
        delta_lat = F("golf_course__golf_club__latitude") - target_lat
        delta_lon = F("golf_course__golf_club__longitude") - target_lon
        distance_sq = Power(delta_lat, 2) + Power(delta_lon, 2)

        sorted_queryset = queryset_with_coords.annotate(
            distance=ExpressionWrapper(Sqrt(distance_sq), output_field=FloatField())
        ).order_by("distance", "time")  # Sort by distance first, then time

        # Optional: Consider how to handle items excluded due to missing coordinates.
        # Currently, they are simply left out if sorting by distance is applied.
        # You could potentially union the sorted queryset with the excluded items
        # if you want them appended at the end, ordered by time.

        logger.info("Successfully sorted results by distance.")
        return sorted_queryset
    else:
        # Default sorting if no location coordinates provided
        logger.info(
            "Sorting results by time (no target coordinates provided for distance sort)."
        )
        return queryset.order_by("time")
