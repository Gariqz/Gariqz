#!/usr/bin/env python3
"""Refresh real GitHub contribution SVGs using only Python's standard library."""

import json
import os
from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

USER = "Gariqz"
ROOT = Path(__file__).resolve().parents[1]
LEVELS = ("NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE")
TOTALS = ("totalCommitContributions", "totalPullRequestContributions", "totalIssueContributions")
QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      startedAt endedAt
      totalCommitContributions totalPullRequestContributions totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date weekday contributionCount contributionLevel } }
      }
    }
  }
}
"""


def validate(payload):
    """Reject incomplete, inconsistent, or non-year calendar responses."""
    def count(value):
        if type(value) is not int or value < 0:
            raise ValueError("Invalid contribution count")
        return value

    try:
        if payload.get("errors"):
            raise ValueError("GitHub GraphQL returned errors")
        collection = payload["data"]["user"]["contributionsCollection"]
        start = datetime.fromisoformat(collection["startedAt"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(collection["endedAt"].replace("Z", "+00:00"))
        if start.utcoffset() != timedelta(0) or end.utcoffset() != timedelta(0):
            raise ValueError("Expected UTC collection range")
        if not 364 <= (end - start).days <= 366:
            raise ValueError("Expected last-year collection")
        calendar = collection["contributionCalendar"]
        total = count(calendar["totalContributions"])
        totals = [count(collection[key]) for key in TOTALS]
        weeks = calendar["weeks"]
        if not isinstance(weeks, list) or not 52 <= len(weeks) <= 54:
            raise ValueError("Invalid calendar weeks")
        days = []
        for column, week in enumerate(weeks):
            entries = week["contributionDays"]
            if not isinstance(entries, list) or not 1 <= len(entries) <= 7:
                raise ValueError("Invalid calendar week")
            for entry in entries:
                day = date.fromisoformat(entry["date"])
                weekday = entry["weekday"]
                number = count(entry["contributionCount"])
                level = LEVELS.index(entry["contributionLevel"])
                if type(weekday) is not int or weekday != (day.weekday() + 1) % 7:
                    raise ValueError("Invalid calendar weekday")
                if (number == 0) != (level == 0):
                    raise ValueError("Inconsistent contribution level")
                if days and (day != days[-1][0] + timedelta(days=1)
                             or column != days[-1][3] + (weekday == 0)):
                    raise ValueError("Calendar dates must be contiguous")
                days.append((day, number, level, column, weekday))
        # GitHub calendar dates follow the profile timezone, not necessarily UTC.
        if (abs((days[0][0] - start.date()).days) > 1
                or abs((days[-1][0] - end.date()).days) > 1
                or not 365 <= len(days) <= 367
                or sum(day[1] for day in days) != total
                or sum(totals) > total):
            raise ValueError("Incomplete or inconsistent contribution calendar")
        return {"days": days, "total": total, "totals": totals}
    except (KeyError, TypeError, AttributeError, IndexError) as exc:
        raise ValueError("Malformed GitHub contribution response") from exc


def fetch(token):
    request = Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "Accept": "application/vnd.github+json", "User-Agent": "Gariqz-activity"},
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        return validate(json.load(response))


def render(data, theme, updated, user=USER):
    if theme not in ("dark", "light"):
        raise ValueError("Unknown theme")
    if updated.utcoffset() != timedelta(0):
        raise ValueError("Update timestamp must be UTC")
    dark = theme == "dark"
    bg, panel, ink, muted, border, accent = (
        ("#0b1210", "#101d17", "#e7f5ed", "#a0b8a9", "#284235", "#6deba5") if dark else
        ("#f7fcf8", "#edf6ef", "#142e20", "#476753", "#cedfd2", "#147c43")
    )
    colors = ("#1b2c22", "#164d30", "#207342", "#35a85e", "#6deba5") if dark else (
        "#dce9df", "#a1dcb0", "#61bc7e", "#2e9556", "#146c39")
    days = data["days"]
    period = f"{days[0][0].isoformat()} — {days[-1][0].isoformat()}"
    stamp = updated.strftime("%Y-%m-%d %H:%M UTC")
    title = escape(f"{user} · GitHub contributions")
    description = escape(
        f"{data['total']:,} contributions from {period}. "
        f"{data['totals'][0]:,} commit contributions, {data['totals'][1]:,} pull request contributions, "
        f"{data['totals'][2]:,} issue contributions. Updated {stamp}. "
        "Counts reflect GitHub API visibility; total also includes other contribution types. "
        "Each square represents one day; greener squares indicate more contributions."
    )
    svg = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="410" viewBox="0 0 960 410" role="img" aria-labelledby="title desc">
<title id="title">{title}</title>
<desc id="desc">{description}</desc>
<style>
text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: {ink}; }}
.muted {{ fill: {muted}; }}
.scan {{ opacity: 0; animation: scan 3.6s ease-in-out 1; }}
@keyframes scan {{ 0% {{ transform: translateX(0); opacity: 0; }} 15% {{ opacity: .6; }} 85% {{ opacity: .6; }} 100% {{ transform: translateX(820px); opacity: 0; }} }}
@media (prefers-reduced-motion: reduce) {{ .scan {{ animation: none; opacity: 0; }} }}
</style>
<rect x="1" y="1" width="958" height="408" rx="20" fill="{bg}" stroke="{border}"/>
<text x="30" y="39" font-size="19" font-weight="650">CONTRIBUTION ACTIVITY</text>
<text x="930" y="39" text-anchor="end" font-size="17" class="muted">{escape(user)} / GitHub</text>
<text x="30" y="102" font-size="52" font-weight="750">{data['total']:,}</text>
<text x="30" y="130" font-size="21" class="muted">contributions</text>''']
    for x, value, label in zip((370, 570, 770), data["totals"], ("Commits", "Pull requests", "Issues")):
        svg.append(f'<text x="{x}" y="100" font-size="40" font-weight="650">{value:,}</text>')
        svg.append(f'<text x="{x}" y="130" font-size="20" class="muted">{label}</text>')
    svg.append(f'<rect x="20" y="152" width="920" height="177" rx="12" fill="{panel}"/>')
    pitch = min(16, 850 / (days[-1][3] + 1))
    previous_month = None
    last_month_x = -100
    for day, number, level, column, weekday in days:
        x, y = 72 + column * pitch, 193 + weekday * 17
        if day.month != previous_month and (column == 0 or day.day == 1):
            if column < days[-1][3] - 1 and x - last_month_x >= 36:
                svg.append(f'<text x="{x:g}" y="177" font-size="13" class="muted">{day:%b}</text>')
                last_month_x = x
            previous_month = day.month
        svg.append(f'<rect x="{x:g}" y="{y}" width="{pitch - 3:g}" height="14" rx="3" fill="{colors[level]}"><title>{day.isoformat()}: {number:,} contributions</title></rect>')
    for weekday, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        svg.append(f'<text x="31" y="{204 + weekday * 17}" font-size="12" class="muted">{label}</text>')
    # Scan stays above the cells: contribution intensity never changes.
    svg.append(f'<rect class="scan" x="72" y="185" width="28" height="2" rx="1" fill="{accent}" aria-hidden="true"/>')
    svg.append(f'<text x="30" y="355" font-size="18" class="muted">{period}</text>')
    svg.append('<text x="735" y="354" font-size="13" class="muted">Less</text>')
    for i, color in enumerate(colors):
        svg.append(f'<rect x="{770 + i * 21}" y="342" width="15" height="15" rx="3" fill="{color}"/>')
    svg.append('<text x="880" y="354" font-size="13" class="muted">More</text>')
    svg.append(f'<text x="30" y="386" font-size="16" class="muted">Updated {stamp} · Source: GitHub GraphQL · API-visible activity</text>\n</svg>\n')
    return "\n".join(svg)


def main():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("Set GH_TOKEN or GITHUB_TOKEN")
    data = fetch(token)
    updated = datetime.now(timezone.utc)
    if abs((data["days"][-1][0] - updated.date()).days) > 1:
        raise ValueError("GitHub returned a stale calendar; retry later")
    # Fetch, validate, and render both themes before touching existing assets.
    outputs = [(ROOT / "assets" / f"activity-{theme}.svg", render(data, theme, updated))
               for theme in ("dark", "light")]
    staged = []
    try:
        for target, content in outputs:
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=target.parent,
                                             prefix=".activity-", delete=False) as temp:
                staged.append((Path(temp.name), target))
                temp.write(content)
                temp.flush()
                os.fsync(temp.fileno())
            os.chmod(temp.name, 0o644)
        for source, target in staged:
            os.replace(source, target)
    finally:
        for source, _ in staged:
            source.unlink(missing_ok=True)
    print("Updated assets/activity-dark.svg and assets/activity-light.svg")


if __name__ == "__main__":
    try:
        main()
    except HTTPError as exc:
        sys.exit(f"GitHub HTTP {exc.code}; existing assets unchanged")
    except (URLError, TimeoutError, ValueError, OSError) as exc:
        # Never echo response bodies, request headers, or credentials.
        sys.exit(f"Activity update failed ({type(exc).__name__}); check API access and calendar data")
