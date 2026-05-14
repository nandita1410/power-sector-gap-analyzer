from google import genai
import os

api_key = "AIzaSyBWKV0tJU89iMcRq3ak9-ssNYRAiRnlj2s"
client = genai.Client(api_key=api_key)

for m in client.models.list():
    if "embedContent" in m.supported_actions:
        print(m.name)
