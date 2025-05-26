import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup, Tag
import pytz
from django.conf import settings
import logging
from golf.models import GolfBoxCookie
from django.utils import timezone

logger = logging.getLogger("default")

golfbox_base_url = "https://www.golfbox.no"
golfbox_club_url = f"{golfbox_base_url}/site/ressources/booking/chooseclub.asp"
golfbox_booking_url = f"{golfbox_base_url}/site/my_golfbox/ressources/booking/grid.asp"
golfbox_login_url = f"{golfbox_base_url}/login.asp"


def login_golfbox():
    with requests.Session() as session:
        form_data = {
            "command": "login",
            "loginform.submitted": "true",
            "loginform.username": settings.GOLFBOX_USERNAME,
            "loginform.password": settings.GOLFBOX_PASSWORD,
            "loginform.submit": "LOGIN",
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "User-Agent": "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        }
        session.post(golfbox_login_url, headers=headers, data=form_data, verify=True)
        cookies_dict = requests.utils.dict_from_cookiejar(session.cookies)
        GolfBoxCookie.objects.all().delete()
        expiration = timezone.now() + timedelta(minutes=10)
        for name, value in cookies_dict.items():
            GolfBoxCookie.objects.create(name=name, value=value, expires=expiration)
        return cookies_dict


def get_cookies():
    cookies = GolfBoxCookie.objects.filter(expires__gt=timezone.now())
    if cookies.exists():
        return {cookie.name: cookie.value for cookie in cookies}
    return login_golfbox()


def parse_golf_clubs(max_amount=20):
    cookies = get_cookies()
    response = requests.get(golfbox_club_url, cookies=cookies)
    soup = BeautifulSoup(response.text, "html.parser")
    if not soup:
        return None
    select = soup.find("select", {"id": "ddlClub"})
    if not select:
        logger.error(
            "Failed to find select element with id ddlClub, are cookies correct?"
        )
        return None
    options = select.find_all("option")

    golf_courses = {}
    counter = 0
    for option in options:
        if counter >= max_amount:
            break
        value = option.get("value")
        name = option.text
        if value:  # Skip the first first option with name Velg klubb with no value
            golf_courses[name] = value.replace("{", "").replace("}", "")
    return golf_courses


def parse_golf_courses_of_club(club_id: str):
    url = get_club_url()
    form_data = {
        "command": "getClub",
        "commandValue": "",
        "ddlClub": f"{{{club_id}}}",
        "ddlResource": "",
    }

    cookies = get_cookies()

    response = requests.post(url, data=form_data, cookies=cookies)
    soup = BeautifulSoup(response.text, "html.parser")
    if not soup:
        return None
    select = soup.find("select", {"id": "ddlRessoruce"})
    if not select:
        select = soup.find("select", {"id": "ddlRessource_GUID"})
    if not select:
        logger.error(
            "Failed to find select element with id ddlRessoruce, are cookies correct?"
        )
        return None
    options = select.find_all("option")

    golf_courses = {}
    for option in options:
        value = option.get("value")
        name = option.text
        if value and value != "x":  # Skip the option Velg fasilitet that has value x
            golf_courses[name] = value.replace("{", "").replace("}", "")
    return golf_courses


def get_club_url():
    uuid = "3C37481D-8C34-4E3F-BCF5-BE2693C983D8"
    return f"{golfbox_club_url}?selected={{{uuid}}}"


def get_course_url(course_id, club_id, selected_date):
    return f"{golfbox_booking_url}?SelectedDate={selected_date}&Ressource_GUID={{{course_id}}}&Club_GUID={{{club_id}}}"


def is_expired(child):
    return "expired" in child["class"]


def get_time(child):
    timeCellDiv = child.find("div", {"class": "timecell"})
    return timeCellDiv.text.strip() if timeCellDiv else None


def get_players(child):
    playerContainerDiv = child.find("div", {"class": "time-players"})
    if playerContainerDiv and playerContainerDiv.children:
        playerDivs = list(playerContainerDiv.children)
        return len(playerDivs)
    return 0


def get_availability(child):
    classes = child["class"]
    if "free" in classes:
        return "free"
    elif "c_partfree" in classes:
        return "partfree"
    elif "full" in classes:
        return "full"
    elif "blocking" in classes:
        return "blocking"
    return "unknown"


def get_price_in_ore(child):
    priceContainerDiv = child.find(
        "div", {"class": "d-flex flex-row flex-center pt-2 pointer"}
    )
    if priceContainerDiv is None:
        return None
    priceDiv = priceContainerDiv.find("div", {"class": "ymPrice"})
    if priceDiv:
        price_in_kr_string = priceDiv.text.strip()
        price_in_kr_string = price_in_kr_string.replace(",", "").replace("-", "")
        if price_in_kr_string:
            return int(price_in_kr_string) * 100
    return None


def process_child(child):
    if isinstance(child, Tag):
        time = get_time(child)
        available_spots = 4 - get_players(child)
        availability = get_availability(child)
        price_in_ore = get_price_in_ore(child)
        if availability == "blocking":
            available_spots = 0
        expired = is_expired(child)
        return {
            "time": time,
            "availability": availability,
            "available_spots": available_spots,
            "expired": expired,
            "price_in_ore": price_in_ore,
        }
    else:
        logger.warning(f"child is not a tag: {child}")
        return None


def get_timeslots_of_course_day(soup):
    div = soup.find("div", {"class": "w-100 classicgrid portal d-flexformlist"})
    if div is None:
        return None
    children = div.children
    result = []
    for child in children:
        processed = process_child(child)
        if processed is not None:
            result.append(processed)
    return result


def date_str_to_datetime(date_str: str, time_str: str, timezone_str="Europe/Oslo"):
    if not date_str or not time_str:
        return None
    date_obj = datetime.strptime(date_str, "%Y%m%dT%H%M%S")
    time_obj = datetime.strptime(time_str, "%H:%M").time()
    combined_datetime = datetime.combine(date_obj.date(), time_obj)
    timezone = pytz.timezone(timezone_str)
    aware_datetime = timezone.localize(combined_datetime)
    return aware_datetime


def get_timeslots_of_course(
    course_id: str, club_id: str, course_name: str, relevant_dates: list[str]
):
    all_timeslots = []
    cookies = get_cookies()
    for date in relevant_dates:
        url = get_course_url(course_id, club_id, date)
        response = requests.post(url, cookies=cookies)
        soup = BeautifulSoup(response.text, "html.parser")

        timeslots = get_timeslots_of_course_day(soup)
        if timeslots is None:
            logger.error(f"Failed to get timeslots for {course_name} on {date}")
            continue
        for slot in timeslots:
            slot["time"] = date_str_to_datetime(date, slot["time"])
            if slot["time"] is None:
                # Blocking timeslots have no time, so we skip them
                continue
            all_timeslots.append(slot)
    return all_timeslots
