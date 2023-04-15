import os

API_ENDPOINT = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
VERBOSE = 0
BASE_DIRECTORY = "generated_apps"