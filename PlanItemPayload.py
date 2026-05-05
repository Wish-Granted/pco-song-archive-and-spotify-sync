import json
from datetime import datetime
from zoneinfo import ZoneInfo

class PlanItemPayload:
	def __init__(self, payload_outer:dict):
		self.payload_outer=payload_outer
		
		if self.check_payload():
			self.payload_inner = json.loads(payload_outer["data"][0]["attributes"]["payload"])


	def check_payload(self):
		is_planning_center_plan_item_payload = True
		
		try:
			action = self.payload_outer["data"][0]["attributes"]["name"]
		except (IndexError, KeyError):
			is_pc_plan_item_payload = False

		if "services.v2.events.plan_item" not in action:
			is_planning_center_plan_item_payload = False
			
		return is_planning_center_plan_item_payload

	def get_action(self):
		action = self.payload_outer["data"][0]["attributes"]["name"]
		action = action.replace("services.v2.events.plan_item.", "")
		return action

	def get_time_of_action(self):
		if self.get_action() == "destroyed":
			return "n/a"
		event_time_unformatted = self.payload_inner["meta"]["event_time"]
		
		event_time_utc = datetime.fromisoformat(event_time_unformatted.replace("Z", "+00:00"))
		event_time_aest = event_time_utc.astimezone(ZoneInfo("Australia/Brisbane"))

		return event_time_aest

	def check_if_song(self):
		if self.payload_inner["data"]["relationships"]["song"]["data"] is None:
			is_song = False
		else:
			is_song = True
		return is_song

	def get_song_id(self):
		return self.payload_inner["data"]["relationships"]["song"]["data"]["id"]
		
	def get_song_details(self):
		if self.get_action() == "destroyed":
			return "n/a"
		song_title = self.payload_inner["data"]["attributes"]["title"]
		song_key = self.payload_inner["data"]["attributes"]["key_name"]
		return {"song_title": song_title, "song_key": song_key}
	
	def get_position_in_plan(self):
		if self.get_action() == "destroyed":
			return "n/a"
			
		return self.payload_inner["data"]["attributes"]["sequence"]
	
	def get_plan_id(self):
		return self.payload_inner["data"]["relationships"]["plan"]["data"]["id"]
		
	def get_plan_url(self):
		url = self.payload_inner["data"]["links"]["self"]
		url = url[:url.find("items")]
		return url
