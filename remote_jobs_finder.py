"""
remote_jobs_finder.py

Kai remote job boards se ek saath jobs nikaalta hai — active jobs +
seedhe APPLY LINKS — aur sab ek CSV mein daal deta hai.

Ye teen FREE, LEGAL APIs use karta hai (koi key nahi chahiye):
    - Remotive     (remote tech jobs, worldwide)
    - Arbeitnow    (Europe + Germany focus, remote)
    - RemoteOK     (worldwide remote)

Chalao:
    python remote_jobs_finder.py
    python remote_jobs_finder.py --keyword "python"
    python remote_jobs_finder.py --keyword "data" --limit 100

NOTE: ye boards khud data dena chahte hain — isliye legal. Google/LinkedIn
ko seedha scrape karna ILLEGAL/ban-able hai. Hamesha khule darwaze (API) se lo.
"""

import argparse
import csv
import time

import requests


HEADERS = {"User-Agent": "job-finder-learning-script"}


# -----------------------------------------------------------------------------
# Har board ka apna function. Har ek alag JSON deta hai, hum sabko ek jaisi
# saaf row mein badalte hain: {title, company, location, tags, apply_link, source}
# -----------------------------------------------------------------------------
def from_remotive(keyword):
    jobs = []
    try:
        url = "https://remotive.com/api/remote-jobs"
        params = {"search": keyword} if keyword else {}
        r = requests.get(url, params=params, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            for j in r.json().get("jobs", []):
                jobs.append({
                    "title": j.get("title", ""),
                    "company": j.get("company_name", ""),
                    "location": j.get("candidate_required_location", "Remote"),
                    "tags": ", ".join(j.get("tags", [])[:4]),
                    "apply_link": j.get("url", ""),
                    "source": "Remotive",
                })
    except requests.RequestException as e:
        print(f"  Remotive skip (network): {e}")
    return jobs


def from_arbeitnow(keyword):
    jobs = []
    try:
        # Arbeitnow: Europe/Germany focus. Ye keyword param nahi leta,
        # isliye hum sab laate hain phir khud filter karte hain.
        url = "https://www.arbeitnow.com/api/job-board-api"
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            for j in r.json().get("data", []):
                title = j.get("title", "")
                tags = j.get("tags", []) or []
                blob = (title + " " + " ".join(tags)).lower()
                if keyword and keyword.lower() not in blob:
                    continue
                if not j.get("remote", False):
                    continue
                jobs.append({
                    "title": title,
                    "company": j.get("company_name", ""),
                    "location": j.get("location", "Europe"),
                    "tags": ", ".join(tags[:4]),
                    "apply_link": j.get("url", ""),
                    "source": "Arbeitnow",
                })
    except requests.RequestException as e:
        print(f"  Arbeitnow skip (network): {e}")
    return jobs


def from_remoteok(keyword):
    jobs = []
    try:
        url = "https://remoteok.com/api"
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200:
            data = r.json()
            for j in data:
                # pehla element metadata hota hai, usme 'position' nahi hoti
                if not isinstance(j, dict) or not j.get("position"):
                    continue
                title = j.get("position", "")
                tags = j.get("tags", []) or []
                blob = (title + " " + " ".join(tags)).lower()
                if keyword and keyword.lower() not in blob:
                    continue
                jobs.append({
                    "title": title,
                    "company": j.get("company", ""),
                    "location": j.get("location") or "Remote",
                    "tags": ", ".join(tags[:4]),
                    "apply_link": j.get("url", ""),
                    "source": "RemoteOK",
                })
    except requests.RequestException as e:
        print(f"  RemoteOK skip (network): {e}")
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyword", default="python",
                    help="job type dhoondo, jaise 'python', 'data', 'react'")
    ap.add_argument("--limit", type=int, default=60, help="max jobs to save")
    args = ap.parse_args()

    print(f"\n  '{args.keyword}' remote jobs dhoond raha hoon (3 boards)...\n")

    all_jobs = []
    for name, fn in [("Remotive", from_remotive),
                     ("Arbeitnow", from_arbeitnow),
                     ("RemoteOK", from_remoteok)]:
        found = fn(args.keyword)
        print(f"  {name:<12} {len(found)} jobs")
        all_jobs.extend(found)
        time.sleep(0.5)   # har board ke beech ruko (tameez)

    # -------------------------------------------------------------------------
    # DEDUP — ek hi job kai boards par ho sakti hai. Title+company se hataao.
    # -------------------------------------------------------------------------
    seen = set()
    unique = []
    for job in all_jobs:
        key = (job["title"].lower().strip(), job["company"].lower().strip())
        if key not in seen and job["apply_link"]:
            seen.add(key)
            unique.append(job)

    unique = unique[:args.limit]

    if not unique:
        print("\n  Koi job nahi mili. Doosra keyword try karo (jaise 'developer').\n")
        return

    with open("remote_jobs.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(unique[0].keys()))
        w.writeheader()
        w.writerows(unique)

    print(f"\n  {len(unique)} unique jobs save huin -> remote_jobs.csv\n")

    # pehli 5 dikhao
    print("  Kuch misaalein:\n")
    for job in unique[:5]:
        print(f"  • {job['title']}  ({job['company']})")
        print(f"    {job['location']}  |  {job['source']}")
        print(f"    Apply: {job['apply_link']}\n")

    print("  remote_jobs.csv Excel mein kholo — saari jobs + apply links.\n")

    print("AB YE KARO:")
    print("  1. --keyword badlo: --keyword 'react'  ya  'data analyst'")
    print("  2. --limit barhao: --limit 150")
    print("  3. CSV se roz 5-10 jobs par apply karo. Consistency = job.\n")


if __name__ == "__main__":
    main()
