#!/usr/bin/env python3
"""
Generates a bespoke 'commit ticker' SVG: a stock-chart-style visualization
of the last 91 days of contribution activity. Bars are colored green when
that day's commits >= the previous day's (an 'up' day) and red otherwise
('down'), echoing a candlestick chart. Fully self-contained -- no
third-party rendering service, just raw SVG built from GitHub's own data.
"""
import os
import sys
import json
import urllib.request

USERNAME = os.environ.get("TICKER_USERNAME", "Malik-AhmadSE")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT_PATH = os.environ.get("TICKER_OUTPUT", "images/commit-ticker.svg")

BG = "#0A0E0F"
SURFACE = "#121A1D"
BORDER = "#1E2A2D"
TEXT = "#E7ECEA"
TEXT_DIM = "#7C8C88"
BULL = "#35D07F"
BEAR = "#FF5C5C"
SIGNAL = "#F5B942"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def fetch_days():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USERNAME}}).encode(),
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "commit-ticker-script",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        payload = json.load(resp)
    weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = []
    for w in weeks:
        for d in w["contributionDays"]:
            days.append({"date": d["date"], "count": d["contributionCount"]})
    return days[-91:]


def build_svg(days):
    W, H = 980, 230
    pad_top, pad_bottom, pad_side = 46, 40, 16
    chart_h = H - pad_top - pad_bottom
    chart_w = W - pad_side * 2
    n = len(days)
    bar_w = chart_w / n
    max_count = max((d["count"] for d in days), default=1) or 1

    bars, line_points = [], []
    prev = 0
    total = best = current_streak = longest_streak = streak = 0

    for i, d in enumerate(days):
        c = d["count"]
        h = (c / max_count) * chart_h
        x = pad_side + i * bar_w
        y = pad_top + chart_h - h
        color = BULL if c >= prev else BEAR
        bw = max(bar_w * 0.62, 1)
        bars.append(
            f'<rect x="{x + bar_w*0.19:.1f}" y="{y:.1f}" width="{bw:.1f}" '
            f'height="{max(h,1.5):.1f}" fill="{color}" opacity="0.88" rx="1"/>'
        )
        line_points.append(f"{x + bar_w/2:.1f},{y:.1f}")
        prev = c
        total += c
        best = max(best, c)
        if c > 0:
            streak += 1
            longest_streak = max(longest_streak, streak)
        else:
            streak = 0

    current_streak = streak
    baseline_y = pad_top + chart_h

    start_date = days[0]["date"] if days else ""
    end_date = days[-1]["date"] if days else ""

    grid_lines = "".join(
        f'<line x1="{pad_side}" y1="{pad_top + chart_h*f:.1f}" '
        f'x2="{W-pad_side}" y2="{pad_top + chart_h*f:.1f}" '
        f'stroke="{BORDER}" stroke-width="1" stroke-dasharray="2,4"/>'
        for f in (0.0, 0.5, 1.0)
    )

    svg = f'''<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="JetBrains Mono, ui-monospace, Menlo, monospace">
  <rect x="0" y="0" width="{W}" height="{H}" rx="10" fill="{SURFACE}" stroke="{BORDER}"/>
  <text x="20" y="26" fill="{TEXT}" font-size="13" font-weight="700" letter-spacing="0.5">COMMIT TICKER &#8212; 91D</text>
  <text x="{W-20}" y="26" fill="{TEXT_DIM}" font-size="11" text-anchor="end">{start_date} &#8594; {end_date}</text>
  {grid_lines}
  {''.join(bars)}
  <polyline points="{' '.join(line_points)}" fill="none" stroke="{SIGNAL}" stroke-width="1.3" opacity="0.55"/>
  <line x1="{pad_side}" y1="{baseline_y:.1f}" x2="{W-pad_side}" y2="{baseline_y:.1f}" stroke="{BORDER}" stroke-width="1"/>
  <text x="20" y="{H-14}" fill="{TEXT_DIM}" font-size="11">TOTAL <tspan fill="{TEXT}" font-weight="700">{total}</tspan></text>
  <text x="180" y="{H-14}" fill="{TEXT_DIM}" font-size="11">BEST DAY <tspan fill="{BULL}" font-weight="700">{best}</tspan></text>
  <text x="360" y="{H-14}" fill="{TEXT_DIM}" font-size="11">STREAK <tspan fill="{TEXT}" font-weight="700">{current_streak}d</tspan></text>
  <text x="520" y="{H-14}" fill="{TEXT_DIM}" font-size="11">BEST STREAK <tspan fill="{TEXT}" font-weight="700">{longest_streak}d</tspan></text>
</svg>'''
    return svg


def main():
    days = fetch_days()
    svg = build_svg(days)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(days)} days)")


if __name__ == "__main__":
    main()
