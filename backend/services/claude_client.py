import anthropic
from dotenv import load_dotenv
import os

load_dotenv("../.env")

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

if not CLAUDE_API_KEY:
    raise ValueError("CLAUDE_API_KEY must be set in .env")

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)