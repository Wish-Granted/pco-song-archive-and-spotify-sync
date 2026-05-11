import requests
import os
from datetime import datetime

PCO_APP_ID = os.getenv('PCO_APP_ID')
PCO_SECRET = os.getenv('PCO_SECRET')

TEST_PCO_APP_ID = os.getenv('TEST_PCO_APP_ID')
TEST_PCO_SECRET = os.getenv('TEST_PCO_SECRET')

def get_plan_details(url, test_pco=False):
    """gets plan name and date from planning center"""
    if not test_pco:
        response = requests.get(url, auth=(PCO_APP_ID, PCO_SECRET))
    else:
        response = requests.get(url, auth=(TEST_PCO_APP_ID, TEST_PCO_SECRET))
    if response.status_code == 200:
        plan_data = response.json()['data']

        raw_date = plan_data['attributes'].get('sort_date')
        plan_date = raw_date.replace('Z', '').replace('T', ' ')
        
        date_object = datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
        is_sunday = date_object.weekday() == 6
        time_str = date_object.strftime('%H:%M')
        backup_title = None
        if is_sunday and time_str == "10:15":
            backup_title = "Contemporary Service"
        elif is_sunday and time_str == "18:00":
            backup_title = "Sunday Night"
        elif time_str == "06:07":
            backup_title = "Example Service"

        plan_title = plan_data['attributes'].get('title')
        series_title = plan_data['attributes'].get('series_title')

        display_name = plan_title or series_title or backup_title or plan_date

        return {"success": True, "plan_title": display_name, "plan_date": plan_date}

    return {"success": False, "error": response.text}
