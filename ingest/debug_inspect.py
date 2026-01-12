import requests
import io
import pandas as pd

UK_URL = "https://sanctionslist.fcdo.gov.uk/docs/UK-Sanctions-List.csv"
CSDB_URL = "https://raw.githubusercontent.com/CryptoScamDB/blacklist/master/data/urls.yaml"

def inspect_uk_search():
    print("\n--- UK SEARCH ---")
    try:
        r = requests.get(UK_URL, timeout=30)
        content = r.text
        if "Digital Currency" in content:
            print("Found 'Digital Currency' in UK content!")
            idx = content.find("Digital Currency")
            print(content[idx-100:idx+200])
        elif "Crypto" in content:
             print("Found 'Crypto' in UK content!")
             idx = content.find("Crypto")
             print(content[idx-100:idx+200])
        else:
            print("'Digital Currency'/'Crypto' NOT found in UK content.")
            
        # Also print columns
        df = pd.read_csv(io.StringIO(content), skiprows=1, on_bad_lines='skip', nrows=5)
        print("Columns:", df.columns.tolist())
    except Exception as e:
        print("UK Search Error:", e)

if __name__ == "__main__":
    inspect_uk_search()
