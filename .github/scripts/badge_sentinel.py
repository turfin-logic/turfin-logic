#!/usr/bin/env python3
"""
Badge Sentinel & Self-Healing Agent
Monitors GitHub Profile README badges, detects Camo proxy failures (404 / 'Cannot proxy the given URL'),
attempts cache purges, and automatically heals broken badges with active fallbacks and cache busters.
"""

import os
import re
import sys
import time
import urllib.request
import urllib.error

# Ensure UTF-8 output encoding across all operating systems
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
GITHUB_USERNAME = os.environ.get("GITHUB_REPOSITORY_OWNER", "turfin-logic")
README_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "README.md") if not os.path.exists("README.md") else "README.md"

def fetch_url(url, method="GET", timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
            return resp.status, content, resp.headers
    except urllib.error.HTTPError as e:
        body = e.read() if hasattr(e, 'read') else b""
        return e.code, body, e.headers
    except Exception as e:
        return 0, str(e).encode('utf-8'), {}

def get_last_known_views(default_count=221):
    """Attempt to fetch the latest view count from available counters to preserve count during failover."""
    # Try komarev direct
    try:
        status, body, _ = fetch_url(f"https://komarev.com/ghpvc/?username={GITHUB_USERNAME}&label=Profile%20Views&color=0e75b6&style=flat")
        if status == 200:
            match = re.search(r">(\d+)</text>", body.decode('utf-8', errors='ignore'))
            if match:
                return int(match.group(1))
    except Exception:
        pass

    # Try hits.sh
    try:
        status, body, _ = fetch_url(f"https://hits.sh/github.com/{GITHUB_USERNAME}/hits.svg")
        if status == 200:
            match = re.search(r"aria-label=\"[^\"]*?(\d+)\"", body.decode('utf-8', errors='ignore'))
            if match:
                return int(match.group(1))
    except Exception:
        pass

    return default_count

def check_and_heal():
    if not os.path.exists(README_PATH):
        print(f"[ERROR] README not found at {README_PATH}")
        sys.exit(1)

    with open(README_PATH, "r", encoding="utf-8") as f:
        readme_content = f.read()

    print(f"[*] Checking Profile page for user: {GITHUB_USERNAME}...")
    profile_url = f"https://github.com/{GITHUB_USERNAME}"
    status, profile_html_bytes, _ = fetch_url(profile_url)
    if status != 200:
        print(f"[WARN] Could not fetch profile page ({status}), falling back to direct README inspection.")
        profile_html = ""
    else:
        profile_html = profile_html_bytes.decode('utf-8', errors='ignore')

    # Find all Camo URLs on profile page
    camo_matches = list(set(re.findall(r"https://camo\.githubusercontent\.com/([a-f0-9]+)/([a-f0-9]+)", profile_html)))
    broken_urls = []

    print(f"[*] Found {len(camo_matches)} Camo-proxied resources on profile.")
    for digest, hex_url in camo_matches:
        camo_full_url = f"https://camo.githubusercontent.com/{digest}/{hex_url}"
        try:
            target_url = bytes.fromhex(hex_url).decode('utf-8', errors='ignore')
        except Exception:
            target_url = "unknown"

        camo_status, camo_body, _ = fetch_url(camo_full_url)
        body_text = camo_body.decode('utf-8', errors='ignore').strip()

        if camo_status != 200 or "Cannot proxy the given URL" in body_text:
            print(f"[!] Broken Camo detected: {camo_status} | Target: {target_url}")
            
            # 1. Try Camo PURGE first
            print(f"[*] Attempting Camo PURGE for {camo_full_url[:50]}...")
            purge_status, _, _ = fetch_url(camo_full_url, method="PURGE")
            time.sleep(1)
            retry_status, retry_body, _ = fetch_url(camo_full_url)
            if retry_status == 200 and "Cannot proxy the given URL" not in retry_body.decode('utf-8', errors='ignore'):
                print(f"[SUCCESS] Camo PURGE succeeded! Resource is healthy again.")
                continue

            broken_urls.append((target_url, camo_full_url))
        else:
            print(f"[OK] 200 OK: {target_url[:60]}...")

    healed = False
    new_readme = readme_content

    # Heal broken targets
    for target_url, camo_url in broken_urls:
        print(f"[*] Self-healing broken target: {target_url}")
        
        # Scenario 1: Komarev view counter failing
        if "komarev.com/ghpvc" in target_url:
            last_views = get_last_known_views(221)
            print(f"[+] Migrating to hits.sh high-availability provider (preserving {last_views} views)...")
            fallback_url = f"https://hits.sh/github.com/{GITHUB_USERNAME}/hits.svg?label=Profile%20Views&color=0e75b6&style=flat&extraCount={last_views}"
            new_readme = re.sub(
                r'https://komarev\.com/ghpvc/[^"\'\s)]+',
                fallback_url,
                new_readme
            )
            healed = True

        # Scenario 2: hits.sh failing -> fallback to Komarev with base count
        elif "hits.sh" in target_url:
            last_views = get_last_known_views(221)
            print(f"[+] hits.sh failing! Migrating to Komarev (preserving {last_views} views)...")
            fallback_url = f"https://komarev.com/ghpvc/?username={GITHUB_USERNAME}&label=Profile%20Views&color=0e75b6&style=flat&base={last_views}"
            new_readme = re.sub(
                r'https://hits\.sh/[^"\'\s)]+',
                fallback_url,
                new_readme
            )
            healed = True

        # Scenario 3: Generic broken badge/image -> Add cache-busting parameter to force Camo to generate new hash
        else:
            print(f"[+] Applying Camo cache-busting param to: {target_url}")
            timestamp = int(time.time())
            if "?" in target_url:
                new_target = re.sub(r'([?&])cb=\d+', r'\1cb=' + str(timestamp), target_url)
                if new_target == target_url:
                    new_target = f"{target_url}&cb={timestamp}"
            else:
                new_target = f"{target_url}?cb={timestamp}"
            
            new_readme = new_readme.replace(target_url, new_target)
            healed = True

    if healed and new_readme != readme_content:
        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(new_readme)
        print("[SUCCESS] README.md successfully healed and updated!")
        
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output and os.path.exists(github_output):
            with open(github_output, "a", encoding="utf-8") as f:
                f.write("healed=true\n")
    else:
        print("[*] All profile badges and assets are healthy. No changes required.")
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output and os.path.exists(github_output):
            with open(github_output, "a", encoding="utf-8") as f:
                f.write("healed=false\n")

if __name__ == "__main__":
    check_and_heal()
