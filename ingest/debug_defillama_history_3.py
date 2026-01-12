import requests
import json
from datetime import datetime

def inspect():
    res = requests.get("https://stablecoins.llama.fi/stablecoins?includePrices=true")
    data = res.json()
    pegged = data.get("peggedAssets", [])
    usdt = next((x for x in pegged if x["symbol"] == "USDT"), None)
    
    url = f"https://stablecoins.llama.fi/stablecoin/{usdt['id']}"
    print(f"Fetching {url}")
    details = requests.get(url).json()
    
    if "tokens" in details:
        print("First 2 tokens:", details["tokens"][:2])
        # Check structure
        # Expected: { 'date': timestamp, 'circulating': { 'peggedUSD': float } }
        
inspect()
