import requests

def debug_resolve(name):
    print(f"DEBUG: Trying to resolve {name}")
    
    # 1. Official SNS API
    try:
        url = f"https://api.sns.id/v1/sns/resolve/{name}"
        res = requests.get(url, timeout=10)
        print(f"SNS.ID API ({name}): {res.status_code} - {res.text}")
    except Exception as e:
        print(f"SNS.ID API Error: {e}")

    # 2. SDK Proxy
    try:
        url = f"https://sdk-proxy.sns.id/resolve/{name}"
        res = requests.get(url, timeout=10)
        print(f"SDK Proxy ({name}): {res.status_code} - {res.text}")
    except Exception as e:
        print(f"SDK Proxy Error: {e}")

    # 3. Seeker Tracker API
    try:
        url = f"https://seeker-production-46ae.up.railway.app/api/resolve/{name}"
        res = requests.get(url, timeout=10)
        print(f"Seeker Tracker API ({name}): {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Seeker Tracker API Error: {e}")

if __name__ == "__main__":
    debug_resolve("msft.skr")
