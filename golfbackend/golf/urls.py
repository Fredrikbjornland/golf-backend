from django.urls import path
from . import views

urlpatterns = [
    path('api/golfclubs/', views.get_golf_clubs, name='get_golf_clubs'),
    path('api/golfclubs/<str:club_id>/', views.get_golf_club, name='get_golf_club'),
    path('api/courses/<str:course_id>/times/<str:date>/', views.get_times, name='get_times'),
]
