import Client
import os
from dotenv import load_dotenv

load_dotenv()

client = Client(api_key=os.getenv("xAI_API_KEY"))

response = client.messages.create(
    model="grok-beta",
    messages=[{"role": "user", "content": "Hello, how are you?"}]
)

print(response.content)