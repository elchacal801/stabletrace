import requests
import json

def inspect():
    # 1. Get list to find USDT ID
    res = requests.get("https://stablecoins.llama.fi/stablecoins?includePrices=true")
    data = res.json()
    pegged = data.get("peggedAssets", [])
    
    usdt = next((x for x in pegged if x["symbol"] == "USDT"), None)
    if not usdt:
        print("USDT not found")
        return

    print(f"USDT ID: {usdt['id']}")
    
    # 2. Fetch specific stablecoin data (hopefully history)
    # Endpoint: https://stablecoins.llama.fi/stablecoin/{id}
    url = f"https://stablecoins.llama.fi/stablecoin/{usdt['id']}"
    print(f"Fetching {url}...")
    r = requests.get(url)
    details = r.json()
    
    # Inspect keys
    print("Keys:", details.keys())
    
    # Check for 'chainBalances' or similar history
    if "chainBalances" in details:
        print("chainBalances found. Keys:", details["chainBalances"].keys())
        # Check first chain
        first_chain = list(details["chainBalances"].keys())[0]
        print(f"Sample data for {first_chain}:", details["chainBalances"][first_chain].get("tokens", [])[:2])
    else:
        print("No chainBalances")

    # Check for 'totalCirculatingUSD' or similar history array
    # often it is 'totalCirculatingUSD' : { 'date': val, ... } or list
    
inspect()
