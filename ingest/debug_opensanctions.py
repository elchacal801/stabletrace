import requests
import json

# Using the default entities file which aggregates everything
URL = "https://data.opensanctions.org/datasets/latest/default/entities.ftm.json"

def scan_opensanctions_wallet():
    print(f"Scanning {URL} for CryptoWallet...")
    try:
        with requests.get(URL, stream=True, timeout=60) as r:
            r.raise_for_status()
            count = 0
            wallets_found = 0
            
            for line in r.iter_lines():
                if not line: continue
                count += 1
                
                # decoding line
                try:
                    line_str = line.decode('utf-8')
                    # Pre-filter string to avoid JSON parse overhead if possible
                    if "CryptoWallet" in line_str:
                        data = json.loads(line_str)
                        if data.get("schema") == "CryptoWallet":
                            wallets_found += 1
                            print(f"\n[MATCH {wallets_found}] Found CryptoWallet:")
                            print(json.dumps(data, indent=2))
                            if wallets_found >= 3:
                                print("Found enough samples. Stopping.")
                                return
                except Exception as e:
                    pass
                
                if count % 50000 == 0:
                    print(f"Scanned {count} lines...", end="\r")
                    
                if count > 1000000: # Scan 1M lines max (file is huge)
                    print("\nReached scan limit.")
                    break
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scan_opensanctions_wallet()
