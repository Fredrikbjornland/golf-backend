from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


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
    golf_club = models.ForeignKey(GolfClub, on_delete=models.CASCADE, related_name="golf_courses")
    course_id = models.CharField(max_length=100)
    created = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.name


class TeeTime(models.Model):
    time = models.DateTimeField()
    golf_course = models.ForeignKey(GolfCourse, on_delete=models.CASCADE)
    availability = models.CharField(max_length=100)
    available_spots = models.IntegerField()
    expired = models.BooleanField()
    last_updated = models.DateTimeField(auto_now=True)
    price_in_ore = models.IntegerField(null=True, blank=True, validators=[
        MinValueValidator(0),
        MaxValueValidator(10000)
    ])

    def __str__(self) -> str:
        return f"{self.time.strftime('%Y-%m-%d %H:%M')} - {self.golf_course.name} - {self.availability}"


class GolfBoxCookie(models.Model):
    name = models.CharField(max_length=255)
    value = models.TextField()
    expires = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name
