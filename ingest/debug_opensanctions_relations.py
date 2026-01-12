import requests
import json

URL = "https://data.opensanctions.org/datasets/latest/sanctions/entities.ftm.json"

def inspect_wallet_relations():
    print(f"Scanning {URL} for CryptoWallet relations...")
    try:
        with requests.get(URL, stream=True, timeout=60) as r:
            r.raise_for_status()
            count = 0
            wallets_found = 0
            
            for line in r.iter_lines():
                if not line: continue
                count += 1
                
                try:
                    data = json.loads(line)
                    if data.get("schema") == "CryptoWallet":
                        wallets_found += 1
                        print(f"\n[WALLET {wallets_found}]")
                        print(json.dumps(data, indent=2))
                        
                        # We need to see if it has 'holder', 'owner', or similar properties
                        # or if we need to find the entity that points TO this wallet.
                        # Usually FTM has properties on the relationship.
                        
                        if wallets_found >= 5:
                            return
                except:
                    pass
                
                if count % 50000 == 0:
                    print(f"Scanned {count} lines...", end="\r")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_wallet_relations()
