#!/usr/bin/env python3
"""Run: python3 tests/check_activity.py. Fixtures never become published assets."""

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sys
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from update_activity import render, validate

start = date(2025, 1, 1)
weeks = []
for offset in range(366):
    day = start + timedelta(days=offset)
    weekday = (day.weekday() + 1) % 7
    if not weeks or weekday == 0:
        weeks.append({"contributionDays": []})
    weeks[-1]["contributionDays"].append({
        "date": day.isoformat(), "weekday": weekday,
        "contributionCount": 2 if offset == 0 else 0,
        "contributionLevel": "SECOND_QUARTILE" if offset == 0 else "NONE",
    })
collection = {
    "startedAt": "2025-01-01T00:00:00Z", "endedAt": "2026-01-01T00:00:00Z",
    "totalCommitContributions": 1, "totalPullRequestContributions": 1,
    "totalIssueContributions": 0,
    "contributionCalendar": {"totalContributions": 2, "weeks": weeks},
}
payload = {"data": {"user": {"contributionsCollection": collection}}}
data = validate(payload)
assert data["total"] == 2 and len(data["days"]) == 366
local_calendar = deepcopy(payload)
local_collection = local_calendar["data"]["user"]["contributionsCollection"]
local_collection["startedAt"] = "2024-12-31T17:00:00Z"
local_collection["endedAt"] = "2026-01-01T16:59:59Z"
assert validate(local_calendar) == data
for theme in ("dark", "light"):
    svg = render(data, theme, datetime(2026, 1, 1, tzinfo=timezone.utc), '<Ada & "Lin">')
    root = ElementTree.fromstring(svg)
    ns = {"s": "http://www.w3.org/2000/svg"}
    assert root.find("s:title", ns).text == '<Ada & "Lin"> · GitHub contributions'
    assert root.attrib["aria-labelledby"] == "title desc"
    assert len(root.findall("s:rect/s:title", ns)) == 366
    assert "2 contributions from 2025-01-01 — 2026-01-01" in svg
    assert "Updated 2026-01-01 00:00 UTC" in svg
    assert "prefers-reduced-motion: reduce" in svg and "3.6s ease-in-out 1" in svg
    assert "infinite" not in svg and "&lt;Ada &amp; &quot;Lin&quot;&gt;" in svg

for defect in ("errors", "count", "total", "gap", "level", "range", "missing"):
    broken = deepcopy(payload)
    c = broken["data"]["user"]["contributionsCollection"]
    first = c["contributionCalendar"]["weeks"][0]["contributionDays"][0]
    if defect == "errors":
        broken["errors"] = [{"message": "partial response"}]
    elif defect == "count":
        first["contributionCount"] = True
    elif defect == "total":
        c["contributionCalendar"]["totalContributions"] = 99
    elif defect == "gap":
        c["contributionCalendar"]["weeks"][1]["contributionDays"].pop()
    elif defect == "level":
        first["contributionLevel"] = "NONE"
    elif defect == "range":
        c["startedAt"] = "2024-01-01T00:00:00Z"
    else:
        del c["totalIssueContributions"]
    try:
        validate(broken)
    except ValueError:
        pass
    else:
        raise AssertionError(f"Accepted invalid response: {defect}")
print("Activity checks passed: calendar validation, SVG escaping, totals, finite/reduced motion")
