"""Run: python -B tests/test_fetch_ats_jobs.py"""
import importlib.util
import os
import sys

sys.dont_write_bytecode = True
PATH = os.path.join(os.path.dirname(__file__), "..", "skills", "miao-career", "scripts", "fetch_ats_jobs.py")
SPEC = importlib.util.spec_from_file_location("fetch_ats_jobs", PATH)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)

CASES = [
    # title, body, expected match, expected largest years
    ("Data Analyst", "Master's plus 2 years of experience, or a bachelor's plus 3 years of experience.", "no", 3),
    ("Data Analyst", "MS or MA plus 2 years, or BS or BA plus 3 years, of full-time experience in analytics.", "no", 3),
    ("Security Analyst", "5+ years of IT experience and 2+ years of work in security data analysis.", "no", 5),
    ("Marketing Analyst", "0-2 years of experience in marketing.", "body", 2),
    ("Marketing Analyst", "0 to 2 years of work in marketing.", "body", 2),
    ("Marketing Analyst", "1-3 years of experience.", "no", 3),
    ("Data Analyst", "one year of experience", "body", 1),
    ("Strategist", "We build things.", "no", None),
    ("Marketing Associate", "3+ years of relevant experience", "too_senior", 3),
    ("Marketing Associate", "1-3 years of experience", "title", 3),
    ("Associate Product Manager", "", "title", None),
    ("Senior Associate", "", "no", None),
    ("Business Analyst I", "", "title", None),
    ("Head of Early Career Recruiting", "", "no", None),
]


def row(title, commitment="", body=""):
    return {"title": title, "commitment": commitment, "body": body}


EXPERIENCED = [
    # title, body, years, expected match
    ("Data Analyst", "2+ years of experience", 3, "within_years"),
    ("Senior Data Analyst", "3+ years of experience", 3, "within_years"),
    ("Senior Data Analyst", "3+ years of experience and 5+ years of work in SQL", 3, "too_senior"),
    ("Data Analyst", "2-4 years of experience", 3, "within_years"),
    ("Data Analyst", "4-6 years of experience", 3, "too_senior"),
    ("Marketing Manager", "We build things.", 3, "no_years"),
    ("Staff Product Designer", "We build things.", 3, "no"),
    ("Sr. Manager, Growth", "We build things.", 3, "no"),
    ("Sr. Manager, Growth", "6+ years of experience", 8, "within_years"),
    ("Director of Analytics", "2 years of experience", 3, "no"),
    ("VP, Marketing", "", 3, "no"),
    ("Principal Analyst", "", 3, "no"),
    ("Data Analyst Intern", "", 3, "no"),
]

TYPES = [
    (row("Analyst"), "fulltime_assumed"),
    (row("Analyst", "Full-time"), "fulltime"),
    (row("Analyst", "FullTime"), "fulltime"),
    (row("Analyst", body="This is a full-time role."), "fulltime"),
    (row("Analyst Intern"), "intern"),
    (row("Analyst", "Contract"), "contract"),
    (row("Analyst", "PartTime"), "part_time"),
]


def main():
    bad = 0
    for title, body, want_match, want_years in CASES:
        got = M.classify(title, body)
        if got != (want_match, want_years):
            bad += 1
            print("BAD", title, "|", body, "=>", got, "want", (want_match, want_years))
    for title, body, years, want in EXPERIENCED:
        got = M.classify_experienced(title, body, years)[0]
        if got != want:
            bad += 1
            print("BAD", title, "|", body, "=>", got, "want", want)
    for item, want in TYPES:
        got = M.job_type(item)
        if got != want:
            bad += 1
            print("BAD", item, "=>", got, "want", want)
    print("{} tests, {} failed".format(len(CASES) + len(EXPERIENCED) + len(TYPES), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
