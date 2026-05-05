import requests
import os
from datetime import datetime

PCO_APP_ID = os.getenv('PCO_APP_ID')
PCO_SECRET = os.getenv('PCO_SECRET')

def get_plan_details(url):
    """gets plan name and date from planning center"""
    response = requests.get(url, auth=(PCO_APP_ID, PCO_SECRET))
    if response.status_code == 200:
        plan_data = response.json()['data']

        plan_title = plan_data['attributes'].get('title')
        series_title = plan_data['attributes'].get('series_title')

        display_name = plan_title or series_title or "Untitled Plan"

        raw_date = plan_data['attributes'].get('sort_date')
        plan_date = raw_date.replace('Z', '').replace('T', ' ')

        return {"success": True, "plan_title": display_name, "plan_date": plan_date}

    return {"success": False, "error": response.text}
