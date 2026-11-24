/* ==========================================================================
   TIER 1 TRAUMA — Interactive Client App
   Loads data/league-data.json, renders unbiased league-wide dispatches,
   holiday themes, sortable standings, matchup drawers, and team pulse charts.
   ========================================================================== */

(function () {
  "use strict";

  const state = {
    data: null,
    selectedWeek: null,
    sortKey: "rank",
    sortDir: "asc",
    selectedTeamId: null,
  };

  function fmt(num, digits = 2) {
    if (num === null || num === undefined || Number.isNaN(Number(num))) return "—";
    return Number(num).toLocaleString("en-US", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  }

  function escapeHtml(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function avatarHtml(teamName, avatarUrl) {
    const initials = (teamName || "T1")
      .split(/\s+/)
      .slice(0, 2)
      .map((w) => w[0] || "")
      .join("")
      .toUpperCase();
    if (avatarUrl) {
      return `<img class="team-avatar" src="${escapeHtml(avatarUrl)}" alt="" loading="lazy" onerror="this.style.display='none'" />`;
    }
    return `<span class="team-avatar-fallback" aria-hidden="true">${escapeHtml(initials)}</span>`;
  }

  function streakHtml(streak) {
    if (!streak || streak === "-") return "";
    const isWin = streak.startsWith("W");
    const cls = isWin ? "hot" : "cold";
    return `<span class="streak-badge ${cls}">${escapeHtml(streak)}</span>`;
  }

  function getWeekObj(weekNum) {
    return state.data.weeks.find((w) => w.week === weekNum) || state.data.weeks[state.data.weeks.length - 1];
  }

  function applyHolidayTheme(weekObj) {
    const root = document.documentElement;
    root.style.setProperty("--holiday-accent", weekObj.theme.accent || "#D9822B");
    root.style.setProperty("--holiday-accent-soft", weekObj.theme.accent_soft || "rgba(217, 130, 43, 0.16)");
  }

  function renderWeekSelector() {
    const sel = document.getElementById("week-select");
    const prevBtn = document.getElementById("prev-week-btn");
    const nextBtn = document.getElementById("next-week-btn");
    const weeks = state.data.weeks;

    sel.innerHTML = weeks
      .slice()
      .reverse()
      .map(
        (w) =>
          `<option value="${w.week}" ${w.week === state.selectedWeek ? "selected" : ""}>Week ${w.week} · ${escapeHtml(w.theme.holiday)}</option>`
      )
      .join("");

    const minW = weeks[0].week;
    const maxW = weeks[weeks.length - 1].week;
    prevBtn.disabled = state.selectedWeek <= minW;
    nextBtn.disabled = state.selectedWeek >= maxW;
  }

  function renderHeroAndWard(weekObj) {
    document.getElementById("hero-holiday-tag").textContent = `${weekObj.theme.holiday} Edition`;
    document.getElementById("hero-date-label").textContent = `Week ${weekObj.week} · ${weekObj.dispatch_date}`;
    document.getElementById("hero-headline").textContent = weekObj.headline;
    document.getElementById("hero-deck").textContent = weekObj.deck;

    const s = weekObj.stats;
    const vitalsEl = document.getElementById("vitals-grid");
    vitalsEl.innerHTML = `
      <div class="vital-card">
        <div class="vital-label">High Score</div>
        <div class="vital-value crimson">${fmt(s.high_score)}</div>
        <div class="vital-sub">${escapeHtml(s.high_team)}</div>
      </div>
      <div class="vital-card">
        <div class="vital-label">League Mean</div>
        <div class="vital-value">${fmt(s.mean)}</div>
        <div class="vital-sub">Median: ${fmt(s.median)} pts</div>
      </div>
      <div class="vital-card">
        <div class="vital-label">Closest Escape</div>
        <div class="vital-value holiday">+${fmt(s.closest_margin)}</div>
        <div class="vital-sub">${escapeHtml(s.closest_winner)}</div>
      </div>
      <div class="vital-card">
        <div class="vital-label">Week Floor</div>
        <div class="vital-value">${fmt(s.low_score)}</div>
        <div class="vital-sub">${escapeHtml(s.low_team)}</div>
      </div>
    `;

    document.getElementById("ward-high-num").textContent = fmt(s.high_score);
    document.getElementById("ward-high-caption").textContent =
      `Highest score of Week ${weekObj.week} by ${s.high_team}, ${fmt(s.above_mean_delta)} points above the ${fmt(s.mean)} league average.`;
    document.getElementById("ward-headline").textContent = weekObj.ward_headline;
    document.getElementById("ward-paragraphs").innerHTML = weekObj.ward_paragraphs
      .map((p) => `<p>${escapeHtml(p)}</p>`)
      .join("");
    document.getElementById("ward-tagline").textContent = `// ${weekObj.theme.tagline}`;
  }

  function renderAwards(weekObj) {
    document.getElementById("awards-heading").textContent = `Week ${weekObj.week} · ${weekObj.theme.holiday} Awards`;
    const grid = document.getElementById("awards-grid");
    grid.innerHTML = weekObj.awards
      .map(
        (a) => `
        <article class="award-card" data-key="${escapeHtml(a.key)}">
          <div class="award-kicker">${escapeHtml(a.title)}</div>
          <div class="award-team">${escapeHtml(a.team)}</div>
          <div class="award-stat">${escapeHtml(a.stat)}</div>
          <div class="award-detail">${escapeHtml(a.detail)}</div>
        </article>
      `
      )
      .join("");
  }

  function renderPlayerList(starters, bench) {
    const sHtml = (starters || [])
      .map(
        (p) => `
        <div class="player-line">
          <span>${escapeHtml(p.name)} <small style="color:var(--text-muted)">${escapeHtml(p.pos)}</small></span>
          <span class="p-pts">${fmt(p.points, 1)}</span>
        </div>
      `
      )
      .join("");
    const bHtml =
      bench && bench.length && bench[0].points > 0
        ? `<div class="player-line bench-line">
            <span>Bench: ${escapeHtml(bench[0].name)} (${escapeHtml(bench[0].pos)})</span>
            <span class="p-pts">${fmt(bench[0].points, 1)}</span>
          </div>`
        : "";
    return sHtml + bHtml;
  }

  function renderMatchups(weekObj) {
    document.getElementById("scoreboard-heading").textContent = `Week ${weekObj.week} Scoreboard & Triage`;
    const grid = document.getElementById("matchups-grid");
    grid.innerHTML = weekObj.matchups
      .map(
        (m, idx) => `
        <article class="matchup-card" data-matchup-idx="${idx}" tabindex="0" role="button" aria-expanded="false">
          <div class="matchup-row winner">
            <div class="matchup-team-info">
              ${avatarHtml(m.winner.team_name, m.winner.avatar)}
              <span class="matchup-name">${escapeHtml(m.winner.team_name)}<span class="matchup-rec">(${escapeHtml(m.winner.record)})</span></span>
            </div>
            <span class="matchup-score">${fmt(m.winner.points)}</span>
          </div>
          <div class="matchup-row loser">
            <div class="matchup-team-info">
              ${avatarHtml(m.loser.team_name, m.loser.avatar)}
              <span class="matchup-name">${escapeHtml(m.loser.team_name)}<span class="matchup-rec">(${escapeHtml(m.loser.record)})</span></span>
            </div>
            <span class="matchup-score">${fmt(m.loser.points)}</span>
          </div>
          <p class="matchup-note">${escapeHtml(m.triage_note)}</p>
          <div class="matchup-expand-hint">
            <span>Margin: +${fmt(m.margin)} · Combined: ${fmt(m.combined)}</span>
            <span class="expand-label">Inspect Box Score +</span>
          </div>
          <div class="matchup-drawer">
            <div class="drawer-col">
              <h4>${escapeHtml(m.winner.team_name)} Top Starters</h4>
              ${renderPlayerList(m.winner.top_starters, m.winner.top_bench)}
            </div>
            <div class="drawer-col">
              <h4>${escapeHtml(m.loser.team_name)} Top Starters</h4>
              ${renderPlayerList(m.loser.top_starters, m.loser.top_bench)}
            </div>
          </div>
        </article>
      `
      )
      .join("");

    grid.querySelectorAll(".matchup-card").forEach((card) => {
      const toggle = () => {
        const expanded = card.classList.toggle("expanded");
        card.setAttribute("aria-expanded", String(expanded));
        const lbl = card.querySelector(".expand-label");
        if (lbl) lbl.textContent = expanded ? "Hide Box Score −" : "Inspect Box Score +";
      };
      card.addEventListener("click", toggle);
      card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          toggle();
        }
      });
    });
  }

  function renderScoringBars(weekObj) {
    const bars = weekObj.scoring_bars;
    const maxVal = Math.max(...bars.map((b) => b.points), weekObj.stats.mean, 100) * 1.06;
    const meanPct = (weekObj.stats.mean / maxVal) * 100;

    document.getElementById("dist-heading").textContent = `Week ${weekObj.week} Scoring Distribution`;
    document.getElementById("dist-sub").textContent =
      `Mean ${fmt(weekObj.stats.mean)} · Median ${fmt(weekObj.stats.median)} — all 12 teams on equal footing (crimson = win, slate = loss).`;
    document.getElementById("legend-mean-text").textContent = `Mean (${fmt(weekObj.stats.mean)})`;

    const wrap = document.getElementById("scoring-bars");
    wrap.innerHTML = bars
      .map((b, i) => {
        const widthPct = Math.max(2, (b.points / maxVal) * 100);
        const marker =
          i === 0
            ? `<div class="mean-marker" style="left:${meanPct.toFixed(2)}%"><span class="mean-marker-tag">Mean ${fmt(weekObj.stats.mean)}</span></div>`
            : `<div class="mean-marker" style="left:${meanPct.toFixed(2)}%"></div>`;
        const title = `${b.team_name}: ${fmt(b.points)} pts (${b.won ? "W" : "L"} vs ${b.opponent}, ${b.margin >= 0 ? "+" : ""}${fmt(b.margin)})`;
        return `
          <div class="bar-row ${b.won ? "won" : "lost"}" title="${escapeHtml(title)}">
            <div class="bar-label">${escapeHtml(b.team_name)}</div>
            <div class="bar-track">
              <div class="bar-fill" style="width:${widthPct.toFixed(2)}%"></div>
              ${marker}
            </div>
            <div class="bar-val">${fmt(b.points)}</div>
          </div>
        `;
      })
      .join("");
  }

  function renderStandings(weekObj) {
    document.getElementById("standings-heading").textContent = `Standings Through Week ${weekObj.week}`;
    const rows = weekObj.standings.slice();
    const key = state.sortKey;
    const dir = state.sortDir === "asc" ? 1 : -1;

    rows.sort((a, b) => {
      if (key === "team_name") return a.team_name.localeCompare(b.team_name) * dir;
      if (key === "wins") {
        const diff = (a.wins - b.wins) * dir;
        return diff !== 0 ? diff : (a.pf - b.pf) * dir;
      }
      const va = a[key] ?? -1;
      const vb = b[key] ?? -1;
      return (va - vb) * dir;
    });

    const playoffCut = state.data.league.playoff_teams || 6;
    const tbody = document.getElementById("standings-body");
    tbody.innerHTML = rows
      .map((r, idx) => {
        const isCutline = state.sortKey === "rank" && state.sortDir === "asc" && idx + 1 === playoffCut;
        return `
          <tr class="${isCutline ? "cutline-row" : ""}">
            <td class="rank-num">${r.rank}</td>
            <td>
              <div class="team-cell">
                ${avatarHtml(r.team_name, r.avatar)}
                <span>${escapeHtml(r.team_name)}</span>
              </div>
            </td>
            <td>${escapeHtml(r.manager)}</td>
            <td class="num">${escapeHtml(r.record)}${streakHtml(r.streak)}</td>
            <td class="num">${fmt(r.pf)}</td>
            <td class="num">${r.max_pf !== null ? fmt(r.max_pf) : "—"}</td>
            <td class="num">${fmt(r.pa)}</td>
            <td class="num">${escapeHtml(r.all_play)} <small style="color:var(--text-muted)">(${fmt(r.all_play_pct, 0)}%)</small></td>
          </tr>
        `;
      })
      .join("");

    document.querySelectorAll("#standings-table th.sortable").forEach((th) => {
      th.classList.toggle("sorted", th.dataset.sort === state.sortKey);
    });
  }

  function renderPlayoffsAndDraft(weekObj) {
    const playoffCut = state.data.league.playoff_teams || 6;
    const pBody = document.getElementById("playoff-body");
    pBody.innerHTML = weekObj.playoff_picture
      .map((p) => {
        let cls = "";
        if (p.seed <= 2) cls = "bye";
        else if (p.seed === playoffCut) cls = "last-in";
        else if (p.seed > playoffCut) cls = "bubble";

        return `
          <tr class="${p.seed === playoffCut ? "cutline-row" : ""}">
            <td class="rank-num">${p.seed}</td>
            <td style="color:var(--text-primary);font-weight:600">${escapeHtml(p.team_name)}</td>
            <td><span class="status-tag ${cls}">${escapeHtml(p.status)}</span></td>
            <td class="num">${escapeHtml(p.record)}</td>
            <td class="num">${fmt(p.pf)}</td>
          </tr>
        `;
      })
      .join("");

    const dBody = document.getElementById("draft-body");
    dBody.innerHTML = state.data.draft_order
      .map((d, idx) => {
        const isLotteryCut = idx === 5;
        return `
          <tr class="${isLotteryCut ? "cutline-row" : ""}">
            <td class="rank-num">${escapeHtml(d.pick)}</td>
            <td style="color:var(--text-primary);font-weight:600">${escapeHtml(d.team_name)}</td>
            <td><span class="status-tag">${escapeHtml(d.basis)}</span></td>
            <td class="num">${fmt(d.max_pf)}</td>
          </tr>
        `;
      })
      .join("");
  }

  function renderTeamPulse() {
    const profiles = state.data.team_profiles;
    if (!profiles || !profiles.length) return;
    if (!state.selectedTeamId) state.selectedTeamId = profiles[0].roster_id;

    const pills = document.getElementById("team-pills");
    pills.innerHTML = profiles
      .map(
        (t) => `
        <button
          type="button"
          class="team-pill ${t.roster_id === state.selectedTeamId ? "active" : ""}"
          data-roster-id="${t.roster_id}"
          role="tab"
          aria-selected="${t.roster_id === state.selectedTeamId}"
        >
          #${t.rank} ${escapeHtml(t.team_name)}
        </button>
      `
      )
      .join("");

    pills.querySelectorAll(".team-pill").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.selectedTeamId = Number(btn.dataset.rosterId);
        renderTeamPulse();
      });
    });

    const team = profiles.find((t) => t.roster_id === state.selectedTeamId) || profiles[0];
    const scores = team.weekly_scores || [];
    const vals = scores.map((s) => s.points);
    const minY = Math.max(0, Math.min(...vals, 60) - 15);
    const maxY = Math.max(...vals, 160) + 15;
    const W = 560;
    const H = 150;
    const padX = 28;
    const padY = 20;

    const pts = scores.map((s, i) => {
      const x = scores.length === 1 ? W / 2 : padX + (i / (scores.length - 1)) * (W - padX * 2);
      const y = H - padY - ((s.points - minY) / Math.max(1, maxY - minY)) * (H - padY * 2);
      return { x, y, week: s.week, points: s.points };
    });

    const polyline = pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
    const areaPath =
      pts.length > 1
        ? `M ${pts[0].x.toFixed(1)},${H - padY} L ${pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" L ")} L ${pts[pts.length - 1].x.toFixed(1)},${H - padY} Z`
        : "";

    const avgY = H - padY - ((team.avg_score - minY) / Math.max(1, maxY - minY)) * (H - padY * 2);

    const dots = pts
      .map(
        (p) => `
        <g>
          <circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4" fill="#E53935" stroke="#0B0D11" stroke-width="1.5">
            <title>Week ${p.week}: ${fmt(p.points)} pts</title>
          </circle>
          <text x="${p.x.toFixed(1)}" y="${H - 4}" text-anchor="middle" fill="#6E7A8A" font-size="9" font-family="JetBrains Mono, monospace">W${p.week}</text>
        </g>
      `
      )
      .join("");

    document.getElementById("pulse-detail").innerHTML = `
      <div class="pulse-meta">
        <h3>${escapeHtml(team.team_name)}</h3>
        <div class="pulse-mgr">@${escapeHtml(team.manager)} · Seed #${team.rank} (${escapeHtml(team.record)}, ${escapeHtml(team.streak)})</div>
        <div class="pulse-stats">
          <div class="pulse-stat"><span>Season Avg</span><strong>${fmt(team.avg_score)}</strong></div>
          <div class="pulse-stat"><span>Lineup Eff.</span><strong>${fmt(team.efficiency, 1)}%</strong></div>
          <div class="pulse-stat"><span>Best Week</span><strong>${team.best_week ? `${fmt(team.best_week.points)} (W${team.best_week.week})` : "—"}</strong></div>
          <div class="pulse-stat"><span>All-Play</span><strong>${escapeHtml(team.all_play)}</strong></div>
        </div>
      </div>
      <div class="sparkline-box">
        <div class="sparkline-header">
          <span>Weekly Scoring Trajectory (Weeks 1–${state.data.latest_week})</span>
          <span>Avg: ${fmt(team.avg_score)} pts</span>
        </div>
        <svg class="sparkline-svg" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-label="Weekly scoring chart for ${escapeHtml(team.team_name)}">
          <defs>
            <linearGradient id="pulseFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#E53935" stop-opacity="0.28" />
              <stop offset="100%" stop-color="#E53935" stop-opacity="0.0" />
            </linearGradient>
          </defs>
          <line x1="${padX}" y1="${avgY.toFixed(1)}" x2="${W - padX}" y2="${avgY.toFixed(1)}" stroke="rgba(255,255,255,0.18)" stroke-dasharray="4 4" />
          ${areaPath ? `<path d="${areaPath}" fill="url(#pulseFill)" />` : ""}
          <polyline fill="none" stroke="#E53935" stroke-width="2.2" points="${polyline}" />
          ${dots}
        </svg>
      </div>
    `;
  }

  function renderCurrentWeek() {
    const weekObj = getWeekObj(state.selectedWeek);
    applyHolidayTheme(weekObj);
    renderWeekSelector();
    renderHeroAndWard(weekObj);
    renderAwards(weekObj);
    renderMatchups(weekObj);
    renderScoringBars(weekObj);
    renderStandings(weekObj);
    renderPlayoffsAndDraft(weekObj);

    const url = new URL(window.location.href);
    url.searchParams.set("week", String(weekObj.week));
    window.history.replaceState({}, "", url.toString());
  }

  function startCountdown(targetIso) {
    const el = document.getElementById("next-dispatch-clock");
    if (!el || !targetIso) return;
    const target = new Date(targetIso).getTime();

    function tick() {
      const diff = target - Date.now();
      if (diff <= 0) {
        el.textContent = "LIVE SOON";
        return;
      }
      const d = Math.floor(diff / 86400000);
      const h = Math.floor((diff % 86400000) / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      el.textContent = d > 0 ? `${d}d ${h}h` : `${h}h ${m}m`;
    }

    tick();
    setInterval(tick, 60000);
  }

  function bindEvents() {
    document.getElementById("week-select").addEventListener("change", (e) => {
      state.selectedWeek = Number(e.target.value);
      renderCurrentWeek();
    });

    document.getElementById("prev-week-btn").addEventListener("click", () => {
      const minW = state.data.weeks[0].week;
      if (state.selectedWeek > minW) {
        state.selectedWeek -= 1;
        renderCurrentWeek();
      }
    });

    document.getElementById("next-week-btn").addEventListener("click", () => {
      const maxW = state.data.weeks[state.data.weeks.length - 1].week;
      if (state.selectedWeek < maxW) {
        state.selectedWeek += 1;
        renderCurrentWeek();
      }
    });

    document.querySelectorAll("#standings-table th.sortable").forEach((th) => {
      th.addEventListener("click", () => {
        const key = th.dataset.sort;
        if (state.sortKey === key) {
          state.sortDir = state.sortDir === "asc" ? "desc" : "asc";
        } else {
          state.sortKey = key;
          state.sortDir = key === "rank" || key === "team_name" ? "asc" : "desc";
        }
        renderStandings(getWeekObj(state.selectedWeek));
      });
    });
  }

  async function init() {
    try {
      const resp = await fetch("data/league-data.json", { cache: "no-store" });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      state.data = await resp.json();

      document.getElementById("league-subtitle").textContent =
        `${state.data.league.name} · ${state.data.league.season}`;
      document.getElementById("footer-league-name").textContent = state.data.league.name;
      document.getElementById("sleeper-link").href = state.data.league.sleeper_url;
      document.getElementById("ffwrapped-link").href = state.data.league.ffwrapped_url;

      const updatedDate = new Date(state.data.generated_at);
      document.getElementById("last-updated-label").textContent =
        `Updated ${updatedDate.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}`;

      const params = new URLSearchParams(window.location.search);
      const reqWeek = Number(params.get("week"));
      const validWeeks = new Set(state.data.weeks.map((w) => w.week));
      state.selectedWeek = validWeeks.has(reqWeek) ? reqWeek : state.data.latest_week;

      bindEvents();
      renderCurrentWeek();
      renderTeamPulse();
      startCountdown(state.data.next_dispatch_at);
    } catch (err) {
      console.error("Failed to load Tier 1 Trauma data:", err);
      document.getElementById("hero-deck").textContent =
        "Unable to load league dispatch data. Please refresh in a moment.";
    }
  }

  init();
})();
