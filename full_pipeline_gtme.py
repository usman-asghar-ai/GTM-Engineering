

    SOURCE  ->  QUALIFY  ->  PERSONALIZE   


import argparse
import csv
import json
import os
import sys
import time


def stage_source():
    print("  [1/3] SOURCE  — leads la raha hoon...")
    leads = [
        {"name": "Guido van Rossum", "company": "Microsoft",  "location": "Seattle",  "followers": 80000, "public_repos": 30},
        {"name": "Ali Khan",         "company": "TechCorp",   "location": "Lahore",   "followers": 3200,  "public_repos": 45},
        {"name": "Sara Ahmed",       "company": "DataSoft",   "location": "Karachi",  "followers": 850,   "public_repos": 22},
        {"name": "New Person",       "company": "",           "location": "",         "followers": 12,    "public_repos": 2},
        {"name": "Ahmed Raza",       "company": "CloudNine",  "location": "Dubai",    "followers": 5400,  "public_repos": 60},
    ]
    time.sleep(0.3)
    print(f"        {len(leads)} leads mile\n")
    return leads

ICP = "Hum developers ke liye tool bechte hain. Achha lead: company mein hai, active repos, achhi (magar bohot zyada nahi) reach."


def qualify_mock(lead):
    score, reasons = 5, []
    if lead.get("company"):
        score += 2; reasons.append("company mein hai")
    else:
        score -= 1; reasons.append("koi company nahi")
    if (lead.get("public_repos") or 0) > 5:
        score += 1; reasons.append("active")
    f = lead.get("followers") or 0
    if 1000 <= f <= 100000:
        score += 2; reasons.append("achhi reach")
    elif f > 100000:
        score -= 1; reasons.append("bohot bara")
    score = max(1, min(10, score))
    return {"score": score, "reason": ", ".join(reasons)}


def qualify_ai(lead, client):
    prompt = f"""Lead qualification. ICP: {ICP}
Lead: {lead.get('name')}, {lead.get('company')}, {lead.get('followers')} followers, {lead.get('public_repos')} repos.
Sirf JSON: {{"score": <1-10>, "reason": "<chhoti wajah>"}}"""
    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=120,
                                  messages=[{"role": "user", "content": prompt}])
    t = "".join(b.text for b in resp.content if b.type == "text").strip()
    if t.startswith("```"):
        t = t.split("```")[1].replace("json", "", 1).strip()
    return json.loads(t)


def stage_qualify(leads, real, client):
    print("  [2/3] QUALIFY — har lead ko score de raha hoon...")
    for lead in leads:
        q = qualify_ai(lead, client) if real else qualify_mock(lead)
        lead["score"] = q["score"]
        lead["reason"] = q["reason"]
        if real:
            time.sleep(0.3)
    passed = [l for l in leads if l["score"] >= 7]
    print(f"        {len(passed)}/{len(leads)} leads 7+ score ke\n")
    return passed


OFFER = "Hum developers ke liye ek tool banate hain jo code review tez karta hai."
SENDER = "Usman"


def email_mock(lead):
    first = (lead.get("name") or "there").split()[0]
    company = lead.get("company") or "your team"
    return {
        "subject": f"quick idea for {company}",
        "body": f"Hi {first},\n\nI saw you're a developer at {company}. {OFFER} Open to a quick look?\n\nBest,\n{SENDER}",
    }


def email_ai(lead, client):
    prompt = f"""Cold email likho. Bechte hain: {OFFER}
Lead: {lead.get('name')}, {lead.get('company')}, {lead.get('followers')} followers, {lead.get('public_repos')} repos.
Rules: 70 lafz se kam, pehli line lead ke bare mein specific, koi jhoot nahi, sign "{SENDER}".
Sirf JSON: {{"subject":"<lowercase, 5 lafz se kam>","body":"<email>"}}"""
    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=350,
                                  messages=[{"role": "user", "content": prompt}])
    t = "".join(b.text for b in resp.content if b.type == "text").strip()
    if t.startswith("```"):
        t = t.split("```")[1].replace("json", "", 1).strip()
    return json.loads(t)


def stage_personalize(leads, real, client):
    print("  [3/3] PERSONALIZE — emails likh raha hoon...")
    for lead in leads:
        e = email_ai(lead, client) if real else email_mock(lead)
        lead["subject"] = e["subject"]
        lead["body"] = e["body"]
        if real:
            time.sleep(0.3)
    print(f"        {len(leads)} emails taiyar\n")
    return leads

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", action="store_true", help="asli AI (key chahiye)")
    args = ap.parse_args()

    client = None
    if args.real:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("\n  --real maanga lekin ANTHROPIC_API_KEY nahi. Bina --real chalao.\n")
            sys.exit(1)
        from anthropic import Anthropic
        client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    mode = "ASLI AI" if args.real else "MOCK (muft)"
    print(f"\n  === GTM PIPELINE === mode: {mode}\n")

    # yahan data ek stage se doosri mein behta hai — yehi pipeline hai
    leads = stage_source()
    qualified = stage_qualify(leads, args.real, client)

    if not qualified:
        print("  Koi lead qualify nahi hua. ICP dekho.\n")
        return

    final = stage_personalize(qualified, args.real, client)

    # output
    with open("pipeline_output.csv", "w", newline="", encoding="utf-8") as f:
        cols = ["name", "company", "score", "reason", "subject", "body"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(final)

    with open("pipeline_review.txt", "w", encoding="utf-8") as f:
        f.write("REVIEW — bhejne se pehle har email parho.\n" + "=" * 55 + "\n\n")
        for l in final:
            f.write(f"TO: {l['name']} ({l['company']})  —  score {l['score']}/10\n")
            f.write(f"SUBJECT: {l['subject']}\n\n{l['body']}\n\n" + "-" * 55 + "\n\n")

    print("  === MUKAMMAL ===")
    print(f"    pipeline_output.csv   -> sending tool ke liye")
    print(f"    pipeline_review.txt   -> PEHLE YE PARHO\n")

    print("  Aapne abhi poori GTM pipeline EK COMMAND mein chalayi:")
    print("    source -> qualify -> personalize\n")
    print("  Yehi woh cheez hai jiske liye companies paise deti hain.\n")


if __name__ == "__main__":
    main()
