from django.contrib import admin

from golf.models import GolfBoxCookie, GolfClub, GolfCourse, TeeTime


class GolfCourseInline(admin.TabularInline):
    model = GolfCourse
    extra = 1


@admin.register(GolfClub)
class GolfClubAdmin(admin.ModelAdmin):
    search_fields = ['name', 'club_id',]
    inlines = [GolfCourseInline,]
    list_filter = ['created', 'disabled',]


@admin.register(TeeTime)
class TeeTimeAdmin(admin.ModelAdmin):
    search_fields = ['golf_course', 'club_id',]
    list_filter = ['time', 'availability', 'available_spots', 'expired', 'last_updated', 'price_in_ore',]


admin.site.register(GolfCourse)
admin.site.register(GolfBoxCookie)
