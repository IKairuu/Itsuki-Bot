import google.generativeai as genai
import os
gemini_api_key = os.getenv("API")
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel("gemini-2.5-pro")

user_input = input("Input Question: ")
response = model.generate_content(user_input)
print(response.text)