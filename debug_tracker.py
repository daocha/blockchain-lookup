import requests

def debug_tracker(name):
    # Seeker Tracker might use a different endpoint or query param
    urls = [
        f"https://seeker-production-46ae.up.railway.app/search?query={name}",
        f"https://seeker-production-46ae.up.railway.app/api/search?query={name}",
        f"https://seeker-production-46ae.up.railway.app/api/v1/search?query={name}"
    ]
    for url in urls:
        try:
            res = requests.get(url, timeout=10)
            print(f"URL: {url} - {res.status_code}")
            if res.status_code == 200:
                print(f"Response: {res.text[:200]}")
        except Exception as e:
            print(f"Error {url}: {e}")

if __name__ == "__main__":
    debug_tracker("msft.skr")
