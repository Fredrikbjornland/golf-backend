from rest_framework import serializers
from .models import GolfClub, GolfCourse, TeeTime
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone


class GolfCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = GolfCourse
        fields = ["course_id", "name", "golf_club", "created"]


class GolfClubSerializer(serializers.ModelSerializer[GolfClub]):
    golf_courses = GolfCourseSerializer(many=True, read_only=True)
    tee_times_capacity_count = serializers.SerializerMethodField()

    class Meta:
        model = GolfClub
        fields = [
            "club_id",
            "name",
            "latitude",
            "longitude",
            "golf_courses",
            "tee_times_capacity_count",
            "created",
            "disabled",
        ]

    def get_tee_times_capacity_count(self, obj):
        # Get all TeeTimes for the GolfClub through the related GolfCourses
        now = timezone.now()
        tee_times = TeeTime.objects.filter(golf_course__golf_club=obj, time__gte=now)

        # Annotate each TeeTime with its date
        tee_times = tee_times.annotate(date=TruncDate("time"))

        # Aggregate counts of TeeTimes by available_spots and date
        counts = (
            tee_times.values("date", "available_spots")
            .annotate(count=Count("id"))
            .order_by("date", "available_spots")
        )
        # Organize data by date and capacity
        data_by_date = {}
        for item in counts:
            if item["available_spots"] == 0:
                continue
            date = item["date"].isoformat()  # Convert date to string
            if date not in data_by_date:
                data_by_date[date] = {str(spots): 0 for spots in range(1, 5)}
            data_by_date[date][str(item["available_spots"])] = item["count"]

        return data_by_date


# Update GolfCourseSerializer to include nested golf_club data
class NestedGolfClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = GolfClub
        fields = ["club_id", "name", "latitude", "longitude"]


class GolfCourseWithClubSerializer(serializers.ModelSerializer):
    golf_club = NestedGolfClubSerializer(read_only=True)

    class Meta:
        model = GolfCourse
        fields = ["course_id", "name", "golf_club", "created"]


class TeeTimeSerializer(serializers.ModelSerializer[TeeTime]):
    golf_course = GolfCourseWithClubSerializer(read_only=True)

    class Meta:
        model = TeeTime
        fields = [
            "time",
            "golf_course",
            "availability",
            "available_spots",
            "expired",
            "last_updated",
            "price_in_ore",
        ]
