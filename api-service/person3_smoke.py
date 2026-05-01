import json
import sys
import urllib.error
import urllib.request


BASE_URL = "http://localhost:8000"


def call(method, path, body=None):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        payload = response.read().decode("utf-8")
        return response.status, payload


def main():
    try:
        health_status, health_payload = call("GET", "/health")
        print(f"HEALTH {health_status} {health_payload}")

        scrape_status, scrape_payload = call(
            "POST",
            "/scrape",
            {"url": "https://example.com"},
        )
        print(f"SCRAPE {scrape_status} {scrape_payload}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP_ERROR {exc.code} {body}")
        return 1
    except Exception as exc:
        print(f"ERROR {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())