import os

# API Configuration
API_URL = "http://192.168.0.97:1234/v1/chat/completions"
MODEL_NAME = "qwen2.5-7b-instruct-1m"
TIMEOUT = 180

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