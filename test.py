import requests
from openai import OpenAI
from dotenv import load_dotenv  # Added for .env loading
import os

BASE_URL = "http://0.0.0.0:8080"

load_dotenv()

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
if not ADMIN_TOKEN:
    raise ValueError("ADMIN_TOKEN environment variable not found in .env file")



def create_api_key():
    payload = {"description": "Test key created via test.py"}
    response = requests.post(
        f"{BASE_URL}/api-keys",
        json=payload,
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"} 
    )
    if response.status_code != 200:
        raise Exception("Failed to create API key: " + response.text)
    data = response.json()
    try:
        return data["key"]
    except:
        return "fake-token"

def get_all_api_keys():
    response = requests.get(
        f"{BASE_URL}/api-keys",
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
    )
    if response.status_code != 200:
        raise Exception("Failed to retrieve API keys: " + response.text)
    return response.json()

def delete_api_key(api_key):
    response = requests.delete(
        f"{BASE_URL}/api-keys/{api_key}",
        headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}  # Use admin token for deletion
    )
    if response.status_code != 200:
        raise Exception("Failed to delete API key: " + response.text)
    return response.json()

# =============================================================================
# Step 1: Create a new API key
# =============================================================================
api_key = create_api_key()
print("New API Key created:", api_key)

# =============================================================================
# Step 2: Initialize the OpenAI client with the new API key and base URL
# =============================================================================
client = OpenAI(
    api_key=api_key,
    base_url=BASE_URL
)

# =============================================================================
# Step 3: Test non-streaming chat completion
# =============================================================================
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "who are you",
        }
    ],
    model="o3-mini",
)
print("\nNon-streaming response:")
print(chat_completion.choices[0].message.content)
print("*" * 20)

# =============================================================================
# Step 4: Test streaming chat completion
# =============================================================================
print("\nStreaming response:")
stream = client.chat.completions.create(
    model="llama-3.3-70b",
    messages=[{"role": "user", "content": "who are you"}],
    stream=True,
)
for chunk in stream:
    # Each chunk returns a delta containing the new token.
    print(chunk.choices[0].delta.content, end='', flush=True)
print()  # newline after stream completes

# =============================================================================
# Step 5: Retrieve all API keys
# =============================================================================
api_keys = get_all_api_keys()
print("\nRetrieved API Keys:")
print(api_keys)

# =============================================================================
# Step 6: Delete the created API key
# =============================================================================
delete_api_key(api_key)
print(f"\nDeleted API Key: {api_key}")