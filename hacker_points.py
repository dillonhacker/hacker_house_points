#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import mimetypes
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
import sys


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Hacker House Points</title>
  <style>
    :root{
      --gold:#d6a54d;
      --gold-soft:#f2d18a;
      --text:#f4e7c7;

      --page-max:1700px;
      --tube-width:400px;

      /* these are tied to the intact base tube asset geometry */
      --liquid-left:14.8%;
      --liquid-right:14.8%;
      --liquid-top:2.8%;
      --liquid-bottom:13.2%;
      --tube-seat:-20px;

      --crest-size:92px;
      --crest-top:116px;

      --name-width:182px;
      --score-width:208px;
    }

    * { box-sizing:border-box; }

    html, body {
      margin:0;
      min-height:100%;
      background:#000;
      color:var(--text);
      font-family:Georgia, "Times New Roman", serif;
      overflow-x:hidden;
    }

    .scene {
      position:relative;
      min-height:100vh;
      overflow:hidden;
      background:#000;
    }

    .bg {
      position:fixed;
      inset:0;
      background:
        linear-gradient(180deg, rgba(0,0,0,0.06), rgba(0,0,0,0.18)),
        url("/static/background.png") center center / cover no-repeat;
      z-index:0;
      transform:scale(1.01);
    }

    .scene::before {
      content:"";
      position:fixed;
      inset:0;
      background:
        radial-gradient(circle at center, transparent 0 40%, rgba(0,0,0,0.10) 68%, rgba(0,0,0,0.32) 100%);
      z-index:0;
      pointer-events:none;
    }

    .wrap {
      position:relative;
      z-index:2;
      max-width:var(--page-max);
      min-height:100vh;
      margin:0 auto;
      padding:8px 20px 8px;
      display:flex;
      flex-direction:column;
    }

    .title-wrap {
      text-align:center;
      margin-top:2px;
      margin-bottom:8px;
    }

    .ornament {
      color:var(--gold);
      letter-spacing:.22em;
      font-size:clamp(1rem,1.4vw,1.2rem);
      margin-bottom:2px;
      text-shadow:0 0 10px rgba(214,165,77,.16);
    }

    .title {
      margin:0;
      color:var(--gold-soft);
      text-transform:uppercase;
      letter-spacing:.05em;
      font-size:clamp(2.3rem,4.5vw,5.1rem);
      line-height:.98;
      text-shadow:
        0 0 8px rgba(214,165,77,.16),
        0 0 24px rgba(214,165,77,.12);
    }

    .subtitle {
      margin-top:8px;
      color:var(--gold);
      text-transform:uppercase;
      letter-spacing:.10em;
      font-size:clamp(.9rem,1.1vw,1.08rem);
      text-shadow:0 0 10px rgba(214,165,77,.10);
    }

    .status {
      text-align:center;
      color:#d2b06e;
      min-height:1.35em;
      font-size:.92rem;
      margin-top:6px;
      text-shadow:0 0 6px rgba(0,0,0,.4);
    }

    .board {
      position:relative;
      flex:1;
      min-height:0;
      padding-top:0;
      display:flex;
      align-items:flex-end;
    }

    .tubes {
      width:100%;
      display:grid;
      grid-template-columns:repeat(4, minmax(220px, 1fr));
      gap:24px;
      align-items:end;
      justify-items:center;
      padding-bottom:0;
    }

    .tube-card {
      width:100%;
      max-width:230px;
      display:flex;
      flex-direction:column;
      align-items:center;
      padding-bottom:0;
    }

    .tube-visual {
      position:relative;
      width:var(--tube-width);
      aspect-ratio:959 / 2048;
      height:auto;
      margin-bottom:26px;
      transform:translateY(var(--tube-seat));
      filter:drop-shadow(0 16px 30px rgba(0,0,0,.32));
    }

    /* use real transparent PNGs; do not rely on blend tricks */
    img.clean-alpha {
      mix-blend-mode:normal;
      background:transparent;
    }

    .tube-base {
      position:absolute;
      inset:0;
      width:100%;
      height:100%;
      object-fit:fill;
      display:block;
      pointer-events:none;
      user-select:none;
      z-index:6;
      opacity:.98;
    }


    .tube-glow {
      position:absolute;
      left:28px;
      right:28px;
      top:50px;
      bottom:74px;
      border-radius:40px;
      filter:blur(28px);
      opacity:.22;
      z-index:1;
      pointer-events:none;
    }

    .liquid-cavity {
      position:absolute;
      left:var(--liquid-left);
      right:var(--liquid-right);
      top:var(--liquid-top);
      bottom:var(--liquid-bottom);
      overflow:hidden;
      z-index:3;
      border-radius:0 0 30px 30px;
      pointer-events:none;
    }

    .liquid-fill {
      position:absolute;
      inset:0;
      overflow:hidden;
      border-radius:0 0 30px 30px;
      transform:translateY(100%);
      transition:transform 2s cubic-bezier(.22,.8,.2,1);
      will-change:transform;
    }

    .liquid-inner {
      position:absolute;
      inset:0;
      overflow:hidden;
      border-radius:0 0 30px 30px;
      background:transparent;
    }

    .liquid-img {
      position:absolute;
      inset:0;
      width:100%;
      height:100%;
      object-fit:fill;
      display:block;
      pointer-events:none;
      user-select:none;
      opacity:.93;
      transform-origin:center bottom;
      animation:liquidBreath 7s ease-in-out infinite;
      filter:brightness(1.08) saturate(1.14);
    }

    .liquid-depth {
      position:absolute;
      inset:0;
      background:
        linear-gradient(90deg, rgba(255,255,255,.08), transparent 12%, transparent 84%, rgba(255,255,255,.06)),
        linear-gradient(180deg, rgba(255,255,255,.10), transparent 18%, transparent 80%, rgba(0,0,0,.08));
      mix-blend-mode:screen;
      opacity:.18;
      pointer-events:none;
    }

    .liquid-caustics {
      position:absolute;
      inset:-8% -10%;
      background:
        radial-gradient(circle at 18% 32%, rgba(255,255,255,.10), transparent 14%),
        radial-gradient(circle at 70% 20%, rgba(255,255,255,.07), transparent 18%),
        radial-gradient(circle at 40% 60%, rgba(255,255,255,.05), transparent 20%),
        radial-gradient(circle at 82% 72%, rgba(255,255,255,.07), transparent 16%);
      mix-blend-mode:screen;
      opacity:.24;
      filter:blur(8px);
      animation:causticsMove 12s linear infinite;
      pointer-events:none;
    }

    .liquid-top-shine {
      position:absolute;
      left:0;
      right:0;
      top:0;
      height:10px;
      background:linear-gradient(180deg, rgba(255,255,255,.16), rgba(255,255,255,.02));
      mix-blend-mode:screen;
      opacity:.18;
      filter:blur(1px);
      pointer-events:none;
    }

    .particle-layer {
      position:absolute;
      inset:0;
      overflow:hidden;
      pointer-events:none;
    }

    .particle-img {
      position:absolute;
      left:-10%;
      width:120%;
      height:132%;
      bottom:-28%;
      object-fit:cover;
      opacity:.42;
      animation:particlesRise 14s linear infinite;
      pointer-events:none;
      user-select:none;
      filter:brightness(1.05) saturate(1.15);
    }

    .particle-img.secondary {
      left:-12%;
      width:126%;
      height:144%;
      bottom:-42%;
      opacity:.13;
      animation-duration:20s;
      animation-delay:-6s;
      transform:scale(1.08);
    }

    .crest {
      position:absolute;
      top:var(--crest-top);
      left:50%;
      transform:translateX(-50%);
      width:var(--crest-size);
      height:var(--crest-size);
      object-fit:contain;
      z-index:7;
      pointer-events:none;
      user-select:none;
      filter:
        drop-shadow(0 6px 8px rgba(0,0,0,.45))
        drop-shadow(0 0 6px rgba(255,220,120,.08));
    }

    .name-plaque {
      margin-top:18px;
      width:var(--name-width);
      text-align:center;
      padding:11px 14px 9px;
      border-radius:18px;
      background:linear-gradient(180deg, rgba(98,61,19,.96), rgba(36,22,7,.99));
      border:1px solid rgba(222,180,84,.22);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,.07),
        0 10px 22px rgba(0,0,0,.28);
      font-size:1.3rem;
      letter-spacing:.04em;
      text-transform:uppercase;
      z-index:5;
    }

    .score-plaque {
      margin-top:12px;
      width:var(--score-width);
      text-align:center;
      padding:14px 16px 10px;
      border-radius:20px;
      background:linear-gradient(180deg, rgba(98,61,19,.97), rgba(31,18,6,1));
      border:1px solid rgba(222,180,84,.20);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,.06),
        0 12px 26px rgba(0,0,0,.28);
      color:#f3e3bd;
      font-size:2.75rem;
      line-height:1;
      font-variant-numeric:tabular-nums;
      z-index:5;
    }

    .footer {
      text-align:center;
      margin-top:18px;
      color:var(--gold);
      font-size:.98rem;
      letter-spacing:.03em;
      text-shadow:0 0 8px rgba(214,165,77,.14);
    }

    .error {
      display:none;
      max-width:900px;
      margin:20px auto 0;
      padding:12px 16px;
      border-radius:12px;
      text-align:center;
      background:rgba(125,24,24,.28);
      border:1px solid rgba(255,120,120,.30);
      color:#ffd7d7;
    }

    .air {
      position:fixed;
      inset:0;
      z-index:1;
      pointer-events:none;
      overflow:hidden;
    }

    .dust {
      position:absolute;
      width:3px;
      height:3px;
      border-radius:50%;
      background:rgba(255,220,160,.20);
      filter:blur(.4px);
      animation:dustFloat linear infinite;
    }

    @keyframes liquidBreath {
      0%,100% { transform:scaleY(1) translateX(0); }
      50% { transform:scaleY(1.012) translateX(1px); }
    }

    @keyframes causticsMove {
      0% { transform:translateX(0) translateY(0); }
      50% { transform:translateX(-4%) translateY(2%); }
      100% { transform:translateX(-8%) translateY(0); }
    }

    @keyframes particlesRise {
      0% { transform:translateY(0) scale(1); opacity:0; }
      10% { opacity:.28; }
      100% { transform:translateY(-42%) scale(1.05); opacity:0; }
    }

    @keyframes dustFloat {
      0% { transform:translateY(0) translateX(0); opacity:0; }
      10% { opacity:.28; }
      100% { transform:translateY(-140px) translateX(26px); opacity:0; }
    }

    @media (max-width: 1400px) {
      :root {
        --tube-width:230px;
        --tube-drop:0px;
      }
    }

    @media (max-width: 1100px) {
      :root {
        --tube-width:205px;
        --tube-drop:0px;
        --name-width:160px;
        --score-width:188px;
        --crest-size:80px;
        --crest-top:104px;
      }

      .tubes {
        grid-template-columns:repeat(2, minmax(220px, 1fr));
        row-gap:30px;
      }
    }

    @media (max-width: 700px) {
      :root {
        --tube-width:180px;
        --tube-drop:0px;
        --name-width:150px;
        --score-width:172px;
        --crest-size:74px;
        --crest-top:92px;
      }

      .tubes {
        grid-template-columns:1fr;
      }
    }
  </style>
</head>
<body>
  <div class="scene">
    <div class="bg"></div>
    <div class="air" id="air"></div>

    <div class="wrap">
      <div class="title-wrap">
        <div class="ornament">✦ James Hubert Blake High School ✦</div>
        <h1 class="title">HACKER House Points</h1>
        <div class="subtitle">Together we make Blake proud</div>
        <div class="status" id="status-text">Waiting for the first live update…</div>
      </div>

      <div class="board">
        <div class="tubes" id="tubes"></div>
        <div class="error" id="error-box"></div>
      </div>

      <div class="footer" id="footer-text">⚡ Last updated: — &nbsp; | &nbsp; Updates every 5 seconds</div>
    </div>
  </div>

  <template id="tube-template">
    <div class="tube-card">
      <div class="tube-visual">
        <div class="tube-glow"></div>


        <div class="liquid-cavity">
          <div class="liquid-fill">
            <div class="liquid-inner">
              <img class="liquid-img clean-alpha" alt="">
              <div class="liquid-depth"></div>
              <div class="liquid-caustics"></div>
              <div class="liquid-top-shine"></div>
              <div class="particle-layer">
                <img class="particle-img clean-alpha primary" src="/static/particles.png" alt="">
                <img class="particle-img clean-alpha secondary" src="/static/particles.png" alt="">
              </div>
            </div>
          </div>
        </div>

        <img class="tube-base clean-alpha" src="/static/tube_base.png" alt="">
        <img class="crest clean-alpha" alt="">
      </div>

      <div class="name-plaque"></div>
      <div class="score-plaque"></div>
    </div>
  </template>

  <script>
    const tubesEl = document.getElementById("tubes");
    const template = document.getElementById("tube-template");
    const statusText = document.getElementById("status-text");
    const footerText = document.getElementById("footer-text");
    const errorBox = document.getElementById("error-box");
    const air = document.getElementById("air");
    const POLL_MS = 5000;

    const DISPLAY_PLAQUE_COLORS = {
      red: "#d94b4b",
      blue: "#5ea1ff",
      green: "#4fd16d",
      yellow: "#f2cf3b",

      gryffindor: "#d94b4b",
      ravenclaw: "#5ea1ff",
      slytherin: "#4fd16d",
      hufflepuff: "#f2cf3b",
    };

    function plaqueColorFor(rawHouse, canonicalHouse) {
      const raw = String(rawHouse || "").trim().toLowerCase();
      return DISPLAY_PLAQUE_COLORS[raw] || DISPLAY_PLAQUE_COLORS[canonicalHouse] || "#f4e7c7";
    }    

    const HOUSE_ALIASES = {
      gryffindor: "gryffindor",
      red: "gryffindor",

      ravenclaw: "ravenclaw",
      blue: "ravenclaw",

      slytherin: "slytherin",
      green: "slytherin",

      hufflepuff: "hufflepuff",
      yellow: "hufflepuff"
    
    };

    function canonicalHouseKey(raw) {
      const key = String(raw || "").trim().toLowerCase();
      return HOUSE_ALIASES[key] || key;
    }

    const HOUSE_ASSETS = {
      gryffindor: {
        crest: "/static/crest_gryffindor.png",
        liquid: "/static/liquid_gryffindor.png",
        plaqueColor: "#f0b640",
        glow: "rgba(255, 90, 20, 0.34)"
      },
      slytherin: {
        crest: "/static/crest_slytherin.png",
        liquid: "/static/liquid_slytherin.png",
        plaqueColor: "#d7d7d7",
        glow: "rgba(30, 220, 90, 0.26)"
      },
      ravenclaw: {
        crest: "/static/crest_ravenclaw.png",
        liquid: "/static/liquid_ravenclaw.png",
        plaqueColor: "#5ea1ff",
        glow: "rgba(45, 110, 255, 0.26)"
      },
      hufflepuff: {
        crest: "/static/crest_hufflepuff.png",
        liquid: "/static/liquid_hufflepuff.png",
        plaqueColor: "#f2cf3b",
        glow: "rgba(255, 220, 40, 0.26)"
      }
    };

    let lastHeights = {};

    function fmtDate(ts) {
      const d = new Date(ts * 1000);
      return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit", second: "2-digit" });
    }

    function showError(msg) {
      errorBox.style.display = "block";
      errorBox.textContent = msg;
    }

    function hideError() {
      errorBox.style.display = "none";
      errorBox.textContent = "";
    }

    function spawnDust() {
      const d = document.createElement("span");
      d.className = "dust";
      d.style.left = `${Math.random() * 100}%`;
      d.style.top = `${60 + Math.random() * 35}%`;

      const size = 1.5 + Math.random() * 3;
      d.style.width = `${size}px`;
      d.style.height = `${size}px`;
      d.style.animationDuration = `${7 + Math.random() * 12}s`;
      d.style.animationDelay = `${Math.random() * 2}s`;

      air.appendChild(d);
      setTimeout(() => d.remove(), 22000);
    }

    function startDustField() {
      for (let i = 0; i < 24; i++) setTimeout(spawnDust, i * 350);
      setInterval(() => {
        const burst = 2 + Math.floor(Math.random() * 3);
        for (let i = 0; i < burst; i++) setTimeout(spawnDust, i * 220);
      }, 1800);
    }

    function renderRows(rows, updatedAt, csvPath) {
      hideError();

      const fallbackMaxPoints = Math.max(1, ...rows.map(r => Number(r.points) || 0));
      const sorted = [...rows].sort((a, b) => (Number(b.points) || 0) - (Number(a.points) || 0));

      const existing = new Map();
      [...tubesEl.children].forEach(card => existing.set(card.dataset.house, card));

      const nextCards = [];

      sorted.forEach((row) => {
        const houseKey = canonicalHouseKey(row.house);
        const asset = HOUSE_ASSETS[houseKey] || HOUSE_ASSETS.gryffindor;
        const plaqueColor = plaqueColorFor(row.house, houseKey);
        let node = existing.get(houseKey);
        const isNew = !node;

        if (!node) {
          node = template.content.firstElementChild.cloneNode(true);
          node.dataset.house = houseKey;

          node.querySelector(".crest").src = asset.crest;
          node.querySelector(".liquid-img").src = asset.liquid;
          node.querySelector(".name-plaque").style.color = asset.plaqueColor;
          node.querySelector(".tube-glow").style.background =
            `radial-gradient(circle, ${asset.glow}, transparent 72%)`;
        }

        node.querySelector(".name-plaque").style.color = plaqueColor;
        node.querySelector(".name-plaque").textContent = row.house;
        
        const rowMax = Number(row.max);
        const effectiveMax = Number.isFinite(rowMax) && rowMax > 0 ? rowMax : fallbackMaxPoints;
        const pct = Math.min(100, Math.max(0, ((Number(row.points) || 0) / effectiveMax) * 100));

        node.querySelector(".name-plaque").textContent = row.house;
        node.querySelector(".score-plaque").textContent = Number(row.points).toLocaleString();
        node.querySelector(".score-plaque").title = `${Number(row.points).toLocaleString()} / ${Number(effectiveMax).toLocaleString()}`;

        const liquidFill = node.querySelector(".liquid-fill");
        const prev = lastHeights[houseKey] ?? 0;
        lastHeights[houseKey] = pct;
        const offset = 100 - pct;

        if (isNew) {
          liquidFill.style.transform = "translateY(100%)";
          requestAnimationFrame(() => {
            requestAnimationFrame(() => {
              liquidFill.style.transform = `translateY(${offset}%)`;
            });
          });
        } else if (Math.abs(prev - pct) > 0.1) {
          liquidFill.style.transform = `translateY(${offset}%)`;
        }

        nextCards.push(node);
      });

      tubesEl.replaceChildren(...nextCards);
      statusText.textContent = ``;
      footerText.innerHTML = `⚡ Last updated: ${fmtDate(updatedAt)} &nbsp; | &nbsp; Updates every ${POLL_MS / 1000} seconds`;
    }

    async function refresh() {
      try {
        const res = await fetch(`/api/points?ts=${Date.now()}`, { cache: "no-store" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const payload = await res.json();

        if (payload.error) {
          statusText.textContent = "The server is running, but the CSV needs attention.";
          showError(payload.error);
          return;
        }

        renderRows(payload.rows, payload.updated_at, payload.csv_path);
      } catch (err) {
        statusText.textContent = "The page could not refresh live data.";
        showError(`Refresh failed: ${err.message}`);
      }
    }

    startDustField();
    refresh();
    setInterval(refresh, POLL_MS);
  </script>
</body>
</html>
"""


@dataclass
class AppConfig:
    csv_path: Path
    static_dir: Path
    poll_seconds: int = 5


def normalize_house_name(raw: str) -> str:
    return " ".join(str(raw).strip().split())


def infer_field(row: dict[str, Any], candidates: list[str]) -> Any | None:
    lowered_map = {str(k).strip().lower(): v for k, v in row.items()}
    for key in candidates:
        if key in lowered_map and str(lowered_map[key]).strip() != "":
            return lowered_map[key]
    return None


def has_any_header(fieldnames: list[str], candidates: list[str]) -> bool:
    lowered = {str(name).strip().lower() for name in fieldnames}
    return any(candidate in lowered for candidate in candidates)


def parse_int_field(raw: Any, *, line_no: int, field_name: str) -> int:
    try:
        return int(float(str(raw).strip()))
    except ValueError as exc:
        raise ValueError(f"Invalid numeric {field_name} value on CSV line {line_no}: {raw!r}") from exc


def parse_points_csv(csv_path: Path) -> list[dict[str, Any]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV has no header row.")

        fieldnames = [name for name in reader.fieldnames if name is not None]
        goal_candidates = ["max"]
        csv_has_goal_column = has_any_header(fieldnames, goal_candidates)

        rows: list[dict[str, Any]] = []
        for i, row in enumerate(reader, start=2):
            house = infer_field(row, ["house", "name", "team", "group", "category"])
            points = infer_field(row, ["points", "score", "value", "total"])
            goal = infer_field(row, goal_candidates)

            if house is None or points is None:
                available = ", ".join(fieldnames)
                raise ValueError(
                    "Could not infer the house/points columns. "
                    "Expected headers like House/Points, house/points, team/score, or name/value. "
                    f"Found: {available}"
                )

            house_name = normalize_house_name(str(house))
            point_value = parse_int_field(points, line_no=i, field_name="points")

            row_data: dict[str, Any] = {"house": house_name, "points": point_value}
            if csv_has_goal_column:
                if goal is None:
                    raise ValueError(
                        f"CSV line {i} is missing a max value. "
                        "When you include a max column, every row needs one."
                    )
                goal_value = parse_int_field(goal, line_no=i, field_name="max")
                if goal_value <= 0:
                    raise ValueError(f"CSV line {i} has a non-positive max value: {goal_value!r}")
                row_data["max"] = goal_value

            rows.append(row_data)

    if not rows:
        raise ValueError("CSV parsed successfully but contains no data rows.")

    return rows


class HousePointsHandler(BaseHTTPRequestHandler):
    server_version = "HousePointsHTTP/3.7"

    def _send_bytes(self, status: int, data: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, status: int, body: str, content_type: str = "text/plain; charset=utf-8") -> None:
        self._send_bytes(status, body.encode("utf-8"), content_type)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        self._send_text(status, json.dumps(payload), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/?"):
            self._send_text(200, HTML_PAGE, "text/html; charset=utf-8")
            return
        if self.path.startswith("/api/points"):
            self.handle_points_api()
            return
        if self.path.startswith("/static/"):
            self.handle_static()
            return
        self._send_text(404, "Not found")

    def handle_points_api(self) -> None:
        config: AppConfig = self.server.app_config  # type: ignore[attr-defined]
        now = int(time.time())

        try:
            rows = parse_points_csv(config.csv_path)
            self._send_json(200, {
                "rows": rows,
                "updated_at": now,
                "csv_path": str(config.csv_path),
                "poll_seconds": config.poll_seconds,
            })
        except Exception as exc:
            self._send_json(200, {
                "error": str(exc),
                "updated_at": now,
                "csv_path": str(config.csv_path),
            })

    def handle_static(self) -> None:
        config: AppConfig = self.server.app_config  # type: ignore[attr-defined]
        rel = self.path[len("/static/"):].split("?", 1)[0]
        rel_path = Path(rel)

        if rel_path.is_absolute() or ".." in rel_path.parts:
            self._send_text(403, "Forbidden")
            return

        static_root = config.static_dir.resolve()
        requested = rel_path.name
        if requested == "tube_base.png":
            preferred = (config.static_dir / "tube_base.png").resolve()
            fallback = (config.static_dir / "tube_empty.png").resolve()
            if preferred.exists() and preferred.is_file():
                file_path = preferred
            else:
                file_path = fallback
        else:
            file_path = (config.static_dir / rel_path).resolve()

        if static_root not in file_path.parents and file_path != static_root:
            self._send_text(403, "Forbidden")
            return

        if not file_path.exists() or not file_path.is_file():
            self._send_text(404, "Static file not found")
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        self._send_bytes(200, file_path.read_bytes(), content_type or "application/octet-stream")

    def log_message(self, fmt: str, *args: Any) -> None:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        print("%s - - [%s] %s" % (self.client_address[0], ts, fmt % args))

def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

BASE_DIR = app_dir()
CSV_PATH = BASE_DIR / "house_points.csv"
STATIC_DIR = BASE_DIR / "static"

def main() -> None:
    parser = argparse.ArgumentParser(description="Serve a live House Points scoreboard from a CSV file.")
    parser.add_argument("--csv", required=True, help="Path to the CSV file containing house points.")
    parser.add_argument("--host", default="127.0.0.1", help="Host/IP to bind to.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to.")
    parser.add_argument("--static-dir", default="static", help="Directory containing image assets.")
    parser.add_argument("--poll-seconds", type=int, default=5, help="Refresh interval in seconds.")
    args = parser.parse_args()

    config = AppConfig(
        csv_path=Path(args.csv).expanduser().resolve(),
        static_dir=Path(args.static_dir).expanduser().resolve(),
        poll_seconds=max(1, args.poll_seconds),
    )

    server = ThreadingHTTPServer((args.host, args.port), HousePointsHandler)
    server.app_config = config  # type: ignore[attr-defined]

    print(f"Serving on http://{args.host}:{args.port}")
    print(f"CSV: {config.csv_path}")
    print(f"Static: {config.static_dir}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
