import urllib.request
import json
import subprocess
import re

print("🌾 AGRI-ADVISORY AGENT")
print("----------------------")

# Get city
city = input("📍 Enter your city: ")

# Get weather
url = f"https://wttr.in/{city}?format=j1"

try:
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode("utf-8"))

    current = data["current_condition"][0]

    weather = (
        f"Temperature: {current['temp_C']} °C, "
        f"Condition: {current['weatherDesc'][0]['value']}, "
        f"Humidity: {current['humidity']}%, "
        f"Wind: {current['windspeedKmph']} km/h"
    )

except:
    weather = "Weather information is not available."

print("\n🌦️ Current Weather:")
print(weather)

# Farmer question
question = input("\n👨‍🌾 Ask your farming question: ")

# AI prompt
prompt = f"""
You are an agriculture advisor for Indian farmers.

Farmer question:
{question}

Current weather:
{weather}

Give simple, practical and safe farming advice in 2 or 3 short sentences.

Use the weather information only when relevant.
Do not invent weather information.

For crop diseases:
- Do not claim a definite disease from symptoms alone.
- Mention that proper identification may require a clear photo or agricultural expert.
- Give safe general prevention advice.

For pesticides:
- Recommend checking the pest or disease first.
- Follow the pesticide label and local agricultural guidance.
- Avoid spraying during strong sunlight, rain, or strong wind.
- Do not recommend unsafe pesticide doses.

Answer in simple English.
"""

# Ask Ollama
result = subprocess.run(
    ["ollama", "run", "llama3.2", prompt],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Get AI answer
answer = result.stdout.decode("utf-8", errors="replace")

# Remove Ollama terminal control characters
answer = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', answer)

print("\n🤖 AI Advice:")
print(answer.strip())