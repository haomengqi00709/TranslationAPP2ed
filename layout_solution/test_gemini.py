#!/usr/bin/env python3
"""Quick test to check Gemini API and list available models."""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY not found in .env")
    exit(1)

print(f"✅ API Key found: {api_key[:10]}...{api_key[-5:]}")

genai.configure(api_key=api_key)

print("\n📋 Available models:")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"  - {model.name}")

print("\n🧪 Testing with first available model...")
try:
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    response = model.generate_content("Say 'Hello' in JSON format with a single key 'message'")
    print(f"✅ Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")
