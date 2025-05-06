import os
import logging
import json
from datetime import datetime, timedelta
from openai import OpenAI
from django.conf import settings

logger = logging.getLogger("default")


def get_openai_client():
    """
    Get an OpenAI client instance using the API key from settings or environment variables.
    """
    api_key = getattr(settings, "OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY"))
    if not api_key:
        logger.error("OpenAI API key not found in settings or environment variables")
        return None

    return OpenAI(api_key=api_key)


def parse_tee_time_query(query_text):
    """
    Parse a natural language query for tee time search using OpenAI.

    Args:
        query_text (str): Natural language query like
                         "I want to play golf tomorrow afternoon near oslo with two other people"

    Returns:
        dict: Structured data with extracted parameters like date, time_range, location, players_count
    """
    client = get_openai_client()
    if not client:
        return {"error": "OpenAI API key not configured"}

    system_prompt = f"""
        You are a helpful assistant that extracts structured information from natural language queries
        about golf tee times.
        Extract the following information if present:
        1. Date (specific date or relative like 'tomorrow', 'next week'. If relative translate to date or date range.
        Today is {datetime.now().strftime("%Y-%m-%d")})
        2. Time range (morning, afternoon, evening, or specific hours). Convert to 24 hour format.
          Eg "morning" -> "06:00 to 12:00"
        3. Golf club (name of the golf club)
        4. Location (city or area).
        5. Number of players (total including the person asking)
        6. Maximum price (if mentioned)

        Return the information in JSON format with these keys: date, time_range, golf_club, location,
        players_count, max_price. If information is not provided, use null for that field.
    """

    logger.info("Mocking OpenAI call: %s", settings.MOCK_OPENAI_CALL)
    if settings.MOCK_OPENAI_CALL:
        tomorrow = datetime.now() + timedelta(days=1)
        three_days_after_tomorrow = tomorrow + timedelta(days=3)
        tomorrow_str = tomorrow.strftime("%Y-%m-%d")
        three_days_after_str = three_days_after_tomorrow.strftime("%Y-%m-%d")

        mock_data = {
            "date": f"{tomorrow_str} to {three_days_after_str}",
            "location": "asker",
            "location_additional_info": "norway",
            "players_count": 2,
            "max_price": 17000,
            "time_range": None,
            "golf_club": None,
        }
        response_content = json.dumps(mock_data)
    else:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query_text},
            ],
            response_format={"type": "json_object"},
        )
        response_content = response.choices[0].message.content

    result = json.loads(response_content)

    # Process date if it's a relative reference like "tomorrow"
    if result.get("date"):
        if result["date"].lower() == "tomorrow":
            tomorrow = datetime.now() + timedelta(days=1)
            result["date"] = tomorrow.strftime("%Y-%m-%d")
        elif result["date"].lower() == "today":
            result["date"] = datetime.now().strftime("%Y-%m-%d")

    return result
