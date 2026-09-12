#!/usr/bin/env python3
"""Pull profile metrics from the GitHub API into a JSON cache."""
import json, os, sys, urllib.request, urllib.error
from datetime import datetime, timezone

USER  = os.environ.get("GH_USER", "Surajsm60720")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

QUERY = """
query($login:String!) {
  user(login:$login) {
    followers { totalCount }
    following { totalCount }
    repositories(first:100, ownerAffiliations:OWNER, isFork:false,
                 orderBy:{field:PUSHED_AT, direction:DESC}) {
      totalCount
      nodes {
        name stargazerCount pushedAt primaryLanguage { name }
        languages(first:8, orderBy:{field:SIZE, direction:DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}"""

def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}",
                 "Content-Type": "application/json",
                 "User-Agent": "profile-renderer"})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload:
        raise SystemExit(f"GraphQL error: {payload['errors']}")
    return payload["data"]

def streaks(weeks):
    days = [d for w in weeks for d in w["contributionDays"]]
    days.sort(key=lambda d: d["date"])
    today = datetime.now(timezone.utc).date().isoformat()
    days = [d for d in days if d["date"] <= today]
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)
    current = 0
    for d in reversed(days):
        if d["contributionCount"] > 0:
            current += 1
        elif d["date"] != today:        # today still has time to count
            break
    return current, longest

def main():
    if not TOKEN:
        raise SystemExit("GITHUB_TOKEN is required")
    u = gql(QUERY, {"login": USER})["user"]
    repos = u["repositories"]["nodes"]
    cc    = u["contributionsCollection"]
    cal   = cc["contributionCalendar"]

    langs = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]

    cur, longest = streaks(cal["weeks"])
    out = {
        "generated_at":  datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "followers":     u["followers"]["totalCount"],
        "following":     u["following"]["totalCount"],
        "repos":         u["repositories"]["totalCount"],
        "stars":         sum(r["stargazerCount"] for r in repos),
        "commits_year":  cc["totalCommitContributions"],
        "prs_year":      cc["totalPullRequestContributions"],
        "contributions": cal["totalContributions"],
        "streak_current": cur,
        "streak_longest": longest,
        "languages":     [{"name": n, "pct": round(v*100/total, 1)} for n, v in top],
        "recent":        [{"name": r["name"],
                           "lang": (r["primaryLanguage"] or {}).get("name"),
                           "stars": r["stargazerCount"],
                           "pushed": r["pushedAt"][:10]} for r in repos[:6]],
    }
    path = sys.argv[1] if len(sys.argv) > 1 else "metrics.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"{path}: {out['repos']} repos, {out['stars']} stars, "
          f"{out['contributions']} contributions, streak {cur}/{longest}")

if __name__ == "__main__":
    main()
