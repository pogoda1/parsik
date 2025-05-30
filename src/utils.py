import json
from typing import Dict, Any, Optional, List, Tuple

class EventValidator:
    @staticmethod
    def validate_event(event: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validates event data structure"""
        if not isinstance(event, dict):
            return False, "Event must be a dictionary"
        
        required_fields = ["eventDate", "eventName", "eventDescription"]
        for field in required_fields:
            if field not in event:
                return False, f"Missing required field: {field}"
        
        if not isinstance(event["eventDate"], list):
            return False, "eventDate must be a list"
        
        for date_item in event["eventDate"]:
            if not isinstance(date_item, dict):
                return False, "Each date item must be a dictionary"
            if "from" not in date_item or "to" not in date_item:
                return False, "Each date item must have 'from' and 'to' fields"
        
        return True, None

class DataLoader:
    def __init__(self):
        self.test_data_file = "data/notParserList.json"

    def load_test_data(self) -> Optional[Dict[str, Any]]:
        """Loads test data from JSON file"""
        try:
            with open(self.test_data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            return None

    def get_event_by_id(self, event_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Gets event by ID from data"""
        events = data.get("data", [])
        for event in events:
            if event.get("id") == event_id:
                return event
        return None 

