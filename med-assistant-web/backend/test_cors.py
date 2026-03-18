import sys
import urllib.request

try:
    req = urllib.request.Request(
        'http://localhost:8000/insights/generate/1', 
        method='POST',
        headers={
            "Content-Type": "application/json",
            "Origin": "http://localhost:5173"
        }
    )
    res = urllib.request.urlopen(req)
    print("Success:", res.status)
except Exception as e:
    print(f"Error type: {type(e).__name__}")
    print(f"Error msg: {e}")
    if hasattr(e, 'headers'):
        print("Headers:", e.headers)
    if hasattr(e, 'read'):
        print("Response body:", e.read().decode())
