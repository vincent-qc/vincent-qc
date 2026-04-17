#!/usr/bin/env python3

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request


def load_json_body(response):
    raw = response.read().decode("utf-8", errors="replace")
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"message": raw}


def main():
    api_key = os.environ.get("WAKATIME_API_KEY")
    if not api_key:
        print("Missing WAKATIME_API_KEY", file=sys.stderr)
        return 1

    api_base_url = os.environ.get("API_BASE_URL", "https://wakatime.com/api").rstrip("/")
    time_range = os.environ.get("TIME_RANGE", "all_time")
    max_attempts = int(os.environ.get("WAKATIME_MAX_ATTEMPTS", "8"))

    auth = base64.b64encode(api_key.encode("utf-8")).decode("utf-8")
    url = f"{api_base_url}/v1/users/current/stats/{time_range}"

    for attempt in range(1, max_attempts + 1):
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Basic {auth}",
                "User-Agent": "vincent-qc/waka-readme-wrapper",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status = response.status
                body = load_json_body(response)
        except urllib.error.HTTPError as err:
            status = err.code
            body = load_json_body(err)
        except urllib.error.URLError as err:
            print(f"WakaTime request failed: {err}", file=sys.stderr)
            return 1

        message = body.get("message", "")
        if status == 200:
            print(f"WakaTime stats ready for '{time_range}' on attempt {attempt}.")
            return 0

        if status == 202:
            if attempt == max_attempts:
                print(
                    f"WakaTime is still calculating '{time_range}' stats after {max_attempts} attempts.",
                    file=sys.stderr,
                )
                return 1

            delay_seconds = min(30 * attempt, 120)
            details = f": {message}" if message else ""
            print(
                f"WakaTime is still preparing '{time_range}' stats (attempt {attempt}/{max_attempts}){details}"
            )
            print(f"Waiting {delay_seconds}s before retrying...")
            time.sleep(delay_seconds)
            continue

        details = f": {message}" if message else ""
        print(
            f"WakaTime returned an unexpected status while fetching '{time_range}' stats: {status}{details}",
            file=sys.stderr,
        )
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
