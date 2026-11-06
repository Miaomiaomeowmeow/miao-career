#!/usr/bin/env python3
# Copyright (c) Miaomiao Yang. MIT License. Part of Miao Career.
"""Fetch jobs from the public Greenhouse / Lever / Ashby job-board APIs.

Default keeps new-grad style jobs (title words, or body says 0-2 years). With
--level experienced --years N it keeps jobs that fit N years instead. Writes a CSV
and prints only a short summary. Job text is never printed, so running this
costs almost no AI usage. Python standard library only. No login. Never applies.

One run = one direction: use a narrow keyword group, not broad words like "analyst".

Examples:
  python fetch_ats_jobs.py --companies stripe,ramp --keywords "business operations,strategy & operations" --direction "business operations"
  python fetch_ats_jobs.py --companies-file slugs.txt --keywords "marketing coordinator" --location "chicago|remote"
  python fetch_ats_jobs.py --companies lever:palantir,greenhouse:stripe --out jobs.csv --fulltext jobs.jsonl
  python fetch_ats_jobs.py --companies stripe,ramp --keywords "data analyst" --level experienced --years 3

A company code ("slug") has to be guessed from its careers-page URL. Same-name
trap: always check the sample titles this script prints for each company.
"""
import argparse
import csv
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter

USER_AGENT = "miao-career-job-search/1.0 (personal job search; public job-board API)"
MIN_SLEEP = 2.0

ENDPOINTS = {
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{}?includeCompensation=true",
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{}/jobs?content=true",
    "lever": "https://api.lever.co/v0/postings/{}?mode=json",
}

# ---- what counts as a new-grad job ----------------------------------------
TITLE_YES = re.compile(
    r"\b(intern|internship|co-?op|new grad(uate)?|recent grad(uate)?|early[- ]career|"
    r"entry[- ]level|junior|jr\.?|associate|coordinator|rotational|apprentice|fellow|"
    r"fellowship|university grad(uate)?|campus|residency|graduate program|class of 20\d\d|"
    r"20\d\d start)\b", re.I)
TITLE_LEVEL_ONE = re.compile(r"\s(I|1)\s*($|[,(|-])")
TITLE_NEVER = re.compile(r"\b(head|director|vp|vice president|chief|partner|counsel)\b", re.I)
TITLE_NO = re.compile(
    r"\b(senior|sr\.?|lead|manager|staff|principal|architect|ii|iii|iv)\b", re.I)
FAKE_ASSOCIATE = re.compile(
    r"\b(senior associate|associate (director|counsel|partner|principal|vice|general|dean|attorney|manager))\b",
    re.I)
FAR_SENIOR = re.compile(
    r"\b(director|vp|svp|evp|vice president|chief|head of|principal|managing partner|general partner)\b", re.I)
SENIOR_FOR_FEW_YEARS = re.compile(r"\b(staff|senior manager|sr\.? manager)\b", re.I)
INTERN_TITLE = re.compile(r"\b(intern|internship|co-?op)\b", re.I)
MANAGER_OK = re.compile(
    r"\b(intern|new grad(uate)?|early[- ]career|associate product manager|apm)\b", re.I)
BODY_YES = re.compile(
    r"(\b0\s*(-|–|—|to)\s*[12]\s*(\+\s*)?(years?|yrs?)\b|recent (college |university )?graduates?\b|"
    r"\bnew grad(uate)?s?\b|\bentry[- ]level\b|\bearly[- ]career\b|"
    r"\bno (prior |previous )?(work )?experience (is )?(required|necessary|needed)\b)", re.I)

WORD_NUM = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
            "seven": "7", "eight": "8", "nine": "9", "ten": "10"}
YEARS = re.compile(
    r"\b(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:\+|plus)?\s*"
    r"(?:(?:-|–|—|to)\s*(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten)\s*\+?\s*)?"
    r"(?:\(\d+\)\s*)?(?:years?|yrs?)\b"
    r"(?=[^.;\n]{0,70}?\b(?:experience|background|work|working)\b)", re.I)

# ---- flags read from the job text (rough keyword rules, check the original) -
NO_SPONSOR = re.compile(
    r"(not (be able to )?(offer |provide )?(visa |employment |immigration )?sponsor|"
    r"(unable|not able) to (offer |provide )?(visa |employment |immigration )?sponsor|"
    r"without (visa |employer |employment |immigration )?sponsorship|no (visa )?sponsorship|"
    r"sponsorship (is )?not available|does not provide [^.]{0,40}sponsorship|"
    r"u\.?s\.? citizen(s|ship)? (is |are )?(only|required)|must be a u\.?s\.? citizen|"
    r"citizens? or permanent residents?|security clearance)", re.I)
MAY_SPONSOR = re.compile(
    r"(visa sponsorship (is )?available|we (will |can |do )?sponsor|(will|can) sponsor (work )?visas?|"
    r"sponsorship (is )?available)", re.I)
OPT = re.compile(r"(\bOPT\b|\bCPT\b|(?i:optional practical training|curricular practical training))")
AI_WORDS = re.compile(
    r"(\bAI\b|\bLLMs?\b|\bGPT\b|(?i:chatgpt|\bclaude\b|generative|machine learning|agentic))")
SAMPLES = re.compile(
    r"(portfolio|work samples?|writing samples?|demo reel|\breel\b|\bclips\b)", re.I)
SAMPLES_NOT = re.compile(
    r"(product|investment|client|customer|asset|brand|company|companies|loan|credit|project|"
    r"software|solutions?|sales|account|equity|real estate|fund|financial)[- ]portfolios?|"
    r"portfolio (compan|manag|of (products|brands|clients|companies|investments|solutions))", re.I)
CODE = re.compile(
    r"(\bpython\b|\bjavascript\b|\btypescript\b|\bjava\b|c\+\+|\bgolang\b|\bwrit(e|ing) code\b|"
    r"\bcoding\b|\bprogramming\b)", re.I)
CS_DEGREE = re.compile(
    r"(degree|bachelor'?s?|master'?s?|\bb\.?s\.?\b|pursuing)[^.\n]{0,90}"
    r"(computer science|computer engineering|software engineering)", re.I)
DESIGN_DEGREE = re.compile(
    r"(degree|bachelor'?s?|master'?s?|\bBFA\b|\bMFA\b)[^.\n]{0,90}"
    r"(graphic design|interaction design|industrial design|visual design|fine arts?|"
    r"human[- ]computer interaction|\bdesign\b)", re.I)
CONTRACT = re.compile(
    r"(\bcontract(or)? (position|role|employee)\b|\bfixed[- ]term\b|\btemporary (position|role)\b)", re.I)
SALARY = re.compile(
    r"\$\s?\d{2,3}(?:,\d{3})?\s?[kK]?\s*(?:-|–|—|to)\s*\$\s?\d{2,3}(?:,\d{3})?\s?[kK]?")

# ---- location -------------------------------------------------------------
US_WORDS = re.compile(
    r"(united states|\busa\b|\bu\.s\.a?\.?\b|\bus\b|new york|\bnyc\b|san francisco|\bsf\b|bay area|"
    r"los angeles|chicago|seattle|austin|boston|atlanta|denver|washington,? ?d\.?c\.?|dallas|"
    r"houston|miami|philadelphia|san diego|san jose|palo alto|mountain view|menlo park|sunnyvale|"
    r"brooklyn|portland|minneapolis|detroit|pittsburgh|phoenix|nashville|charlotte|salt lake|"
    r"california|texas|florida|illinois|massachusetts|washington state|colorado|georgia|virginia|"
    r"north carolina|new jersey|pennsylvania|ohio|michigan|arizona|oregon|utah|tennessee|minnesota)",
    re.I)
US_ABBR = re.compile(
    r",\s*(AL|AK|AZ|AR|CA|CO|CT|DC|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|"
    r"NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b")
NOT_US = re.compile(
    r"(canada|toronto|vancouver|montreal|ontario|india|bangalore|bengaluru|hyderabad|mumbai|delhi|"
    r"pune|gurgaon|united kingdom|\buk\b|london|ireland|dublin|germany|berlin|munich|france|paris|"
    r"singapore|japan|tokyo|australia|sydney|melbourne|brazil|mexico|israel|netherlands|amsterdam|"
    r"spain|madrid|poland|warsaw|sweden|stockholm|china|hong kong|korea|seoul)", re.I)


def clean_text(raw):
    """Turn escaped HTML into plain text."""
    text = html.unescape(html.unescape(raw or ""))
    text = re.sub(r"<(br|/p|/li|/div|/h\d)[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n", text).strip()


def get_json(url):
    """Returns (data, status). status: ok / not_found / blocked / error."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            return json.loads(response.read().decode("utf-8", "replace")), "ok"
    except urllib.error.HTTPError as error:
        if error.code in (401, 403, 429):
            return None, "blocked"
        return None, "not_found" if error.code == 404 else "error"
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None, "error"


def from_ashby(data, slug):
    rows = []
    for job in data.get("jobs") or []:
        if job.get("isListed") is False:
            continue
        address = (job.get("address") or {}).get("postalAddress") or {}
        places = [job.get("location") or ""]
        for extra in job.get("secondaryLocations") or []:
            places.append(extra.get("location") or "")
        compensation = (job.get("compensation") or {}).get("compensationTierSummary") or ""
        rows.append({
            "company": slug, "ats": "ashby", "title": job.get("title") or "",
            "places": [p for p in places if p], "url": job.get("jobUrl") or "",
            "posted": (job.get("publishedAt") or "")[:10],
            "department": job.get("department") or job.get("team") or "",
            "commitment": job.get("employmentType") or "",
            "country": address.get("addressCountry") or "",
            "salary": compensation,
            "body": job.get("descriptionPlain") or clean_text(job.get("descriptionHtml")),
        })
    return rows


def from_greenhouse(data, slug):
    rows = []
    for job in data.get("jobs") or []:
        departments = job.get("departments") or []
        rows.append({
            "company": job.get("company_name") or slug, "ats": "greenhouse",
            "title": job.get("title") or "",
            "places": [(job.get("location") or {}).get("name") or ""],
            "url": job.get("absolute_url") or "",
            "posted": (job.get("first_published") or job.get("updated_at") or "")[:10],
            "department": departments[0].get("name", "") if departments else "",
            "commitment": "", "country": "", "salary": "",
            "body": clean_text(job.get("content")),
        })
    return rows


def from_lever(data, slug):
    rows = []
    for job in data if isinstance(data, list) else []:
        categories = job.get("categories") or {}
        lists = " ".join((item.get("text") or "") + " " + clean_text(item.get("content"))
                         for item in job.get("lists") or [])
        body = " ".join([job.get("descriptionPlain") or "", lists, job.get("additionalPlain") or ""])
        created = job.get("createdAt")
        salary = job.get("salaryRange") or {}
        salary_text = ""
        if salary.get("min") and salary.get("max"):
            salary_text = "{}-{} {}".format(salary["min"], salary["max"], salary.get("currency") or "")
        places = categories.get("allLocations") or [categories.get("location") or ""]
        rows.append({
            "company": slug, "ats": "lever", "title": job.get("text") or "",
            "places": [p for p in places if p], "url": job.get("hostedUrl") or "",
            "posted": time.strftime("%Y-%m-%d", time.gmtime(created / 1000)) if created else "",
            "department": categories.get("department") or categories.get("team") or "",
            "commitment": categories.get("commitment") or "",
            "country": job.get("country") or "", "salary": salary_text, "body": body.strip(),
        })
    return rows


PARSERS = {"ashby": from_ashby, "greenhouse": from_greenhouse, "lever": from_lever}


def fetch_company(slug, ats_list, sleep):
    """Try each system until one answers. Sleeps between every request."""
    network_trouble = False
    for index, ats in enumerate(ats_list):
        if index:
            time.sleep(sleep)
        data, status = get_json(ENDPOINTS[ats].format(slug))
        if status == "blocked":
            return None, ats, "blocked"
        if status == "error":
            network_trouble = True
        if status != "ok":
            continue
        rows = PARSERS[ats](data, slug)
        # An empty board on one system often means the slug lives on another one.
        if rows or index == len(ats_list) - 1:
            return rows, ats, "ok"
    return None, "", "network_error" if network_trouble else "not_found"


def is_in_location(row, wanted):
    joined = " | ".join(row["places"])
    if wanted == "any":
        return True
    if wanted == "us":
        if row["country"]:
            country = row["country"].strip().lower()
            if country in ("us", "usa", "united states", "united states of america"):
                return True
        if US_WORDS.search(joined):
            return True
        return bool(US_ABBR.search(joined)) and not NOT_US.search(joined)
    return bool(re.search(wanted, joined, re.I))


def years_mentioned(body):
    """Returns (largest, largest_floor). "0-2 years" counts as 2 for largest, 0 for floor."""
    largest = floor = None
    for match in YEARS.finditer(body or ""):
        low = int(WORD_NUM.get(match.group(1).lower(), match.group(1)))
        high_raw = match.group(2)
        high = int(WORD_NUM.get(high_raw.lower(), high_raw)) if high_raw else low
        if max(low, high) > 15:
            continue
        largest = high if largest is None else max(largest, high)
        floor = low if floor is None else max(floor, low)
    return largest, floor


def classify(title, body):
    """Returns (match, largest years in the text). match: title / body / too_senior / no.

    Body match: every year count in the text must be 2 or less.
    Title match: dropped when any requirement starts at 3+ years ("3+", "5 years");
    a range such as "1-3 years" stays, with 3 shown in the CSV.
    """
    years, floor = years_mentioned(body)
    if TITLE_NEVER.search(title) or FAKE_ASSOCIATE.search(title):
        return "no", years
    if TITLE_NO.search(title) and not MANAGER_OK.search(title):
        return "no", years
    if TITLE_YES.search(title) or TITLE_LEVEL_ONE.search(title):
        if floor is not None and floor >= 3:
            return "too_senior", years
        return "title", years
    if years is not None and years > 2:
        return "no", years
    if BODY_YES.search(body or "") or years is not None:
        return "body", years
    return "no", years


def classify_experienced(title, body, max_years):
    """Returns (match, largest years). match: within_years / no_years / too_senior / no.

    No new-grad title word needed. A requirement that starts above max_years drops
    the job; a range counts from its low end, so "2-4 years" fits 3 years.
    """
    years, floor = years_mentioned(body)
    if FAR_SENIOR.search(title) or INTERN_TITLE.search(title):
        return "no", years
    if max_years < 5 and SENIOR_FOR_FEW_YEARS.search(title):
        return "no", years
    if years is None:
        return "no_years", years
    return ("too_senior", years) if floor > max_years else ("within_years", years)


def job_type(row):
    text = " ".join([row["title"], row["commitment"]])
    if re.search(r"\b(intern|internship|co-?op)\b", text, re.I):
        return "intern"
    if re.search(r"\b(contract|contractor|temporary|temp|freelance)\b", text, re.I) or CONTRACT.search(row["body"]):
        return "contract"
    if re.search(r"part[- ]?time", text, re.I):
        return "part_time"
    if re.search(r"full[- ]?time", text + " " + row["body"], re.I):
        return "fulltime"
    return "fulltime_assumed"


def asks_for_samples(body):
    cleaned = SAMPLES_NOT.sub(" ", body or "")
    return bool(SAMPLES.search(cleaned))


def yes_no(value):
    return "yes" if value else ""


def build_record(row, match, years, hit):
    body = row["body"]
    salary = row["salary"]
    if not salary:
        found = SALARY.search(body)
        salary = found.group(0) if found else ""
    return {
        "company": row["company"], "ats": row["ats"], "title": row["title"], "match": match,
        "job_type": job_type(row), "max_years_mentioned": "" if years is None else years,
        "locations": " | ".join(row["places"]), "posted": row["posted"], "url": row["url"],
        "department": row["department"], "salary": salary, "keyword_hit": hit,
        "mentions_ai": yes_no(AI_WORDS.search(body)),
        "visa_no_sponsor": yes_no(NO_SPONSOR.search(body)),
        "visa_may_sponsor": yes_no(MAY_SPONSOR.search(body)),
        "visa_opt_mentioned": yes_no(OPT.search(body)),
        "asks_portfolio": yes_no(asks_for_samples(body)),
        "needs_code": yes_no(CODE.search(body)),
        "needs_cs_degree": yes_no(CS_DEGREE.search(body)),
        "needs_design_degree": yes_no(DESIGN_DEGREE.search(body)),
    }


FIELDS = ["company", "ats", "title", "match", "job_type", "max_years_mentioned", "locations", "posted", "url",
          "department", "salary", "keyword_hit", "mentions_ai", "visa_no_sponsor", "visa_may_sponsor",
          "visa_opt_mentioned", "asks_portfolio", "needs_code", "needs_cs_degree", "needs_design_degree"]


def dedupe(records):
    """Same company + same title in several cities counts as one job."""
    merged = {}
    for record in records:
        key = (record["company"].lower(), re.sub(r"\W+", " ", record["title"]).strip().lower())
        if key not in merged:
            merged[key] = dict(record)
            continue
        kept = merged[key]
        places = kept["locations"].split(" | ") + record["locations"].split(" | ")
        kept["locations"] = " | ".join(dict.fromkeys(p for p in places if p))
        if record["posted"] and (not kept["posted"] or record["posted"] < kept["posted"]):
            kept["posted"] = record["posted"]
    return list(merged.values())


def quantity_score(count):
    for floor, score in ((50, 40), (30, 32), (15, 24), (8, 16), (3, 8)):
        if count >= floor:
            return score
    return 3


def percent(part, whole):
    return "{:.0f}%".format(100.0 * part / whole) if whole else "n/a"


def parse_companies(args):
    items = []
    if args.companies:
        items += [c.strip() for c in args.companies.split(",") if c.strip()]
    if args.companies_file:
        with open(args.companies_file, encoding="utf-8-sig") as handle:
            for line in handle:
                line = line.split("#")[0].strip()
                if line:
                    items += [c.strip() for c in line.split(",") if c.strip()]
    return list(dict.fromkeys(items))


def main():
    parser = argparse.ArgumentParser(description="Fetch new-grad jobs from public Greenhouse / Lever / Ashby APIs.")
    parser.add_argument("--companies", help="comma-separated company codes; use ats:code to force a system, e.g. lever:palantir")
    parser.add_argument("--companies-file", help="text file with one company code per line; # starts a comment")
    parser.add_argument("--keywords", default="", help='comma-separated words for ONE direction, e.g. "business operations,bizops"; empty keeps every job')
    parser.add_argument("--keywords-in", choices=["title", "body", "both"], default="title", help="where to look for keywords (default: title)")
    parser.add_argument("--location", default="us", help='"us" (default), "any", or your own regex, e.g. "chicago|remote"')
    parser.add_argument("--level", choices=["new", "experienced"], default="new", help="new (default): new-grad style jobs; experienced: jobs that fit --years")
    parser.add_argument("--years", type=int, help="with --level experienced: the user's years of relevant experience")
    parser.add_argument("--all-levels", action="store_true", help="do not filter by level at all")
    parser.add_argument("--direction", help="say this run is one direction's sample; only then the opportunity score is printed")
    parser.add_argument("--out", default="jobs.csv", help="CSV output path (default: jobs.csv)")
    parser.add_argument("--fulltext", help="optional JSONL path to save job text, for reading one job later")
    parser.add_argument("--sleep", type=float, default=3.0, help="seconds between requests (minimum 2, default 3)")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.level == "experienced" and args.years is None:
        parser.error("--level experienced needs --years N")
    if args.level == "new" and args.years is not None:
        parser.error("--years only works with --level experienced")
    companies = parse_companies(args)
    if not companies:
        parser.error("give --companies or --companies-file")
    sleep = max(args.sleep, MIN_SLEEP)
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    patterns = [(k, re.compile(r"\b" + re.escape(k) + r"\b", re.I)) for k in keywords]

    records, dropped_senior, fulltext = [], 0, []
    total_seen = total_location = total_keyword = 0
    missing, blocked, failed, unknown, succeeded = [], [], [], [], []

    print("--- per company (check the sample titles: is this the right company?) ---")
    for position, item in enumerate(companies):
        if position:
            time.sleep(sleep)
        if ":" in item:
            forced, slug = item.split(":", 1)
            ats_list = [forced.lower()]
            if ats_list[0] not in ENDPOINTS:
                print("{}: unknown system '{}', skipped".format(item, forced))
                unknown.append(item)
                continue
        else:
            slug, ats_list = item, ["ashby", "greenhouse", "lever"]
        rows, ats, status = fetch_company(slug, ats_list, sleep)
        if status == "blocked":
            blocked.append(slug)
            print("{}: {} refused the request (401/403/429). Stopping here; do not retry right away.".format(slug, ats))
            break
        if status == "network_error":
            failed.append(slug)
            print("{}: could not connect. This is a network problem, not a wrong code.".format(slug))
            if len(failed) >= 2 and total_seen == 0:
                print("Stopping: no connection. If your AI runs commands in a sandbox, allow network access or run this command in your own terminal.")
                break
            continue
        if status != "ok":
            missing.append(slug)
            print("{}: not found on {}".format(slug, " / ".join(ats_list)))
            continue
        succeeded.append(slug)
        kept_here = 0
        for row in rows:
            total_seen += 1
            if not is_in_location(row, args.location):
                continue
            total_location += 1
            hit = ""
            if patterns:
                haystack = {"title": row["title"], "body": row["body"]}.get(args.keywords_in, row["title"] + " " + row["body"])
                hits = [k for k, pattern in patterns if pattern.search(haystack)]
                if not hits:
                    continue
                hit = ",".join(hits)
            total_keyword += 1
            if args.all_levels:
                match, years = "all", years_mentioned(row["body"])[0]
            elif args.level == "experienced":
                match, years = classify_experienced(row["title"], row["body"], args.years)
            else:
                match, years = classify(row["title"], row["body"])
            if match == "too_senior":
                dropped_senior += 1
                continue
            if match == "no":
                continue
            kept_here += 1
            records.append(build_record(row, match, years, hit))
            if args.fulltext:
                fulltext.append({"company": row["company"], "title": row["title"], "url": row["url"], "body": row["body"]})
        samples = "; ".join(row["title"][:40] for row in rows[:3])
        print("{} [{}]: {} jobs, kept {}. e.g. {}".format(slug, ats, len(rows), kept_here, samples or "(empty board)"))

    before_dedupe = len(records)
    records = dedupe(records)
    for path in (args.out, args.fulltext):
        if path and os.path.dirname(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)
    if args.fulltext:
        with open(args.fulltext, "w", encoding="utf-8") as handle:
            for item in fulltext:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")

    types = Counter(r["job_type"] for r in records)
    stated, assumed = types["fulltime"], types["fulltime_assumed"]
    fail_count = len(missing) + len(blocked) + len(failed) + len(unknown)
    print("\n--- summary (a one-day snapshot of these companies, not the whole market) ---")
    print("companies: asked {}, succeeded {}, failed {} (not found {}, refused {}, network error {}, unknown system {}), not tried {}".format(
        len(companies), len(succeeded), fail_count, len(missing), len(blocked), len(failed), len(unknown),
        len(companies) - len(succeeded) - fail_count))
    print("jobs: seen {}, in location {}, keyword match {}".format(total_seen, total_location, total_keyword))
    print("kept candidates: {} rows before merging cities, {} after".format(before_dedupe, len(records)))
    print("by type: full-time stated {}, full-time assumed (not stated) {}, intern {}, contract {}, part-time {}".format(
        stated, assumed, types["intern"], types["contract"], types["part_time"]))
    if args.level == "experienced":
        print("found by: years in text fit {} or less {}, no years in text {}".format(
            args.years, sum(r["match"] == "within_years" for r in records), sum(r["match"] == "no_years" for r in records)))
        print("dropped: text mentions more than {} years: {}".format(args.years, dropped_senior))
        over_label = "over {} years".format(args.years)
    else:
        print("found by: title {}, body only (every year count in text is 2 or less) {}".format(
            sum(r["match"] == "title" for r in records), sum(r["match"] == "body" for r in records)))
        print("dropped: new-grad style title but text asks 3+ years: {}".format(dropped_senior))
        over_label = "3+ years"
    count = len(records)
    print("flags, share of kept rows: no sponsorship {}, OPT/CPT mentioned {}, mentions AI {}, asks portfolio {}".format(
        percent(sum(bool(r["visa_no_sponsor"]) for r in records), count),
        percent(sum(bool(r["visa_opt_mentioned"]) for r in records), count),
        percent(sum(bool(r["mentions_ai"]) for r in records), count),
        percent(sum(bool(r["asks_portfolio"]) for r in records), count)))

    if args.direction and not args.all_levels and (count or dropped_senior):
        whole = count + dropped_senior
        share_3 = dropped_senior / whole
        share_code = sum(bool(r["needs_code"]) for r in records) / whole
        share_design = sum(bool(r["needs_design_degree"]) for r in records) / whole
        share_cs = sum(bool(r["needs_cs_degree"]) for r in records) / whole
        gate = 35 - share_3 * 10 - share_code * 10 - share_design * 8 - share_cs * 7
        quantity = quantity_score(stated + assumed)
        print("\nstep-2 opportunity score for direction: {}".format(args.direction))
        print("quantity counts full-time stated + assumed: {} + {}".format(stated, assumed))
        print("gate shares, of kept rows + dropped ({} rows): {} {:.0%}, code {:.0%}, design degree {:.0%}, CS degree {:.0%}".format(
            whole, over_label, share_3, share_code, share_design, share_cs))
        print("quantity {} + gate {:.1f} => opportunity {:.1f} / 100".format(
            quantity, gate, (quantity + gate) * 100 / 75))
    elif not args.direction:
        print("\nNo opportunity score: add --direction NAME only if this run is one direction's sample.")
    print("\nCSV: {}".format(args.out))
    if args.fulltext:
        print("Job text: {} (read one job at a time, not the whole file)".format(args.fulltext))
    print("These are keyword candidates, not verified jobs. Empty flag means not found, not \"no\". Read the job page before you trust them or apply.")


if __name__ == "__main__":
    main()
