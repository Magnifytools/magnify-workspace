#!/usr/bin/env python3
"""SEO AutoResearch Runner.

Autonomous loop that fetches Engine data, analyzes with Claude,
self-evaluates quality, and iterates to improve.

Inspired by Karpathy's autoresearch pattern.

Usage:
    python3 scripts/autoresearch/runner.py --project-id 1 --iterations 5
    python3 scripts/autoresearch/runner.py --project-id 1 --iterations 5 --engine-url http://localhost:8001
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import requests
    import anthropic
except ImportError:
    print("pip install requests anthropic")
    sys.exit(1)


# ── Config ────────────────────────────────────────────────────────────

SUPABASE_URL = "https://zzjesnxinsbzqqjmgcub.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp6amVzbnhpbnNienFxam1nY3ViIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3Mzg2ODksImV4cCI6MjA4NTMxNDY4OX0.73rLJ2mfnIfzTfac_xOaDagj1JXCXBzB3C2n0Y_2yes"
USER = {"email": "david@magnify.ing", "password": "Magnify2026!"}

PROGRAM_PATH = Path(__file__).parent / "program.md"
OUTPUT_DIR = Path(__file__).parent / "output"


def login(engine_url: str) -> Optional[str]:
    """Login to Engine backend."""
    try:
        resp = requests.post(
            f"{engine_url}/api/auth/login",
            json=USER,
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except Exception:
        pass
    # Fallback: Supabase direct
    try:
        resp = requests.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            json=USER,
            headers={"apikey": SUPABASE_ANON_KEY},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except Exception:
        pass
    return None


def fetch_data(engine_url: str, token: str, project_id: int, endpoints: List[str]) -> Dict:
    """Fetch data from multiple Engine endpoints."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {}
    for ep in endpoints:
        path = ep.replace("{pid}", str(project_id))
        try:
            resp = requests.get(f"{engine_url}/api{path}", headers=headers, timeout=15)
            if resp.status_code == 200:
                data[ep] = resp.json()
            else:
                data[ep] = {"error": resp.status_code}
        except Exception as e:
            data[ep] = {"error": str(e)[:80]}
    return data


def analyze_with_claude(program: str, data: Dict, iteration: int, previous_findings: List[Dict]) -> Dict:
    """Send data to Claude for analysis. Returns finding dict."""
    client = anthropic.Anthropic()

    prev_text = ""
    if previous_findings:
        prev_text = "\n\nHallazgos anteriores (mejorar sobre estos):\n"
        for f in previous_findings:
            prev_text += f"- [{f.get('score', '?')}/10] {f.get('title', '?')}: {f.get('summary', '')[:100]}\n"

    prompt = f"""Eres un analista SEO senior. Iteración {iteration} del análisis.

{program}

## Datos actuales:
```json
{json.dumps(data, indent=2, default=str)[:8000]}
```
{prev_text}

Genera UN hallazgo accionable basado en los datos. Formato JSON exacto:
{{
  "title": "Título del hallazgo (máx 80 chars)",
  "summary": "Resumen en 2-3 frases con datos concretos",
  "data_points": ["dato1 con número", "dato2 con número"],
  "action": "Qué hacer exactamente (accionable y específico)",
  "priority": "high|medium|low",
  "self_score": {{
    "actionable": 1-3,
    "data_backed": 1-3,
    "specific": 1-2,
    "novel": 1-2,
    "total": 1-10
  }}
}}

Solo JSON, nada más."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        # Extract JSON from response
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as e:
        return {"title": "Error en análisis", "summary": str(e)[:200], "self_score": {"total": 0}}


def run_iteration(
    engine_url: str,
    token: str,
    project_id: int,
    iteration: int,
    program: str,
    previous_findings: List[Dict],
) -> Dict:
    """Run one research iteration."""
    # Define what data to fetch based on iteration
    base_endpoints = [
        "/content-performance/projects/{pid}/intent-shift?days=60",
        "/content-performance/projects/{pid}/performance-by-page-type?days=60",
    ]

    if iteration == 1:
        endpoints = base_endpoints
    elif iteration == 2:
        endpoints = base_endpoints + [
            "/content-performance/projects/{pid}/intent-yoy?days=60&min_clicks=5",
        ]
    elif iteration == 3:
        endpoints = base_endpoints + [
            "/projects/{pid}/sistrix/budget",
            "/projects/{pid}/rank-tracker/keywords?limit=20",
        ]
    elif iteration == 4:
        endpoints = base_endpoints + [
            "/content-performance/projects/{pid}/engagement-overview",
            "/content-performance/projects/{pid}/freshness-health",
        ]
    else:
        # Synthesis iteration — use key findings
        endpoints = base_endpoints + [
            "/projects/{pid}/influence/score",
            "/projects/{pid}/influence/brand-trend?days=90",
        ]

    # Fetch
    data = fetch_data(engine_url, token, project_id, endpoints)

    # Analyze
    finding = analyze_with_claude(program, data, iteration, previous_findings)
    finding["iteration"] = iteration
    finding["timestamp"] = datetime.utcnow().isoformat()
    finding["endpoints_used"] = list(data.keys())

    return finding


def main():
    parser = argparse.ArgumentParser(description="SEO AutoResearch Runner")
    parser.add_argument("--project-id", type=int, default=1)
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--engine-url", default="https://mellow-vision-production-80e2.up.railway.app")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    print(f"SEO AutoResearch — Project {args.project_id}")
    print(f"Engine: {args.engine_url}")
    print(f"Iterations: {args.iterations}")
    print(f"Started: {datetime.utcnow().isoformat()}")

    # Read program
    program = PROGRAM_PATH.read_text()

    # Login
    token = login(args.engine_url)
    if not token:
        print("❌ Login failed")
        sys.exit(1)
    print("✅ Logged in\n")

    # Run iterations
    findings = []
    iteration_log = []

    for i in range(1, args.iterations + 1):
        print(f"{'─'*40}")
        print(f"  Iteration {i}/{args.iterations}")
        print(f"{'─'*40}")

        start = time.time()
        finding = run_iteration(args.engine_url, token, args.project_id, i, program, findings)
        elapsed = round(time.time() - start, 1)

        score = finding.get("self_score", {}).get("total", 0)
        title = finding.get("title", "?")
        print(f"  Score: {score}/10 | {title}")
        print(f"  Time: {elapsed}s")

        if score >= 7:
            findings.append(finding)
            print(f"  ✅ Accepted (score >= 7)")
        else:
            print(f"  ⚠️  Below threshold — will iterate")

        iteration_log.append({
            "iteration": i,
            "score": score,
            "accepted": score >= 7,
            "title": title,
            "elapsed_s": elapsed,
        })

    # Save outputs
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    findings_path = OUTPUT_DIR / f"findings_{ts}.json"
    with open(findings_path, "w") as f:
        json.dump(findings, f, indent=2, default=str)

    log_path = OUTPUT_DIR / f"iteration_log_{ts}.json"
    with open(log_path, "w") as f:
        json.dump(iteration_log, f, indent=2, default=str)

    # Generate report
    report_lines = [
        f"# SEO AutoResearch Report — Project {args.project_id}",
        f"> Generated: {datetime.utcnow().isoformat()}",
        f"> Iterations: {args.iterations} | Accepted findings: {len(findings)}/{args.iterations}",
        "",
        "---",
        "",
    ]
    for i, f_item in enumerate(findings, 1):
        score = f_item.get("self_score", {}).get("total", "?")
        report_lines.extend([
            f"## {i}. {f_item.get('title', '?')} (score: {score}/10)",
            "",
            f_item.get("summary", ""),
            "",
            "**Datos:**",
        ])
        for dp in f_item.get("data_points", []):
            report_lines.append(f"- {dp}")
        report_lines.extend([
            "",
            f"**Acción:** {f_item.get('action', '?')}",
            f"**Prioridad:** {f_item.get('priority', '?')}",
            "",
            "---",
            "",
        ])

    report_path = OUTPUT_DIR / f"report_{ts}.md"
    report_path.write_text("\n".join(report_lines))

    # Summary
    avg_score = sum(il["score"] for il in iteration_log) / len(iteration_log) if iteration_log else 0
    print(f"\n{'='*40}")
    print(f"  RESULTS")
    print(f"{'='*40}")
    print(f"  Iterations: {args.iterations}")
    print(f"  Accepted findings: {len(findings)}")
    print(f"  Avg score: {avg_score:.1f}/10")
    print(f"  Report: {report_path}")
    print(f"  Findings: {findings_path}")


if __name__ == "__main__":
    main()
