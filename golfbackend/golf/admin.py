from django.contrib import admin

from golf.models import GolfBoxCookie, GolfClub, GolfCourse, SearchQuery, TeeTime


class GolfCourseInline(admin.TabularInline):
    model = GolfCourse
    extra = 1


@admin.register(GolfClub)
class GolfClubAdmin(admin.ModelAdmin):
    search_fields = [
        "name",
        "club_id",
    ]
    inlines = [
        GolfCourseInline,
    ]
    list_filter = [
        "created",
        "disabled",
    ]


@admin.register(TeeTime)
class TeeTimeAdmin(admin.ModelAdmin):
    search_fields = ["golf_course__name", "golf_course__golf_club__name"]
    list_filter = [
        "time",
        "availability",
        "available_spots",
        "expired",
        "last_updated",
        "price_in_ore",
    ]
    list_display = [
        "display_time",
        "golf_course",
        "availability",
        "available_spots",
        "expired",
        "last_updated",
        "price_in_ore",
    ]

    def display_time(self, obj):
        return obj.time.strftime("%Y-%m-%d %H:%M")

    display_time.admin_order_field = "time"  # Allows column ordering
    display_time.short_description = "Time"  # Column header


@admin.register(GolfCourse)
class GolfCourseAdmin(admin.ModelAdmin):
    search_fields = [
        "name",
        "course_id",
    ]
    list_filter = [
        "created",
    ]


admin.site.register(GolfBoxCookie)
admin.site.register(SearchQuery)
