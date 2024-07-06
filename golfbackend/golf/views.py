from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import GolfClub, GolfCourse, TeeTime
from .serializers import GolfClubSerializer, GolfCourseSerializer, TeeTimeSerializer
from django.http import JsonResponse, Http404


@api_view(['GET'])
def get_golf_clubs(request):
    golf_clubs = GolfClub.objects.all()
    serializer = GolfClubSerializer(golf_clubs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_golf_club(request, club_id):
    try:
        golf_club = GolfClub.objects.get(club_id=club_id)
    except GolfClub.DoesNotExist:
        raise Http404("Golf club does not exist")

    serializer = GolfClubSerializer(golf_club)
    return JsonResponse(serializer.data)


@api_view(['GET'])
def get_golf_courses(request, club_id):
    golf_courses = GolfCourse.objects.filter(golf_club__club_id=club_id)
    serializer = GolfCourseSerializer(golf_courses, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_times(request, course_id, date):
    times = TeeTime.objects.filter(golf_course__course_id=course_id, time__date=date)
    serializer = TeeTimeSerializer(times, many=True)
    return Response(serializer.data)
