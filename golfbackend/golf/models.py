from typing import Any
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("default")


class GolfClub(models.Model):
    name = models.CharField(max_length=100, unique=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    club_id = models.CharField(max_length=100)
    created = models.DateTimeField(default=timezone.now)
    disabled = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name


class GolfCourse(models.Model):
    name = models.CharField(max_length=100, unique=True)
    golf_club = models.ForeignKey(
        GolfClub, on_delete=models.CASCADE, related_name="golf_courses"
    )
    course_id = models.CharField(max_length=100)
    created = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.name


class TeeTime(models.Model):
    time = models.DateTimeField()
    golf_course = models.ForeignKey(
        GolfCourse, on_delete=models.CASCADE, related_name="tee_times"
    )
    availability = models.CharField(max_length=100)
    available_spots = models.IntegerField()
    expired = models.BooleanField()
    last_updated = models.DateTimeField(auto_now=True)
    price_in_ore = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1000000)],
    )

    @classmethod
    def apply_filters(self, filter_data: dict[str, Any]) -> Q:
        filters = Q()

        if filter_data.get("date"):
            # Handles both dates and date ranges on the format 'YYYY-MM-DD to YYYY-MM-DD'
            try:
                if "to" in filter_data["date"]:
                    start_date, end_date = filter_data["date"].split("to")
                    start_date = start_date.strip()
                    end_date = end_date.strip()
                    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
                    date_range = []
                    current_date = start_date_obj
                    while current_date <= end_date_obj:
                        date_range.append(current_date)
                        current_date += timedelta(days=1)
                    filters &= Q(time__date__in=date_range)
                else:
                    date_obj = datetime.strptime(filter_data["date"], "%Y-%m-%d").date()
                    filters &= Q(time__date=date_obj)
            except ValueError:
                logger.warning(f"Invalid date format: {filter_data['date']}")

        if filter_data.get("time_range"):
            time_range = filter_data["time_range"].lower()
            if "morning" in time_range:
                filters &= Q(time__hour__gte=6, time__hour__lt=12)
            elif "afternoon" in time_range:
                filters &= Q(time__hour__gte=12, time__hour__lt=17)
            elif "evening" in time_range:
                filters &= Q(time__hour__gte=17, time__hour__lt=21)
            elif "to" in time_range:
                start_time, end_time = time_range.split("to")
                start_time = start_time.strip()
                end_time = end_time.strip()
                start_time_obj = datetime.strptime(start_time, "%H:%M").time()
                end_time_obj = datetime.strptime(end_time, "%H:%M").time()
                filters &= Q(
                    time__time__gte=start_time_obj, time__time__lt=end_time_obj
                )

        if filter_data.get("players_count"):
            try:
                players_count = int(filter_data["players_count"])
                filters &= Q(available_spots__gte=players_count)
            except (ValueError, TypeError):
                logger.warning(f"Invalid players count: {filter_data['players_count']}")
        else:
            filters &= Q(available_spots__gt=0)

        if filter_data.get("golf_club"):
            golf_club = filter_data["golf_club"].lower()
            location_filters = Q(golf_course__golf_club__name__icontains=golf_club)
            filters &= location_filters

        if filter_data.get("golf_club_id"):
            golf_club_id = filter_data["golf_club_id"]
            filters &= Q(golf_course__golf_club__club_id=golf_club_id)

        if filter_data.get("max_price") and filter_data["max_price"] is not None:
            try:
                max_price_ore = int(float(filter_data["max_price"]) * 100)
                filters &= Q(price_in_ore__lte=max_price_ore) | Q(
                    price_in_ore__isnull=True
                )
            except (ValueError, TypeError):
                logger.warning(f"Invalid max price: {filter_data['max_price']}")

        filters &= Q(expired=False)
        return filters

    def __str__(self) -> str:
        return f"{self.time.strftime('%Y-%m-%d %H:%M')} - {self.golf_course.name} - {self.availability}"


class GolfBoxCookie(models.Model):
    name = models.CharField(max_length=255)
    value = models.TextField()
    expires = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class SearchQuery(models.Model):
    query = models.TextField()
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.query


class Location(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name
