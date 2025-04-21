from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import GolfClub, GolfCourse, TeeTime
from .serializers import GolfClubSerializer, GolfCourseSerializer, TeeTimeSerializer
from django.http import JsonResponse, Http404
from .utils.openai_utils import parse_tee_time_query
import logging
from django.core.paginator import Paginator

logger = logging.getLogger("default")


@api_view(["GET"])
def get_golf_clubs(request):
    golf_clubs = GolfClub.objects.all()
    serializer = GolfClubSerializer(golf_clubs, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_golf_club(request, club_id):
    try:
        golf_club = GolfClub.objects.get(club_id=club_id)
    except GolfClub.DoesNotExist:
        raise Http404("Golf club does not exist")

    serializer = GolfClubSerializer(golf_club)
    return JsonResponse(serializer.data)


@api_view(["GET"])
def get_golf_courses(request, club_id):
    golf_courses = GolfCourse.objects.filter(golf_club__club_id=club_id)
    serializer = GolfCourseSerializer(golf_courses, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_times(request, course_id, date):
    times = TeeTime.objects.filter(golf_course__course_id=course_id, time__date=date)
    serializer = TeeTimeSerializer(times, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def tee_times(request):
    query_dict = request.GET

    parsed_query = {
        "date": query_dict.get("date"),
        "players_count": query_dict.get("slotsAvailable"),
        "max_price": query_dict.get("maxPrice"),
    }

    # Remove None values
    parsed_query = {k: v for k, v in parsed_query.items() if v is not None}
    filters = TeeTime.apply_filters(parsed_query)
    tee_times = (
        TeeTime.objects.filter(filters)
        .select_related("golf_course", "golf_course__golf_club")
        .order_by("time")
    )
    serializer = TeeTimeSerializer(tee_times, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def search_for_tee_time(request):
    """
    Search for tee times using natural language query processed by OpenAI.

    Example query: "I want to play golf tomorrow afternoon near oslo with two other people"
    """
    query = request.GET.get("query", "")
    if not query:
        return Response({"error": "Query parameter is required"}, status=400)

    parsed_query = parse_tee_time_query(query)
    if "error" in parsed_query:
        return Response({"error": parsed_query["error"]}, status=500)

    filters = TeeTime.apply_filters(parsed_query)
    tee_times = (
        TeeTime.objects.filter(filters)
        .select_related("golf_course", "golf_course__golf_club")
        .order_by("time")
    )

    paginator = Paginator(tee_times, 100)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    serializer = TeeTimeSerializer(page_obj, many=True)

    return Response(
        {
            "parsed_query": parsed_query,
            "results": serializer.data,
            "pagination": {
                "total_results": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": page_obj.number,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
            },
        }
    )
