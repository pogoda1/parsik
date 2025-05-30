import os

# API Configuration
API_URL = "http://192.168.0.97:1234/v1/chat/completions"
MODEL_NAME = "qwen2.5-7b-instruct-1m"
MODEL_NAME_VERY_SMART = "devstral-small-2505_gguf"
TIMEOUT = 300
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOnsiaWQiOiI5MjZjYTBhNC1lODdmLTRhODQtYmNkYS04YWU0NzZkMmEwNDAiLCJ1c2VyTmFtZSI6Ik5pa2l0YSIsInVzZXJQaG9uZSI6IiIsInVzZXJFbWFpbCI6Im5pa2l0YS51c2hha292LjAyQGdtYWlsLmNvbSIsInVzZXJSb2xlIjoiYWRtaW4ifSwiaWF0IjoxNzQ4NTMxNTYxLCJleHAiOjE3NDg1NzQ3NjF9.qKriHiYzGlG-S4559MlY_-As7x10eBpXNl4eGJwPeDQ"


# File Paths
PROMPT_FILE = os.path.expanduser("prompt.md")
FEW_SHOT_FILE = os.path.expanduser("few_shot.md")
JSON_SCHEME_FILE = os.path.expanduser("json_scheme.md")
SCHEME_HINTS_FILE = os.path.expanduser("schema_hints.md")
TEST_JSON_PATH = "../dataForParse/SwaggerUIresponse_1.json"


# Age Limits
EVENT_AGE_LIMITS = ('0', '6', '12', '16', '18')

# Error Codes
ERROR_CODES = {
    'DATE_NOT_FOUND': '1',
    'JSON_NOT_FOUND': '2',
    'INVALID_DATE': '3'
} 


CATEGORIES_DICT = [
       "excursion",
       "exhibitions",
       "well",
       "lecture",
       "seminar",
       "conference",
       "presentation",
       "webinar",
       "training",
       "master_class",
       "vorkshop",
       "business_game",
       "class",
       "forum",
       "mitap",
       "business_breakfast",
       "meeting",
       "networking",
       "mastermind",
       "theater",
       "movie",
       "stand__up",
       "concerts",
       "party",
       "circus",
       "festivals",
       "show",
       "games",
       "active_rest",
       "olympics",
       "battle",
       "championship",
       "league",
       "competition",
       "volunteering",
       "charity",
       "social_initiatives",
     ]

THEMES_DICT = [
       "culture_and_art",
       "science_and_education",
       "industry_specialized",
       "it_and_the_internet",
       "business_and_entrepreneurship",
       "visual_creativity_visual_graphics",
       "psychology_and_self__knowledge",
       "humor",
       "music",
       "travel_and_tourism",
       "cooking_and_gastronomy",
       "beauty_and_health",
       "sport"
  ]