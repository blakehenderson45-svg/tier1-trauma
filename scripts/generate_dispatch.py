#!/usr/bin/env python3
"""
Tier 1 Trauma — Automated Weekly Dispatch Generator
Fetches live league data from the public Sleeper API for Tier 1 Dynasty
and builds data/league-data.json with unbiased, league-wide, holiday-themed
weekly dispatches for all 12 leaguemates.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import statistics
import sys
import urllib.request
from pathlib import Path
from typing import Any

LEAGUE_ID = os.environ.get("SLEEPER_LEAGUE_ID", "1398719645564796928")
SLEEPER_BASE = "https://api.sleeper.app/v1"
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
PLAYERS_CACHE = DATA_DIR / "players-cache.json"
OUTPUT_FILE = DATA_DIR / "league-data.json"


# Holiday & Seasonal Theme Mixups keyed by NFL regular/postseason week number.
# Each week pairs the signature Tier 1 Trauma medical/gridiron motif with a
# timely holiday or calendar mixup so every Tuesday dispatch feels fresh.
WEEK_THEMES: dict[int, dict[str, Any]] = {
    1: {
        "id": "labor-day",
        "holiday": "Labor Day",
        "edition": "Labor Day Intake",
        "accent": "#3B82F6",
        "accent_soft": "rgba(59, 130, 246, 0.16)",
        "tagline": "No days off in the Tier 1 Trauma ward — Opening Week vitals are in.",
        "awards": {
            "high": ("Employee of the Week", "Clocked the heaviest shift of Opening Week."),
            "low": ("Called In Sick", "No-showed the Labor Day shift."),
            "close": ("Overtime Shift", "Narrowest margin of the opener."),
            "upset": ("Union Walkout", "Biggest opening-week statement."),
            "bench": ("Left on Break", "Highest-scoring starter left sitting on the bench."),
        },
        "verbs": ("clocked", "steamrolled", "handled"),
    },
    2: {
        "id": "harvest-moon",
        "holiday": "Harvest Moon",
        "edition": "Harvest Moon Triage",
        "accent": "#D97706",
        "accent_soft": "rgba(217, 119, 6, 0.16)",
        "tagline": "Full moon over the trauma ward — weird bounce-backs and early panic.",
        "awards": {
            "high": ("Apex Howler", "Lit up the Week 2 scoreboard under the Harvest Moon."),
            "low": ("Lunar Eclipse", "Completely vanished under the floodlights."),
            "close": ("Silver Bullet Escape", "Survived the tightest finish of the week."),
            "upset": ("Full Moon Madness", "Biggest shockwave of Week 2."),
            "bench": ("Left in the Dark", "Biggest point explosion stranded on the pine."),
        },
        "verbs": ("eclipsed", "torched", "outlasted"),
    },
    3: {
        "id": "equinox",
        "holiday": "Autumn Equinox",
        "edition": "Equinox Flatline",
        "accent": "#C26D2D",
        "accent_soft": "rgba(194, 109, 45, 0.16)",
        "tagline": "Equal day, equal night — wildly unequal fantasy point totals.",
        "awards": {
            "high": ("Peak Season", "Hottest lineup as fall officially arrived."),
            "low": ("Early Frost", "Lineup went ice cold on the first day of autumn."),
            "close": ("Razor Balance", "Decided by the slimmest margin of the equinox."),
            "upset": ("Seasonal Shift", "Flipped the early standings upside down."),
            "bench": ("Fallen Leaves", "Left a pile of points raked onto the bench."),
        },
        "verbs": ("froze out", "flattened", "edged"),
    },
    4: {
        "id": "oktoberfest",
        "holiday": "Oktoberfest",
        "edition": "Oktoberfest Trauma Ward",
        "accent": "#CA8A04",
        "accent_soft": "rgba(202, 138, 4, 0.16)",
        "tagline": "Steins raised, lineups toasted, and a few managers nursing heavy hangovers.",
        "awards": {
            "high": ("King of the Beer Hall", "Poured the biggest point total of Week 4."),
            "low": ("Flat Keg", "Nothing left on tap in Week 4."),
            "close": ("Last Call Escape", "Snuck out a win right before closing time."),
            "upset": ("Bavarian Ambush", "Spilled a contender's stein in broad daylight."),
            "bench": ("Untapped Reserve", "Best performer left sitting in the cellar."),
        },
        "verbs": ("toasted", "crushed", "outlasted"),
    },
    5: {
        "id": "indigenous-peoples",
        "holiday": "October Long Weekend",
        "edition": "October Triage Expedition",
        "accent": "#B45309",
        "accent_soft": "rgba(180, 83, 9, 0.16)",
        "tagline": "Uncharted territory as bye weeks begin and contender tiers separate.",
        "awards": {
            "high": ("Trailblazer", "Charted the highest score of Week 5."),
            "low": ("Lost at Sea", "Drifted well below the league pulse."),
            "close": ("Photo Finish", "Tightest survival of the long weekend."),
            "upset": ("Mutiny on Deck", "Biggest standings shaker of Week 5."),
            "bench": ("Stranded Cargo", "Biggest star left behind on the bench."),
        },
        "verbs": ("charted past", "sank", "outmaneuvered"),
    },
    6: {
        "id": "midseason-checkup",
        "holiday": "Sweetest Day & Midseason",
        "edition": "Midseason Autopsy",
        "accent": "#E11D48",
        "accent_soft": "rgba(225, 29, 72, 0.16)",
        "tagline": "Six weeks in: no more small-sample excuses in the Tier 1 ward.",
        "awards": {
            "high": ("Sweetest Victory", "Delivered the cleanest clinical beatdown of Week 6."),
            "low": ("Bitter Pill", "Hardest Week 6 score to swallow."),
            "close": ("Heartbeat Away", "Barely kept a pulse to steal the W."),
            "upset": ("Heartbreaker", "Pulled off the cruelest upset of Week 6."),
            "bench": ("Left Unopened", "Sweetest stat line wasted on the bench."),
        },
        "verbs": ("dissected", "overwhelmed", "survived"),
    },
    7: {
        "id": "haunted-ward",
        "holiday": "Spooky Season",
        "edition": "Haunted Ward Intake",
        "accent": "#EA580C",
        "accent_soft": "rgba(234, 88, 12, 0.16)",
        "tagline": "Ghostly projections and nightmare matchups as Halloween approaches.",
        "awards": {
            "high": ("Apex Predator", "Terrorized the league scoreboard in Week 7."),
            "low": ("Ghost Town", "Lineup pulled a full disappearing act."),
            "close": ("Final Girl Survival", "Escaped Week 7 by the skin of their teeth."),
            "upset": ("Jump Scare", "Ambushed a higher seed out of nowhere."),
            "bench": ("Buried Alive", "Monster performance entombed on the bench."),
        },
        "verbs": ("haunted", "shredded", "escaped"),
    },
    8: {
        "id": "halloween",
        "holiday": "Halloween",
        "edition": "Halloween Bloodbath",
        "accent": "#F97316",
        "accent_soft": "rgba(249, 115, 22, 0.16)",
        "tagline": "All tricks, no treats — a full Code Red horror show across Tier 1.",
        "awards": {
            "high": ("Full-Size Candy Bar", "Handed out the scariest point total of Halloween week."),
            "low": ("Bag of Rocks", "Pure nightmare fuel at the bottom of the scoreboard."),
            "close": ("Midnight Escape", "Survived the closest thriller of the night."),
            "upset": ("Poltergeist Upset", "Knocked off a contender in the dark."),
            "bench": ("Skeleton on the Bench", "Left a monster stat line locked in the closet."),
        },
        "verbs": ("carved up", "terrified", "survived"),
    },
    9: {
        "id": "daylight-saving",
        "holiday": "Daylight Saving & Election Week",
        "edition": "Fall Back Flatline",
        "accent": "#0EA5E9",
        "accent_soft": "rgba(14, 165, 233, 0.16)",
        "tagline": "Clocks fell back an hour, and several playoff hopes fell back a full game.",
        "awards": {
            "high": ("Landslide Victory", "Ran away with the Week 9 popular vote."),
            "low": ("Recount Required", "Lineup never even showed up to the polls."),
            "close": ("Too Close to Call", "Needed every decimal point to survive."),
            "upset": ("Polling Error", "Defied the standings to snatch a huge W."),
            "bench": ("Unclaimed Ballot", "Game-changing points left sitting on the bench."),
        },
        "verbs": ("swept", "outvoted", "edged"),
    },
    10: {
        "id": "veterans-day",
        "holiday": "Veterans Day Week",
        "edition": "Week 10 Bloodbath",
        "accent": "#DC2626",
        "accent_soft": "rgba(220, 38, 38, 0.16)",
        "tagline": "Heavy artillery at the top of the table as the playoff stretch begins.",
        "awards": {
            "high": ("Top Trauma Unit", "Unleashed the heaviest barrage of Week 10."),
            "low": ("Flatline Watch", "Lowest vital signs across the entire ward."),
            "close": ("Trench Survival", "Ground out the tightest margin of the week."),
            "upset": ("Ambush of the Week", "Stunned a higher-seeded heavyweight."),
            "bench": ("Reserve Artillery", "Left maximum firepower unused on the bench."),
        },
        "verbs": ("obliterated", "blasted", "ground past"),
    },
    11: {
        "id": "thanksgiving",
        "holiday": "Thanksgiving",
        "edition": "Thanksgiving Carving",
        "accent": "#D9822B",
        "accent_soft": "rgba(217, 130, 43, 0.16)",
        "tagline": "Carving knives out before the turkey hits the table — the playoff moat is set.",
        "awards": {
            "high": ("Head of the Table", "Carved up the league for the biggest feast of Week 11."),
            "low": ("Stuffed & Cold", "Leftover-grade scoring at the bottom of the ward."),
            "close": ("Turkey Steal", "Snatched the narrowest escape right off the platter."),
            "upset": ("Kids' Table Ambush", "Crashed the grown-ups' table for a massive upset."),
            "bench": ("Left in the Oven", "Cooked up huge points — and forgot to serve them."),
        },
        "verbs": ("carved up", "stuffed", "snatched a win from"),
    },
    12: {
        "id": "black-friday",
        "holiday": "Black Friday & Cyber Monday",
        "edition": "Black Friday Clearance",
        "accent": "#EAB308",
        "accent_soft": "rgba(234, 179, 8, 0.16)",
        "tagline": "Doorbuster blowouts and discounted playoff dreams two weeks from the bracket.",
        "awards": {
            "high": ("Doorbuster Special", "Dropped the loudest point total of Black Friday week."),
            "low": ("Out of Stock", "Shelves completely bare when it mattered most."),
            "close": ("Checkout Line Steal", "Snuck out the tightest win at the register."),
            "upset": ("Clearance Ambush", "Discounted a playoff contender in prime time."),
            "bench": ("Left in the Cart", "Monster scorer left unpurchased on the bench."),
        },
        "verbs": ("marked down", "cleaned out", "outbid"),
    },
    13: {
        "id": "december-kickoff",
        "holiday": "Giving Tuesday & December Freeze",
        "edition": "December Code Blue",
        "accent": "#38BDF8",
        "accent_soft": "rgba(56, 189, 248, 0.16)",
        "tagline": "Winter arrives in Tier 1 — penultimate regular-season triage before brackets lock.",
        "awards": {
            "high": ("Blizzard Warning", "Buried the competition under a mountain of points."),
            "low": ("Hypothermia Watch", "Vital signs plummeted in the December cold."),
            "close": ("Thin Ice Survival", "Skated away with the week's narrowest win."),
            "upset": ("Cold-Blooded Upset", "Put a contender's seed on ice."),
            "bench": ("Frozen on the Bench", "Left a red-hot scorer out in the snow."),
        },
        "verbs": ("buried", "froze out", "slipped past"),
    },
    14: {
        "id": "final-triage",
        "holiday": "Regular Season Finale",
        "edition": "Final Triage & Cut-Line Judgment",
        "accent": "#EF4444",
        "accent_soft": "rgba(239, 68, 68, 0.16)",
        "tagline": "Last call for the Week 15 bracket — six survive, six head to the Max PF lottery.",
        "awards": {
            "high": ("Final Boss", "Closed the regular season with a statement eruption."),
            "low": ("DOA at the Cutoff", "Limped across the regular-season finish line."),
            "close": ("Buzzer-Beater Pulse", "Kept the heartbeat alive by a fraction."),
            "upset": ("Spoiler Alert", "Played ultimate spoiler on Finale Sunday."),
            "bench": ("Regret of the Season", "Biggest Week 14 explosion stranded on the bench."),
        },
        "verbs": ("dispatched", "eliminated", "edged"),
    },
    15: {
        "id": "holiday-playoffs",
        "holiday": "Hanukkah & Playoff Opening",
        "edition": "Holiday Playoff Intake",
        "accent": "#3B82F6",
        "accent_soft": "rgba(59, 130, 246, 0.16)",
        "tagline": "Win or go to the morgue — Tier 1 postseason triage is officially live.",
        "awards": {
            "high": ("Festival of Points", "Lit up Round 1 with the brightest scoreboard."),
            "low": ("First-Round Flatline", "Postseason pulse faded early."),
            "close": ("Miracle Survival", "Escaped elimination by the tightest margin."),
            "upset": ("Bracket Buster", "Shook up the playoff tree in Round 1."),
            "bench": ("Unlit Candle", "Massive stat line left on the sideline."),
        },
        "verbs": ("torched", "bounced", "survived"),
    },
    16: {
        "id": "christmas",
        "holiday": "Christmas",
        "edition": "Christmas Trauma Ward",
        "accent": "#22C55E",
        "accent_soft": "rgba(34, 197, 94, 0.16)",
        "tagline": "Semifinal carnage under the mistletoe — nice-list blowouts and coal-filled stockings.",
        "awards": {
            "high": ("Top of the Nice List", "Delivered a gift-wrapped semifinal explosion."),
            "low": ("Lump of Coal", "Nothing but coal in the Week 16 box score."),
            "close": ("Miracle on Trauma Street", "Pulled off a holiday-miracle finish."),
            "upset": ("Grinch Steal", "Stole a championship ticket right out of the sleigh."),
            "bench": ("Unwrapped Gift", "Best player left sitting under the tree."),
        },
        "verbs": ("gift-wrapped", "sledged", "stole a win from"),
    },
    17: {
        "id": "new-years",
        "holiday": "New Year's",
        "edition": "New Year's Championship Flatline",
        "accent": "#EAB308",
        "accent_soft": "rgba(234, 179, 8, 0.16)",
        "tagline": "Pop the champagne or call time of death — a Tier 1 Dynasty champion is crowned.",
        "awards": {
            "high": ("Champagne Toast", "Capped the season with the loudest Week 17 score."),
            "low": ("Midnight Hangover", "Rough way to ring in the offseason."),
            "close": ("Ball-Drop Finish", "Decided at the stroke of midnight."),
            "upset": ("New Year's Shock", "Closed the year with an unforgettable stunner."),
            "bench": ("Left in Last Year", "Huge performance left behind on the bench."),
        },
        "verbs": ("crowned themselves over", "closed out", "outlasted"),
    },
}


def fetch_json(url: str, timeout: int = 25) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Tier1Trauma-DispatchBot/1.0 (+https://github.com/blakehenderson45-svg/tier1-trauma)"
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_or_fetch_players(needed_ids: set[str]) -> dict[str, dict[str, str]]:
    """Fetch NFL player directory from Sleeper and persist only rostered players."""
    cached: dict[str, dict[str, str]] = {}
    if PLAYERS_CACHE.exists():
        try:
            cached = json.loads(PLAYERS_CACHE.read_text(encoding="utf-8"))
        except Exception:
            cached = {}

    missing = [pid for pid in needed_ids if pid not in cached and not pid.isalpha()]
    if not missing and cached:
        return cached

    print(f"Fetching Sleeper NFL player directory ({len(missing)} uncached IDs)...", file=sys.stderr)
    all_players = fetch_json(f"{SLEEPER_BASE}/players/nfl", timeout=45)
    for pid in needed_ids:
        if pid.isalpha():
            cached[pid] = {"name": f"{pid} D/ST", "pos": "DEF", "team": pid}
            continue
        p = all_players.get(pid)
        if p:
            full = p.get("full_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or pid
            cached[pid] = {
                "name": full,
                "pos": p.get("position") or "FLEX",
                "team": p.get("team") or "FA",
            }
        else:
            cached[pid] = {"name": f"Player {pid}", "pos": "FLEX", "team": "FA"}

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PLAYERS_CACHE.write_text(json.dumps(cached, indent=2, sort_keys=True), encoding="utf-8")
    return cached


def round2(val: float) -> float:
    return round(float(val), 2)


def get_theme(week: int) -> dict[str, Any]:
    if week in WEEK_THEMES:
        return WEEK_THEMES[week]
    return {
        "id": f"week-{week}",
        "holiday": f"Week {week}",
        "edition": f"Week {week} Triage",
        "accent": "#E53935",
        "accent_soft": "rgba(229, 57, 53, 0.16)",
        "tagline": "Weekly vitals from the Tier 1 Trauma ward.",
        "awards": {
            "high": ("Top Trauma Unit", "Highest score of the week."),
            "low": ("Flatline Watch", "Lowest score of the week."),
            "close": ("Narrowest Escape", "Tightest victory of the week."),
            "upset": ("Upset of the Week", "Biggest standings stunner."),
            "bench": ("Bench Malpractice", "Highest-scoring player left on the bench."),
        },
        "verbs": ("handled", "routed", "edged"),
    }


def dispatch_date_for_week(season: int, week: int) -> str:
    """Compute the Tuesday morning dispatch date for a given NFL season & week."""
    # NFL 2026 Week 1 Tuesday after MNF is Sept 15, 2026.
    # More generally, find the first Thursday of September + 12 days = Week 1 Tuesday.
    sept1 = dt.date(season, 9, 1)
    # Find first Monday (Labor Day) -> Week 1 kicks off Thursday after Labor Day -> MNF is 7 days after Labor Day -> Dispatch Tuesday is 8 days after Labor Day.
    days_to_monday = (0 - sept1.weekday()) % 7
    labor_day = sept1 + dt.timedelta(days=days_to_monday)
    week1_tuesday = labor_day + dt.timedelta(days=8)
    target = week1_tuesday + dt.timedelta(days=7 * (week - 1))
    return target.strftime("%b %d, %Y")


def next_tuesday_iso() -> str:
    """Return ISO timestamp for next Tuesday at 06:30 AM America/Los_Angeles (14:30 UTC)."""
    now = dt.datetime.now(dt.timezone.utc)
    days_ahead = (1 - now.weekday()) % 7  # 1 = Tuesday
    candidate = now.replace(hour=14, minute=30, second=0, microsecond=0) + dt.timedelta(days=days_ahead)
    if candidate <= now:
        candidate += dt.timedelta(days=7)
    return candidate.isoformat().replace("+00:00", "Z")


def format_streak(streak_type: str, count: int) -> str:
    if not streak_type or count <= 0:
        return "-"
    return f"{streak_type}{count}"


def build_data() -> dict[str, Any]:
    league = fetch_json(f"{SLEEPER_BASE}/league/{LEAGUE_ID}")
    nfl_state = fetch_json(f"{SLEEPER_BASE}/state/nfl")
    users = fetch_json(f"{SLEEPER_BASE}/league/{LEAGUE_ID}/users")
    rosters = fetch_json(f"{SLEEPER_BASE}/league/{LEAGUE_ID}/rosters")

    season = int(league.get("season", 2026))
    playoff_teams = int(league.get("settings", {}).get("playoff_teams", 6))
    playoff_week_start = int(league.get("settings", {}).get("playoff_week_start", 15))
    leg = int(league.get("settings", {}).get("leg", 1))
    display_week = int(nfl_state.get("display_week") or leg)
    # Determine highest completed week by checking matchups with non-zero points
    max_probe_week = min(17, max(leg, display_week))

    user_map = {u["user_id"]: u for u in users}
    teams_by_roster: dict[int, dict[str, Any]] = {}
    for r in rosters:
        rid = int(r["roster_id"])
        u = user_map.get(r.get("owner_id"), {})
        meta = u.get("metadata") or {}
        team_name = (meta.get("team_name") or u.get("display_name") or f"Team {rid}").strip()
        # Normalize curly apostrophes for cleaner search/display consistency
        team_name = team_name.replace("\u2019", "'")
        manager = u.get("display_name") or f"Manager {rid}"
        avatar_id = meta.get("avatar") or u.get("avatar")
        if avatar_id and not str(avatar_id).startswith("http"):
            avatar_url = f"https://sleepercdn.com/avatars/thumbs/{avatar_id}"
        else:
            avatar_url = avatar_id or ""

        s = r.get("settings") or {}
        pf = round2(s.get("fpts", 0) + s.get("fpts_decimal", 0) / 100.0)
        max_pf = round2(s.get("ppts", 0) + s.get("ppts_decimal", 0) / 100.0)
        pa = round2(s.get("fpts_against", 0) + s.get("fpts_against_decimal", 0) / 100.0)
        teams_by_roster[rid] = {
            "roster_id": rid,
            "team_name": team_name,
            "manager": manager,
            "avatar": avatar_url,
            "wins": int(s.get("wins", 0)),
            "losses": int(s.get("losses", 0)),
            "ties": int(s.get("ties", 0)),
            "pf": pf,
            "max_pf": max_pf,
            "pa": pa,
            "efficiency": round2((pf / max_pf * 100.0) if max_pf > 0 else 0.0),
        }

    # Fetch all matchups for weeks 1..max_probe_week
    raw_matchups_by_week: dict[int, list[dict[str, Any]]] = {}
    needed_player_ids: set[str] = set()
    completed_weeks: list[int] = []

    for w in range(1, max_probe_week + 1):
        mdata = fetch_json(f"{SLEEPER_BASE}/league/{LEAGUE_ID}/matchups/{w}")
        if not mdata:
            continue
        total_pts = sum(float(entry.get("points") or 0.0) for entry in mdata)
        if total_pts <= 0:
            continue
        completed_weeks.append(w)
        raw_matchups_by_week[w] = mdata
        for entry in mdata:
            for pid in (entry.get("players") or []):
                needed_player_ids.add(str(pid))

    players = load_or_fetch_players(needed_player_ids)

    # Track cumulative stats per roster week-by-week so archive weeks show exact
    # standings, streaks, all-play records, and playoff seedings as of that week!
    cum: dict[int, dict[str, Any]] = {
        rid: {
            "wins": 0,
            "losses": 0,
            "ties": 0,
            "pf": 0.0,
            "pa": 0.0,
            "streak_type": "",
            "streak_len": 0,
            "all_play_w": 0,
            "all_play_l": 0,
            "weekly_scores": [],
        }
        for rid in teams_by_roster
    }

    weeks_out: list[dict[str, Any]] = []
    latest_week = completed_weeks[-1] if completed_weeks else 1

    for w in completed_weeks:
        mdata = raw_matchups_by_week[w]
        theme = get_theme(w)

        # Group by matchup_id
        by_mid: dict[int, list[dict[str, Any]]] = {}
        for entry in mdata:
            mid = entry.get("matchup_id")
            if mid is None:
                continue
            by_mid.setdefault(int(mid), []).append(entry)

        # Compute pre-week ranks for upset detection
        pre_ranks: dict[int, int] = {}
        if w > 1:
            pre_sorted = sorted(
                teams_by_roster.keys(),
                key=lambda r: (cum[r]["wins"], cum[r]["pf"], cum[r]["pa"]),
                reverse=True,
            )
            pre_ranks = {r: idx + 1 for idx, r in enumerate(pre_sorted)}

        # Compute all-play for this week
        week_scores_list = [(int(e["roster_id"]), round2(float(e.get("points") or 0.0))) for e in mdata]
        scores_only = [pts for _, pts in week_scores_list]
        mean_score = round2(statistics.mean(scores_only)) if scores_only else 0.0
        median_score = round2(statistics.median(scores_only)) if scores_only else 0.0

        for rid, pts in week_scores_list:
            ap_w = sum(1 for orid, opts in week_scores_list if orid != rid and pts > opts)
            ap_l = sum(1 for orid, opts in week_scores_list if orid != rid and pts < opts)
            cum[rid]["all_play_w"] += ap_w
            cum[rid]["all_play_l"] += ap_l
            cum[rid]["weekly_scores"].append({"week": w, "points": pts})

        matchups_out: list[dict[str, Any]] = []
        bench_regrets: list[dict[str, Any]] = []
        top_starters_league: list[dict[str, Any]] = []
        winner_ids: set[int] = set()

        def extract_lineup(entry: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
            pp = entry.get("players_points") or {}
            starters_set = set(str(x) for x in (entry.get("starters") or []) if x and x != "0")
            starters_list = []
            bench_list = []
            for pid_raw, pval in pp.items():
                pid = str(pid_raw)
                pinfo = players.get(pid, {"name": f"Player {pid}", "pos": "FLEX", "team": "FA"})
                item = {
                    "id": pid,
                    "name": pinfo["name"],
                    "pos": pinfo["pos"],
                    "team": pinfo["team"],
                    "points": round2(float(pval or 0.0)),
                }
                if pid in starters_set:
                    starters_list.append(item)
                else:
                    bench_list.append(item)
            starters_list.sort(key=lambda x: x["points"], reverse=True)
            bench_list.sort(key=lambda x: x["points"], reverse=True)
            return starters_list, bench_list

        for mid, pair in by_mid.items():
            if len(pair) != 2:
                continue
            a, b = pair[0], pair[1]
            pts_a = round2(float(a.get("points") or 0.0))
            pts_b = round2(float(b.get("points") or 0.0))
            if pts_a >= pts_b:
                win_e, lose_e = a, b
                win_pts, lose_pts = pts_a, pts_b
            else:
                win_e, lose_e = b, a
                win_pts, lose_pts = pts_b, pts_a

            wid = int(win_e["roster_id"])
            lid = int(lose_e["roster_id"])
            is_tie = abs(win_pts - lose_pts) < 0.001
            margin = round2(win_pts - lose_pts)

            # Update cumulative records
            cum[wid]["pf"] = round2(cum[wid]["pf"] + win_pts)
            cum[wid]["pa"] = round2(cum[wid]["pa"] + lose_pts)
            cum[lid]["pf"] = round2(cum[lid]["pf"] + lose_pts)
            cum[lid]["pa"] = round2(cum[lid]["pa"] + win_pts)

            if is_tie:
                cum[wid]["ties"] += 1
                cum[lid]["ties"] += 1
            else:
                winner_ids.add(wid)
                cum[wid]["wins"] += 1
                cum[lid]["losses"] += 1
                if cum[wid]["streak_type"] == "W":
                    cum[wid]["streak_len"] += 1
                else:
                    cum[wid]["streak_type"] = "W"
                    cum[wid]["streak_len"] = 1
                if cum[lid]["streak_type"] == "L":
                    cum[lid]["streak_len"] += 1
                else:
                    cum[lid]["streak_type"] = "L"
                    cum[lid]["streak_len"] = 1

            w_starters, w_bench = extract_lineup(win_e)
            l_starters, l_bench = extract_lineup(lose_e)

            for st in w_starters[:2]:
                top_starters_league.append({**st, "team_name": teams_by_roster[wid]["team_name"], "roster_id": wid})
            for st in l_starters[:2]:
                top_starters_league.append({**st, "team_name": teams_by_roster[lid]["team_name"], "roster_id": lid})

            for rid_x, b_list, won_flag, m_val in [(wid, w_bench, True, margin), (lid, l_bench, False, margin)]:
                if b_list:
                    top_b = b_list[0]
                    bench_regrets.append({
                        "roster_id": rid_x,
                        "team_name": teams_by_roster[rid_x]["team_name"],
                        "player_name": top_b["name"],
                        "pos": top_b["pos"],
                        "points": top_b["points"],
                        "lost_matchup": not won_flag,
                        "margin": m_val,
                    })

            # Upset score: difference in pre-week rank (positive if lower-ranked team beat higher-ranked team)
            upset_delta = 0
            if pre_ranks and not is_tie:
                upset_delta = pre_ranks.get(wid, 6) - pre_ranks.get(lid, 6)

            w_mvp = w_starters[0] if w_starters else None
            l_mvp = l_starters[0] if l_starters else None
            l_top_bench = l_bench[0] if l_bench else None

            # Craft unbiased, fun, holiday-flavored triage note
            w_name = teams_by_roster[wid]["team_name"]
            l_name = teams_by_roster[lid]["team_name"]
            combined = round2(win_pts + lose_pts)
            verb_big, verb_mid, verb_close = theme["verbs"]

            if margin >= 60:
                triage_note = (
                    f"Code Blue blowout by {margin:.2f} pts: "
                    f"{w_mvp['name']} ({w_mvp['points']:.1f}) led {w_name} as they {verb_big} {l_name}."
                    if w_mvp else f"Code Blue blowout by {margin:.2f} pts."
                )
            elif combined >= mean_score * 2.45:
                triage_note = (
                    f"Shootout of the week ({combined:.2f} combined): "
                    f"{w_mvp['name']} ({w_mvp['points']:.1f}) helped {w_name} outgun "
                    f"{l_mvp['name']} ({l_mvp['points']:.1f}) by {margin:.2f} pts."
                    if w_mvp and l_mvp else f"High-scoring shootout ({combined:.2f} combined)."
                )
            elif margin <= 8.0:
                triage_note = (
                    f"Razor-thin escape by {margin:.2f} pts: "
                    f"{w_name} {verb_close} {l_name} behind {w_mvp['name']}'s {w_mvp['points']:.1f} pts."
                    if w_mvp else f"Razor-thin escape by {margin:.2f} pts."
                )
            elif l_top_bench and l_top_bench["points"] >= 18.0 and l_top_bench["points"] > margin * 0.6:
                triage_note = (
                    f"Bench malpractice watch: {l_name} left {l_top_bench['name']} ({l_top_bench['points']:.1f} pts) "
                    f"on the pine as {w_name} took it by {margin:.2f}."
                )
            elif win_pts < mean_score:
                triage_note = (
                    f"Ugly survival: {w_name} won by {margin:.2f} despite scoring "
                    f"{round2(mean_score - win_pts):.2f} below the league average."
                )
            else:
                triage_note = (
                    f"{w_mvp['name']} ({w_mvp['points']:.1f}) paced {w_name} past {l_name} "
                    f"by {margin:.2f} pts"
                    + (f", erasing {l_mvp['name']}'s {l_mvp['points']:.1f}." if l_mvp and l_mvp["points"] >= 22 else ".")
                    if w_mvp else f"{w_name} defeated {l_name} by {margin:.2f} pts."
                )

            matchups_out.append({
                "matchup_id": mid,
                "winner": {
                    "roster_id": wid,
                    "team_name": w_name,
                    "manager": teams_by_roster[wid]["manager"],
                    "avatar": teams_by_roster[wid]["avatar"],
                    "points": win_pts,
                    "record": f"{cum[wid]['wins']}-{cum[wid]['losses']}",
                    "top_starters": w_starters[:4],
                    "top_bench": w_bench[:2],
                },
                "loser": {
                    "roster_id": lid,
                    "team_name": l_name,
                    "manager": teams_by_roster[lid]["manager"],
                    "avatar": teams_by_roster[lid]["avatar"],
                    "points": lose_pts,
                    "record": f"{cum[lid]['wins']}-{cum[lid]['losses']}",
                    "top_starters": l_starters[:4],
                    "top_bench": l_bench[:2],
                },
                "margin": margin,
                "combined": combined,
                "upset_delta": upset_delta,
                "triage_note": triage_note,
            })

        # Sort matchups from highest winning score down (cleanest carving -> ugliest trench fight)
        matchups_out.sort(key=lambda m: (m["winner"]["points"], m["combined"]), reverse=True)

        # Build week standings snapshot
        standings_rows = []
        for rid, t in teams_by_roster.items():
            c = cum[rid]
            standings_rows.append({
                "roster_id": rid,
                "team_name": t["team_name"],
                "manager": t["manager"],
                "avatar": t["avatar"],
                "wins": c["wins"],
                "losses": c["losses"],
                "ties": c["ties"],
                "record": f"{c['wins']}-{c['losses']}" + (f"-{c['ties']}" if c["ties"] else ""),
                "streak": format_streak(c["streak_type"], c["streak_len"]),
                "pf": round2(c["pf"]),
                "max_pf": t["max_pf"] if w == latest_week else None,
                "pa": round2(c["pa"]),
                "all_play": f"{c['all_play_w']}-{c['all_play_l']}",
                "all_play_pct": round2(
                    c["all_play_w"] / max(1, c["all_play_w"] + c["all_play_l"]) * 100.0
                ),
            })
        standings_rows.sort(key=lambda r: (r["wins"], r["pf"], r["pa"]), reverse=True)
        for idx, row in enumerate(standings_rows, start=1):
            row["rank"] = idx

        # Scoring distribution (sorted highest to lowest)
        scoring_bars = []
        opp_lookup = {}
        for m in matchups_out:
            opp_lookup[m["winner"]["roster_id"]] = (m["loser"]["team_name"], m["margin"], True)
            opp_lookup[m["loser"]["roster_id"]] = (m["winner"]["team_name"], -m["margin"], False)

        for rid, pts in sorted(week_scores_list, key=lambda x: x[1], reverse=True):
            opp_name, signed_margin, won = opp_lookup.get(rid, ("", 0.0, False))
            scoring_bars.append({
                "roster_id": rid,
                "team_name": teams_by_roster[rid]["team_name"],
                "manager": teams_by_roster[rid]["manager"],
                "points": pts,
                "won": won,
                "opponent": opp_name,
                "margin": signed_margin,
            })

        # Weekly Awards (completely unbiased, league-wide)
        high_bar = scoring_bars[0]
        low_bar = scoring_bars[-1]
        closest_m = min(matchups_out, key=lambda m: m["margin"])
        upset_m = max(matchups_out, key=lambda m: (m["upset_delta"], -m["margin"]))
        # Bench malpractice: prioritize losing teams with huge bench points, else highest overall bench player
        bench_regrets.sort(key=lambda b: (b["points"] + (6.0 if b["lost_matchup"] else 0.0)), reverse=True)
        worst_bench = bench_regrets[0] if bench_regrets else None
        top_starters_league.sort(key=lambda s: s["points"], reverse=True)

        aw = theme["awards"]
        awards_out = [
            {
                "key": "high",
                "title": aw["high"][0],
                "team": high_bar["team_name"],
                "stat": f"{high_bar['points']:.2f} pts",
                "detail": f"+{round2(high_bar['points'] - mean_score):.2f} above league average ({mean_score:.2f}).",
            },
            {
                "key": "low",
                "title": aw["low"][0],
                "team": low_bar["team_name"],
                "stat": f"{low_bar['points']:.2f} pts",
                "detail": f"{round2(mean_score - low_bar['points']):.2f} pts below the Week {w} mean.",
            },
            {
                "key": "close",
                "title": aw["close"][0],
                "team": closest_m["winner"]["team_name"],
                "stat": f"+{closest_m['margin']:.2f} pts",
                "detail": f"Edged {closest_m['loser']['team_name']} ({closest_m['winner']['points']:.2f}–{closest_m['loser']['points']:.2f}).",
            },
        ]
        shootout_m = max(matchups_out, key=lambda m: m["combined"])
        if upset_m["upset_delta"] > 0 and upset_m["matchup_id"] != closest_m["matchup_id"]:
            awards_out.append({
                "key": "upset",
                "title": aw["upset"][0],
                "team": upset_m["winner"]["team_name"],
                "stat": f"#{pre_ranks[upset_m['winner']['roster_id']]} over #{pre_ranks[upset_m['loser']['roster_id']]}",
                "detail": f"Knocked off {upset_m['loser']['team_name']} {upset_m['winner']['points']:.2f}–{upset_m['loser']['points']:.2f}.",
            })
        else:
            awards_out.append({
                "key": "shootout",
                "title": "Shootout of the Week",
                "team": f"{shootout_m['winner']['team_name']} vs {shootout_m['loser']['team_name']}",
                "stat": f"{shootout_m['combined']:.2f} pts",
                "detail": f"{shootout_m['winner']['team_name']} took the firefight {shootout_m['winner']['points']:.2f}–{shootout_m['loser']['points']:.2f}.",
            })
        if worst_bench:
            awards_out.append({
                "key": "bench",
                "title": aw["bench"][0],
                "team": worst_bench["team_name"],
                "stat": f"{worst_bench['points']:.1f} pts",
                "detail": f"Left {worst_bench['player_name']} ({worst_bench['pos']}) on the bench"
                + (" in a loss." if worst_bench["lost_matchup"] else "."),
            })

        # Unbiased Hero Headline & Editorial Ward Report
        high_matchup = next(m for m in matchups_out if m["winner"]["roster_id"] == high_bar["roster_id"])
        leader1, leader2 = standings_rows[0], standings_rows[1]
        seed6, seed7 = standings_rows[playoff_teams - 1], standings_rows[playoff_teams]
        bubble_gap = seed6["wins"] - seed7["wins"]
        weeks_left = max(0, playoff_week_start - 1 - w)

        deck = (
            f"{high_bar['team_name']} {theme['verbs'][0]} {high_matchup['loser']['team_name']} "
            f"for {high_bar['points']:.2f} points to pace Week {w}, while "
            f"{closest_m['winner']['team_name']} survived a {closest_m['winner']['points']:.2f}–"
            f"{closest_m['loser']['points']:.2f} nail-biter over {closest_m['loser']['team_name']} "
            f"in {league.get('name', 'Tier 1 Dynasty')}."
        )

        if bubble_gap >= 2:
            gap_phrase = f"two full games ({bubble_gap}W) clear of the #{playoff_teams + 1} bubble"
        elif bubble_gap == 1:
            gap_phrase = f"one game ahead of the #{playoff_teams + 1} bubble"
        else:
            gap_phrase = f"locked in a dead-heat tiebreaker battle with {seed7['team_name']}"

        ward_headline = (
            f"{leader1['team_name']} Leads the Ward as Playoff Lines Sharpen"
            if w >= 8
            else f"{leader1['team_name']} Sets the Pace in {theme['edition']}"
        )

        ward_p1 = (
            f"Coming out of Week {w} ({theme['holiday']}), {leader1['team_name']} ({leader1['record']}, {leader1['streak']}) "
            f"and {leader2['team_name']} ({leader2['record']}, {leader2['streak']}) sit atop the Tier 1 standings. "
            f"At the cutoff, {seed6['team_name']} ({seed6['record']}) holds the #{playoff_teams} seed — {gap_phrase} "
            f"with {weeks_left} regular-season {'week' if weeks_left == 1 else 'weeks'} remaining before the Week {playoff_week_start} bracket."
            if w < playoff_week_start
            else f"Postseason triage is underway in Week {w} ({theme['holiday']}), led by {high_bar['team_name']}'s {high_bar['points']:.2f}-point surge."
        )

        mvp1 = top_starters_league[0] if top_starters_league else None
        mvp2 = top_starters_league[1] if len(top_starters_league) > 1 else None
        ward_p2 = (
            f"Six teams cleared the {median_score:.2f} median while {low_bar['team_name']} "
            f"hit the week's floor at {low_bar['points']:.2f}. "
            + (
                f"Individual fireworks were headlined by {mvp1['name']} ({mvp1['points']:.1f} pts for {mvp1['team_name']})"
                + (f" and {mvp2['name']} ({mvp2['points']:.1f} pts for {mvp2['team_name']})." if mvp2 else ".")
                if mvp1 else ""
            )
        )

        # Playoff seedings & Projected Draft Order (Max PF for latest week)
        playoff_picture = []
        for idx, row in enumerate(standings_rows[:8], start=1):
            if idx <= 2:
                status = "First-Round Bye"
            elif idx < playoff_teams:
                status = "Playoff Field"
            elif idx == playoff_teams:
                status = "Last Team In"
            elif idx == playoff_teams + 1:
                status = "First Team Out (Bubble)"
            else:
                gb = seed6["wins"] - row["wins"]
                status = f"On the Bubble ({gb} GB)" if gb > 0 else "On the Bubble (PF Tiebreaker)"
            playoff_picture.append({
                "seed": idx,
                "roster_id": row["roster_id"],
                "team_name": row["team_name"],
                "manager": row["manager"],
                "record": row["record"],
                "streak": row["streak"],
                "pf": row["pf"],
                "status": status,
                "in_playoffs": idx <= playoff_teams,
            })

        weeks_out.append({
            "week": w,
            "dispatch_date": dispatch_date_for_week(season, w),
            "theme": {
                "id": theme["id"],
                "holiday": theme["holiday"],
                "edition": theme["edition"],
                "accent": theme["accent"],
                "accent_soft": theme["accent_soft"],
                "tagline": theme["tagline"],
            },
            "headline": f"Tier 1 Trauma: {theme['edition']}",
            "deck": deck,
            "ward_headline": ward_headline,
            "ward_paragraphs": [ward_p1, ward_p2],
            "stats": {
                "high_score": high_bar["points"],
                "high_team": high_bar["team_name"],
                "low_score": low_bar["points"],
                "low_team": low_bar["team_name"],
                "mean": mean_score,
                "median": median_score,
                "closest_margin": closest_m["margin"],
                "closest_winner": closest_m["winner"]["team_name"],
                "above_mean_delta": round2(high_bar["points"] - mean_score),
            },
            "top_players": top_starters_league[:6],
            "awards": awards_out,
            "matchups": matchups_out,
            "scoring_bars": scoring_bars,
            "standings": standings_rows,
            "playoff_picture": playoff_picture,
        })

    # Projected Rookie Draft Order (Anti-Tanking Max PF rules for current standings)
    latest_standings = weeks_out[-1]["standings"] if weeks_out else []
    non_playoff = [r for r in latest_standings if r["rank"] > playoff_teams]
    playoff_squads = [r for r in latest_standings if r["rank"] <= playoff_teams]
    non_playoff.sort(key=lambda r: teams_by_roster[r["roster_id"]]["max_pf"])
    playoff_squads.sort(key=lambda r: r["rank"], reverse=True)

    draft_order = []
    ordinal = ["Lowest", "2nd-Lowest", "3rd-Lowest", "4th-Lowest", "5th-Lowest", "Highest"]
    for i, r in enumerate(non_playoff):
        t = teams_by_roster[r["roster_id"]]
        basis = f"{ordinal[i] if i < len(ordinal) else f'#{i+1}'} Max PF (Non-Playoff)"
        draft_order.append({
            "pick": f"1.{i + 1:02d}",
            "roster_id": r["roster_id"],
            "team_name": t["team_name"],
            "manager": t["manager"],
            "record": r["record"],
            "max_pf": t["max_pf"],
            "basis": basis,
            "lottery": True,
        })
    for i, r in enumerate(playoff_squads):
        t = teams_by_roster[r["roster_id"]]
        draft_order.append({
            "pick": f"1.{len(non_playoff) + i + 1:02d}",
            "roster_id": r["roster_id"],
            "team_name": t["team_name"],
            "manager": t["manager"],
            "record": r["record"],
            "max_pf": t["max_pf"],
            "basis": f"Projected #{r['rank']} Seed",
            "lottery": False,
        })

    # Team season profiles for the interactive "Team Pulse" explorer
    team_profiles = []
    for row in latest_standings:
        rid = row["roster_id"]
        t = teams_by_roster[rid]
        scores = cum[rid]["weekly_scores"]
        pts_vals = [x["points"] for x in scores]
        team_profiles.append({
            "roster_id": rid,
            "rank": row["rank"],
            "team_name": t["team_name"],
            "manager": t["manager"],
            "avatar": t["avatar"],
            "record": row["record"],
            "streak": row["streak"],
            "pf": t["pf"],
            "max_pf": t["max_pf"],
            "pa": t["pa"],
            "efficiency": t["efficiency"],
            "all_play": row["all_play"],
            "all_play_pct": row["all_play_pct"],
            "avg_score": round2(statistics.mean(pts_vals)) if pts_vals else 0.0,
            "best_week": max(scores, key=lambda x: x["points"]) if scores else None,
            "worst_week": min(scores, key=lambda x: x["points"]) if scores else None,
            "weekly_scores": scores,
        })

    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "next_dispatch_at": next_tuesday_iso(),
        "league": {
            "id": LEAGUE_ID,
            "name": league.get("name", "Tier 1 Dynasty"),
            "brand": "Tier 1 Trauma",
            "season": season,
            "total_teams": len(teams_by_roster),
            "playoff_teams": playoff_teams,
            "playoff_week_start": playoff_week_start,
            "ffwrapped_url": f"https://ffwrapped.com/?leagueId={LEAGUE_ID}&view=weekly-report",
            "sleeper_url": f"https://sleeper.com/leagues/{LEAGUE_ID}",
        },
        "latest_week": latest_week,
        "draft_order": draft_order,
        "team_profiles": team_profiles,
        "weeks": weeks_out,
    }
    return payload


def main() -> None:
    payload = build_data()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        f"Generated {OUTPUT_FILE} — Season {payload['league']['season']}, "
        f"{len(payload['weeks'])} weeks (latest: Week {payload['latest_week']} · "
        f"{payload['weeks'][-1]['theme']['edition']})."
    )


if __name__ == "__main__":
    main()
