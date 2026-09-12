#!/usr/bin/env python3
"""Print the age of a metrics cache in whole hours, or 9999 if unusable."""
import datetime, json, sys

try:
    stamp = json.load(open(sys.argv[1]))["generated_at"]
    written = datetime.datetime.fromisoformat(stamp)
    now = datetime.datetime.now(datetime.timezone.utc)
    print(int((now - written).total_seconds() // 3600))
except Exception:
    print(9999)
