import requests
import json

def inspect():
    res = requests.get("https://stablecoins.llama.fi/stablecoins?includePrices=true")
    data = res.json()
    pegged = data.get("peggedAssets", [])
    usdt = next((x for x in pegged if x["symbol"] == "USDT"), None)
    
    url = f"https://stablecoins.llama.fi/stablecoin/{usdt['id']}"
    print(f"Fetching {url}")
    details = requests.get(url).json()
    
    print("Top Level Keys:", list(details.keys()))
    
    if "chainBalances" in details:
        print("Chains:", list(details["chainBalances"].keys())[:5])
        
    # Check for direct total history
    # "tokens" might be there?
    if "tokens" in details:
        print("Tokens found at top level")
    
    # "circulating" might be a list?
    print("Circulating type:", type(details.get("circulating")))

inspect()
