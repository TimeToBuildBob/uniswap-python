#!/usr/bin/env python3
"""
adoption_snapshot.py — Uniswap-Python Adoption Metrics

Usage:
  python3 scripts/adoption_snapshot.py [--out DIR]
  python3 scripts/adoption_snapshot.py --report BASELINE.json

Modes:
  Snapshot (default): Emits a dated JSON + Markdown snapshot of:
    - GitHub stars, forks, watchers, open issues
    - GitHub Traffic: clones + unique visitors (14-day window — run frequently!)
    - PyPI downloads last day/week/month (pypistats.org API)
    - Recent release versions and dates

  Report (--report BASELINE.json): reads current metrics + a saved baseline
    and prints a deltas table for UF grant D4 final adoption report.

GitHub Traffic requires a token with push access to the repo:
  GITHUB_TOKEN=ghp_... python3 scripts/adoption_snapshot.py

Without GITHUB_TOKEN, traffic metrics are omitted (other metrics still work).
Version-split download counts require BigQuery — not yet wired; see TODO below.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = "uniswap-python/uniswap-python"
PACKAGE = "uniswap-python"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gh(path: str, token: str | None = None) -> tuple[dict | list | None, str | None]:
    base = f"https://api.github.com/repos/{REPO}"
    url = f"{base}/{path}" if path else base
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return None, str(e)


def _fetch_json(url: str, headers: dict | None = None) -> tuple[dict | None, str | None]:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return None, str(e)


# ---------------------------------------------------------------------------
# Collectors
# ---------------------------------------------------------------------------


def _collect_github(token: str | None) -> dict:
    data, err = _gh("", token)
    if err:
        return {"error": err}
    return {
        "stars": data.get("stargazers_count"),
        "forks": data.get("forks_count"),
        "watchers": data.get("subscribers_count"),
        "open_issues": data.get("open_issues_count"),
    }


def _collect_traffic(token: str | None) -> dict:
    if not token:
        return {"note": "Skipped — set GITHUB_TOKEN with push access to capture traffic (14-day window only)"}

    clones, c_err = _gh("traffic/clones?per=week", token)
    views, v_err = _gh("traffic/views?per=week", token)
    result: dict = {
        "clones_14d": clones.get("count") if clones else None,
        "unique_cloners_14d": clones.get("uniques") if clones else None,
        "views_14d": views.get("count") if views else None,
        "unique_visitors_14d": views.get("uniques") if views else None,
    }
    if c_err:
        result["clones_error"] = c_err
    if v_err:
        result["views_error"] = v_err
    return result


def _collect_pypi_recent() -> dict:
    # TODO: version-split downloads require BigQuery or a scraper not yet wired.
    # pypistats.org /recent gives overall day/week/month totals only.
    url = f"https://pypistats.org/api/packages/{PACKAGE}/recent"
    data, err = _fetch_json(url, {"User-Agent": f"{PACKAGE}-adoption-tracker/1.0; +https://github.com/{REPO}"})
    if err:
        return {"error": err, "note": "pypistats.org rate-limited; retry after a few minutes"}
    d = data.get("data", {})
    return {
        "downloads_last_day": d.get("last_day"),
        "downloads_last_week": d.get("last_week"),
        "downloads_last_month": d.get("last_month"),
        "version_split_note": (
            "Per-version counts require BigQuery (pypistats.org does not expose them). "
            "To check v4 pickup specifically, compare release-date-filtered BigQuery results."
        ),
    }


def _collect_pypi_versions() -> list[dict]:
    """Top-10 versions by recency from PyPI JSON API."""
    url = f"https://pypi.org/pypi/{PACKAGE}/json"
    data, err = _fetch_json(url)
    if err:
        return [{"error": err}]
    releases = data.get("releases", {})
    versions = []
    for ver, files in releases.items():
        if not files:
            continue
        upload_time = sorted(f.get("upload_time", "") for f in files)[-1]
        versions.append({"version": ver, "released": upload_time})
    versions.sort(key=lambda x: x["released"], reverse=True)
    return versions[:10]


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------


def collect_metrics(token: str | None = None) -> dict:
    return {
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
        "repo": REPO,
        "package": PACKAGE,
        "github": _collect_github(token),
        "github_traffic": _collect_traffic(token),
        "pypi": _collect_pypi_recent(),
        "pypi_versions": _collect_pypi_versions(),
    }


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


def _md_table(headers: list[str], rows: list[list]) -> str:
    def fmt(v):
        return "N/A" if v is None else str(v)

    lines = ["| " + " | ".join(headers) + " |", "|" + " --- |" * len(headers)]
    for row in rows:
        lines.append("| " + " | ".join(fmt(v) for v in row) + " |")
    return "\n".join(lines)


def format_markdown(m: dict) -> str:
    gh = m.get("github", {})
    traffic = m.get("github_traffic", {})
    pypi = m.get("pypi", {})
    versions = m.get("pypi_versions", [])

    sections = [
        f"# uniswap-python Adoption Snapshot",
        f"",
        f"**Snapshot date**: {m['snapshot_at']}",
        f"",
        f"## GitHub",
        f"",
        _md_table(
            ["Metric", "Value"],
            [
                ["Stars", gh.get("stars", "N/A")],
                ["Forks", gh.get("forks", "N/A")],
                ["Watchers", gh.get("watchers", "N/A")],
                ["Open Issues", gh.get("open_issues", "N/A")],
            ],
        ),
        f"",
        f"## GitHub Traffic (14-day window)",
        f"",
    ]

    if "note" in traffic:
        sections += [f"_{traffic['note']}_", ""]
    elif "error" in traffic:
        sections += [f"_Error: {traffic['error']}_", ""]
    else:
        sections += [
            _md_table(
                ["Metric", "Value"],
                [
                    ["Clones (14d)", traffic.get("clones_14d", "N/A")],
                    ["Unique Cloners (14d)", traffic.get("unique_cloners_14d", "N/A")],
                    ["Views (14d)", traffic.get("views_14d", "N/A")],
                    ["Unique Visitors (14d)", traffic.get("unique_visitors_14d", "N/A")],
                ],
            ),
            "",
        ]

    sections += [
        f"## PyPI Downloads",
        f"",
        _md_table(
            ["Period", "Downloads"],
            [
                ["Last day", pypi.get("downloads_last_day", "N/A")],
                ["Last week", pypi.get("downloads_last_week", "N/A")],
                ["Last month", pypi.get("downloads_last_month", "N/A")],
            ],
        ),
        f"",
        f"_{pypi.get('version_split_note') or pypi.get('note', '')}_",
        f"",
        f"## Recent Releases",
        f"",
        _md_table(
            ["Version", "Released"],
            [[v.get("version", "?"), v.get("released", "?")[:10]] for v in versions[:5]],
        ),
        f"",
    ]

    return "\n".join(sections)


def _delta(old, new) -> str:
    if old is None or new is None:
        return "N/A"
    try:
        d = int(new) - int(old)
        return f"+{d}" if d >= 0 else str(d)
    except (TypeError, ValueError):
        return "N/A"


def format_report(baseline: dict, current: dict) -> str:
    bg = baseline.get("github", {})
    cg = current.get("github", {})
    bp = baseline.get("pypi", {})
    cp = current.get("pypi", {})

    sections = [
        "# uniswap-python Adoption Report — Deltas",
        "",
        f"Baseline: {baseline['snapshot_at']}",
        f"Current:  {current['snapshot_at']}",
        "",
        "## GitHub",
        "",
        _md_table(
            ["Metric", "Baseline", "Current", "Delta"],
            [
                ["Stars", bg.get("stars", "N/A"), cg.get("stars", "N/A"), _delta(bg.get("stars"), cg.get("stars"))],
                ["Forks", bg.get("forks", "N/A"), cg.get("forks", "N/A"), _delta(bg.get("forks"), cg.get("forks"))],
                ["Watchers", bg.get("watchers", "N/A"), cg.get("watchers", "N/A"), _delta(bg.get("watchers"), cg.get("watchers"))],
            ],
        ),
        "",
        "## PyPI Downloads",
        "",
        _md_table(
            ["Period", "Baseline", "Current", "Delta"],
            [
                ["Last day", bp.get("downloads_last_day", "N/A"), cp.get("downloads_last_day", "N/A"),
                 _delta(bp.get("downloads_last_day"), cp.get("downloads_last_day"))],
                ["Last week", bp.get("downloads_last_week", "N/A"), cp.get("downloads_last_week", "N/A"),
                 _delta(bp.get("downloads_last_week"), cp.get("downloads_last_week"))],
                ["Last month", bp.get("downloads_last_month", "N/A"), cp.get("downloads_last_month", "N/A"),
                 _delta(bp.get("downloads_last_month"), cp.get("downloads_last_month"))],
            ],
        ),
        "",
    ]

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--out", default="metrics", help="Output directory (default: metrics/)")
    parser.add_argument(
        "--report",
        metavar="BASELINE.json",
        help="Report mode: compute deltas vs baseline snapshot",
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")

    if args.report:
        baseline_path = Path(args.report)
        if not baseline_path.exists():
            print(f"ERROR: Baseline file not found: {baseline_path}", file=sys.stderr)
            sys.exit(1)
        baseline = json.loads(baseline_path.read_text())
        current = collect_metrics(token)
        print(format_report(baseline, current))
        return

    metrics = collect_metrics(token)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    json_path = out_dir / f"adoption-{date_str}.json"
    md_path = out_dir / f"adoption-{date_str}.md"

    json_path.write_text(json.dumps(metrics, indent=2) + "\n")
    md_path.write_text(format_markdown(metrics))

    print(f"Snapshot written:\n  JSON: {json_path}\n  Markdown: {md_path}\n")

    gh = metrics.get("github", {})
    pypi = metrics.get("pypi", {})
    print(f"Stars: {gh.get('stars', 'N/A')}  Forks: {gh.get('forks', 'N/A')}  "
          f"PyPI/month: {pypi.get('downloads_last_month', 'N/A')}")


if __name__ == "__main__":
    main()
