import urllib.request
import json
import subprocess
import re
import requests
from datetime import datetime


# =========================================================
# WEATHER
# =========================================================

def get_weather(city):

    url = f"https://wttr.in/{city}?format=j1"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        current = data["current_condition"][0]

        return (
            f"Temperature: {current['temp_C']} °C\n"
            f"Condition: {current['weatherDesc'][0]['value']}\n"
            f"Humidity: {current['humidity']}%\n"
            f"Wind: {current['windspeedKmph']} km/h"
        )

    except:
        return "Weather information is not available."


# =========================================================
# AI ADVISOR
# =========================================================

def ask_ai(question, extra=""):

    prompt = f"""
You are an agricultural advisor for farmers in India.

Farmer question:
{question}

Additional information:
{extra}

IMPORTANT:
- Reply ONLY in simple English.
- Do NOT use Telugu.
- Do NOT use Hindi.
- Give short and clear advice.
- Give practical and safe farming advice.
- Do not invent exact pesticide doses.
- Do not claim a definite disease diagnosis from symptoms alone.
- If a photo or more information is needed, say so.
- For government schemes, explain them simply.
- Tell the farmer to verify current eligibility from official sources.

Answer in 2 or 3 simple sentences.
"""

    result = subprocess.run(
        ["ollama", "run", "llama3.2", prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    answer = result.stdout.decode("utf-8", errors="replace")

    answer = re.sub(
        r'\x1b\[[0-9;]*[A-Za-z]',
        '',
        answer
    )

    return answer.strip()


# =========================================================
# AGMARKNET HEADERS
# =========================================================

def get_headers():

    return {
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://agmarknet.gov.in",
        "Referer": "https://agmarknet.gov.in/",
        "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/154.0.0.0 Safari/537.36"
    }


# =========================================================
# FIND CROP
# =========================================================

def find_crop(crop):

    url = (
        "https://api.agmarknet.gov.in/"
        "v1/daily-price-arrival/filters"
    )

    try:

        response = requests.get(
            url,
            headers=get_headers(),
            timeout=20
        )

        data = response.json()

        crop = crop.strip().lower()

        commodities = []

        if isinstance(data, dict):

            filter_data = data.get("data", data)

            if isinstance(filter_data, dict):

                commodities = (
                    filter_data.get("cmdt_data")
                    or filter_data.get("commodity")
                    or filter_data.get("commodities")
                    or []
                )

            elif isinstance(filter_data, list):

                commodities = filter_data

        # Exact match
        for item in commodities:

            name = str(
                item.get("cmdt_name")
                or item.get("commodityName")
                or item.get("name")
                or ""
            )

            if name.lower() == crop:

                crop_id = (
                    item.get("cmdt_id")
                    or item.get("commodityId")
                    or item.get("id")
                )

                group_id = (
                    item.get("cmdt_group_id")
                    or item.get("commodityGroupId")
                    or item.get("groupId")
                )

                return name, crop_id, group_id

        # Partial match
        for item in commodities:

            name = str(
                item.get("cmdt_name")
                or item.get("commodityName")
                or item.get("name")
                or ""
            )

            if crop in name.lower():

                crop_id = (
                    item.get("cmdt_id")
                    or item.get("commodityId")
                    or item.get("id")
                )

                group_id = (
                    item.get("cmdt_group_id")
                    or item.get("commodityGroupId")
                    or item.get("groupId")
                )

                return name, crop_id, group_id

        return None

    except Exception as e:

        print("❌ Crop search error:")
        print(e)

        return None


# =========================================================
# GET MARKET PRICES
# =========================================================

def get_market_prices(crop):

    print("\n⏳ Finding crop...")

    crop_info = find_crop(crop)

    if not crop_info:

        print("❌ Crop not found.")

        return []

    crop_name, commodity_id, group_id = crop_info

    print(
        f"✅ Found: {crop_name} "
        f"(ID: {commodity_id})"
    )

    print("\n⏳ Getting live market prices...")

    url = (
        "https://api.agmarknet.gov.in/"
        "v1/prices-and-arrivals/market-report/specific"
    )

    today = datetime.now().strftime("%Y-%m-%d")

    # Tomato group ID
    if str(crop_name).lower() == "tomato":

        group_id = 6

    params = {
        "date": today,
        "commodityGroupId": group_id,
        "commodityId": commodity_id,
        "includeExcel": "false"
    }

    try:

        response = requests.get(
            url,
            headers=get_headers(),
            params=params,
            timeout=30
        )

        report = response.json()

        results = []

        # -------------------------------------------------
        # SEARCH THE COMPLETE API RESPONSE
        # -------------------------------------------------

        def search_data(
            obj,
            state="Unknown",
            market="Unknown"
        ):

            if isinstance(obj, dict):

                # Find state
                new_state = (
                    obj.get("stateName")
                    or obj.get("state")
                    or state
                )

                # Find market
                new_market = (
                    obj.get("marketName")
                    or obj.get("market")
                    or market
                )

                # Find price record
                if (
                    "minimumPrice" in obj
                    and "maximumPrice" in obj
                    and "modalPrice" in obj
                ):

                    results.append({

                        "state": new_state,

                        "market": new_market,

                        "minimum":
                            obj.get("minimumPrice"),

                        "maximum":
                            obj.get("maximumPrice"),

                        "modal":
                            obj.get("modalPrice"),

                        "unit":
                            obj.get(
                                "unitOfPrice",
                                "Rs./Quintal"
                            )
                    })

                # Continue searching inside dictionary
                for value in obj.values():

                    search_data(
                        value,
                        new_state,
                        new_market
                    )

            elif isinstance(obj, list):

                for item in obj:

                    search_data(
                        item,
                        state,
                        market
                    )

        search_data(report)

        # -------------------------------------------------
        # REMOVE DUPLICATES
        # -------------------------------------------------

        unique_results = []

        seen = set()

        for row in results:

            key = (
                row["state"],
                row["market"],
                row["minimum"],
                row["maximum"],
                row["modal"]
            )

            if key not in seen:

                seen.add(key)

                unique_results.append(row)

        return unique_results

    except Exception as e:

        print("\n❌ Market API error:")
        print(e)

        return []


# =========================================================
# DISPLAY MARKET PRICES
# =========================================================

def show_market_prices(crop):

    results = get_market_prices(crop)

    if not results:

        print("\n❌ No market data found.")

        return

    print("\n")

    print("=" * 105)

    print(
        f"💰 LIVE ALL-INDIA MARKET PRICES — "
        f"{crop.upper()}"
    )

    print("=" * 105)

    print(
        f"{'STATE':<20}"
        f"{'MARKET':<30}"
        f"{'MIN ₹':<12}"
        f"{'MAX ₹':<12}"
        f"{'MODAL ₹':<12}"
    )

    print("-" * 105)

    count = 0

    for row in results:

        print(
            f"{str(row['state'])[:19]:<20}"
            f"{str(row['market'])[:29]:<30}"
            f"{str(row['minimum']):<12}"
            f"{str(row['maximum']):<12}"
            f"{str(row['modal']):<12}"
        )

        count += 1

        # Show maximum 100 markets
        if count >= 100:

            break

    print("-" * 105)

    print(
        f"Showing {count} market records."
    )

    print(
        "Price unit: Rs./Quintal"
    )


# =========================================================
# MAIN PROGRAM
# =========================================================

print(
    "🌾 AGRI-ADVISORY & MARKET LINKAGE AGENT"
)

print(
    "========================================"
)


while True:

    print("""
1. 🌱 Crop / Farming Advice
2. 🐛 Disease Advice
3. 🌦️ Weather
4. 🏛️ Government Schemes
5. 💰 Market Prices
6. ❌ Exit
""")

    choice = input(
        "Choose an option: "
    )

    # =====================================================
    # OPTION 1 — FARMING ADVICE
    # =====================================================

    if choice == "1":

        question = input(
            "\n👨‍🌾 Ask your farming question: "
        )

        print("\n🤖 AI Advice:")

        print(
            ask_ai(question)
        )


    # =====================================================
    # OPTION 2 — DISEASE ADVICE
    # =====================================================

    elif choice == "2":

        question = input(
            "\n🐛 Describe the crop problem: "
        )

        print("\n🤖 AI Advice:")

        print(
            ask_ai(question)
        )


    # =====================================================
    # OPTION 3 — WEATHER
    # =====================================================

    elif choice == "3":

        city = input(
            "\n📍 Enter your city: "
        )

        weather = get_weather(city)

        print("\n🌦️ Current Weather:")

        print(weather)

        question = input(
            "\n👨‍🌾 Ask a weather-related farming "
            "question (or press Enter to return): "
        )

        if question.strip():

            print("\n🤖 AI Advice:")

            print(
                ask_ai(
                    question,
                    weather
                )
            )


    # =====================================================
    # OPTION 4 — GOVERNMENT SCHEMES
    # =====================================================

    elif choice == "4":

        question = input(
            "\n🏛️ Ask about a government farmer scheme: "
        )

        print("\n🤖 AI Advice:")

        print(
            ask_ai(question)
        )


    # =====================================================
    # OPTION 5 — MARKET PRICES
    # =====================================================

    elif choice == "5":

        crop = input(
            "\n💰 Enter crop name: "
        )

        show_market_prices(crop)


    # =====================================================
    # OPTION 6 — EXIT
    # =====================================================

    elif choice == "6":

        print(
            "\n🌾 Thank you for using "
            "Agri-Advisory Agent!"
        )

        break


    else:

        print(
            "\n❌ Please choose a number "
            "from 1 to 6."
        )