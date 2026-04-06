import requests

url = "https://apps.apple.com/us/app/boldvoice-accent-training/id1567841142"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
resp = requests.get(url, headers=headers)
with open("page.html", "w", encoding="utf-8") as f:
    f.write(resp.text)
print("Saved page.html")
