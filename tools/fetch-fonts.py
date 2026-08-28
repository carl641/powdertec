#!/usr/bin/env python3
"""Re-downloads the self-hosted webfonts from Google Fonts (latin subset only).

    python3 tools/fetch-fonts.py

Writes assets/fonts/*.woff2 and regenerates assets/css/fonts.css.
"""
import os, re, subprocess, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = ("https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700"
       "&family=Big+Shoulders+Display:wght@600;700;800;900&display=swap")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

req = urllib.request.Request(API, headers={"User-Agent": UA})
css = urllib.request.urlopen(req, timeout=30).read().decode()

fonts_dir = os.path.join(ROOT, "assets", "fonts")
os.makedirs(fonts_dir, exist_ok=True)

seen, faces = {}, []
for block in re.findall(r"@font-face\s*\{[^}]*\}", css):
    rng = re.search(r"unicode-range:\s*([^;]+);", block)
    if not rng or not rng.group(1).strip().startswith("U+0000-00FF"):
        continue  # latin only
    fam = re.search(r"font-family:\s*'([^']+)'", block).group(1)
    wt = re.search(r"font-weight:\s*(\d+)", block).group(1)
    url = re.search(r"url\((https://[^)]+)\)", block).group(1)

    variable = fam == "Big Shoulders Display"
    slug = (fam.lower().replace(" ", "-") + ("-var" if variable else "-" + wt) + ".woff2")
    if slug in seen:
        continue
    data = urllib.request.urlopen(url, timeout=30).read()
    open(os.path.join(fonts_dir, slug), "wb").write(data)
    seen[slug] = True
    print("  %-34s %6d bytes" % (slug, len(data)))

    faces.append("@font-face {\n  font-family: '%s';\n  font-style: normal;\n"
                 "  font-weight: %s;\n  font-display: swap;\n"
                 "  src: url('../fonts/%s') format('woff2');\n}"
                 % (fam, "600 900" if variable else wt, slug))

open(os.path.join(ROOT, "assets", "css", "fonts.css"), "w").write(
    "/* Self-hosted webfonts — Barlow and Big Shoulders Display.\n"
    "   Google Fonts originals, SIL Open Font License 1.1. Latin subset.\n"
    "   Refresh with: python3 tools/fetch-fonts.py */\n\n" + "\n\n".join(faces) + "\n")
print("wrote assets/css/fonts.css")
