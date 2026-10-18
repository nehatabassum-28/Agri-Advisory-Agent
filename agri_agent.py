import urllib.request
import json

print("🌾 AGRI-ADVISORY AGENT")
print("----------------------")

while True:
    question = input("\n👨‍🌾 Ask your farming question: ")

    if question.lower() == "exit":
        print("Goodbye!")
        break

    data = json.dumps({
        "model": "llama3.2",
        "prompt": question,
        "stream": False
    }).encode("utf-8")

    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read().decode("utf-8"))

        print("\n🤖 AI Advice:")
        print(result["response"])

    except Exception as e:
        print("\n❌ Error:", e)