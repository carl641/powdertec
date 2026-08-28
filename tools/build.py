#!/usr/bin/env python3
"""
Builds the static PowderTec site.

Every page shares one header, footer and <head> block, so run this after
editing anything global:

    python3 tools/build.py

Output is plain static HTML committed to the repo — the site itself needs no
build step to deploy.
"""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SITE    = "https://www.alabamapowdercoating.com"
BRAND   = "PowderTec Powder Coating, Inc."
PHONE   = "(256) 287-3031"
TEL     = "+12562873031"
EMAIL   = "info@alabamapowdercoating.com"
STREET  = "2700 Alabama Highway 69 South"
CITY    = "Cullman"
STATE   = "AL"
ZIP     = "35057"

NAV = [
    ("Home",             "",                 "index.html"),
    ("Services",         "services/",        "services/index.html"),
    ("Locations Served", "locations-served/", "locations-served/index.html"),
    ("Contact",          "contact/",         "contact/index.html"),
]

AREAS = ["Cullman", "Morgan", "Madison", "Limestone", "Jefferson", "Shoals", "Guntersville Lakes"]


# --------------------------------------------------------------------------
# icons
# --------------------------------------------------------------------------
def icon(name, cls="card__icon"):
    paths = {
        # oven / large-format capacity
        "oven": '<rect x="2.6" y="4" width="18.8" height="16" rx="1.2"/><path d="M2.6 9.2h18.8"/>'
                '<circle cx="6" cy="6.6" r=".95"/>'
                '<path d="M9.6 13.4c0 1.9 1.4 2.4 1.4 3.9M13.4 12.4c0 2.4 1.9 2.9 1.9 4.9"/>',
        # AWS certified
        "shield": '<path d="M12 2.4l8.2 3v6.1c0 5.1-3.5 8.8-8.2 10.1-4.7-1.3-8.2-5-8.2-10.1V5.4z"/>'
                  '<path d="M8.5 11.9l2.5 2.5 4.5-4.7"/>',
        # precision application
        "target": '<circle cx="12" cy="12" r="8.6"/><circle cx="12" cy="12" r="4.1"/>'
                  '<path d="M12 1.4v3.2M12 19.4v3.2M1.4 12h3.2M19.4 12h3.2"/>',
        # CAD / drafting compass
        "compass": '<circle cx="12" cy="4.2" r="1.9"/><path d="M12 6.1v2.2"/>'
                   '<path d="M12.9 8.6L17.8 20.6M11.1 8.6L6.2 20.6"/><path d="M9.3 15.4h5.4"/>',
        # automotive
        "wheel": '<circle cx="12" cy="12" r="8.8"/><circle cx="12" cy="12" r="3.1"/>'
                 '<path d="M12 3.2v5.7M12 15.1v5.7M3.2 12h5.7M15.1 12h5.7"/>',
        # marine
        "anchor": '<circle cx="12" cy="4.6" r="2.2"/><path d="M12 6.8V21"/><path d="M8.2 10.6h7.6"/>'
                  '<path d="M4.4 13.8v1.4a7.6 7.6 0 0 0 15.2 0v-1.4"/>',
        # industrial
        "gear": '<circle cx="12" cy="12" r="3.3"/>'
                '<path d="M12 1.8v3M12 19.2v3M22.2 12h-3M4.8 12h-3'
                'M19.2 4.8l-2.1 2.1M6.9 17.1l-2.1 2.1M19.2 19.2l-2.1-2.1M6.9 6.9L4.8 4.8"/>',
        # location
        "pin": '<path d="M12 21.4s7-5.8 7-11.4a7 7 0 1 0-14 0c0 5.6 7 11.4 7 11.4z"/>'
               '<circle cx="12" cy="10" r="2.7"/>',
    }
    return ('<svg class="%s" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true" focusable="false">%s</svg>' % (cls, paths[name]))


PHONE_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
              '<path d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.4 11.4 0 0 0 3.6.58 '
              '1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1 11.4 11.4 '
              '0 0 0 .57 3.6 1 1 0 0 1-.25 1z"/></svg>')

ARROW = ('<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" '
         'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" '
         'focusable="false"><path d="M2.5 8h11M9 3.5L13.5 8 9 12.5"/></svg>')


# --------------------------------------------------------------------------
# service-radius diagram — plotted from real coordinates, Cullman at centre
# --------------------------------------------------------------------------
#   scale: 75 miles = 250px.  y inverted (north = up)
RADIUS_POINTS = [
    # x,   y,   name,                 towns,                              placement
    (275, 156, "Limestone County",   "Athens",                            "above"),
    (349, 172, "Madison County",     "Huntsville",                        "right"),
    (273, 201, "Morgan County",      "Decatur",                           "left"),
    (142, 156, "The Shoals",         "Florence &#183; Muscle Shoals",     "left"),
    (404, 258, "Guntersville Lakes", "Lake Guntersville",                 "right"),
    (306, 450, "Jefferson County",   "Birmingham",                        "below"),
]


def radius_svg():
    out = ['<svg class="radius" viewBox="-72 0 682 600" aria-hidden="true" focusable="false">']

    # distance rings
    for r, mi in ((83, "25"), (167, "50"), (250, "75")):
        cls = "ring ring--lit" if r == 250 else "ring"
        out.append('<circle class="%s" cx="300" cy="300" r="%d"/>' % (cls, r))
        out.append('<text class="sub mi" x="%d" y="294">%s MI</text>' % (300 + r + 9, mi))

    # cross-hairs
    out.append('<path class="axis" d="M300 44V556M44 300H556"/>')

    # spokes
    for x, y, _, _, _ in RADIUS_POINTS:
        out.append('<line class="spoke" x1="300" y1="300" x2="%d" y2="%d"/>' % (x, y))

    # hub
    out.append('<circle class="halo pulse" cx="300" cy="300" r="14"/>')
    out.append('<circle class="halo" cx="300" cy="300" r="20"/>')
    out.append('<circle class="dot dot--hub" cx="300" cy="300" r="8"/>')
    out.append('<text class="lbl--hub" x="300" y="345" text-anchor="middle">Cullman</text>')
    out.append('<text class="sub" x="300" y="364" text-anchor="middle">Our facility</text>')

    for x, y, name, towns, where in RADIUS_POINTS:
        if where == "right":
            tx, ty, anchor = x + 16, y + 1, "start"
        elif where == "left":
            tx, ty, anchor = x - 16, y + 1, "end"
        elif where == "above":
            tx, ty, anchor = x, y - 26, "middle"
        else:
            tx, ty, anchor = x, y + 32, "middle"
        out.append('<g class="g">')
        out.append('<circle class="dot" cx="%d" cy="%d" r="6"/>' % (x, y))
        out.append('<text class="lbl" x="%d" y="%d" text-anchor="%s">%s</text>' % (tx, ty, anchor, name))
        out.append('<text class="sub" x="%d" y="%d" text-anchor="%s">%s</text>' % (tx, ty + 17, anchor, towns))
        out.append('</g>')

    out.append('</svg>')
    return "".join(out)


# --------------------------------------------------------------------------
# shared chrome
# --------------------------------------------------------------------------
def brand(rel):
    return (
        '<a class="brand" href="%(rel)s" aria-label="%(brand)s — home">'
        '<svg class="brand__bolt" viewBox="0 0 50 70" aria-hidden="true" focusable="false">'
        '<path d="M31 0 L3 42 L21 42 L12 70 L47 30 L27 30 Z"/></svg>'
        '<span class="brand__word">Powder<em>Tec</em></span></a>'
    ) % {"rel": rel or "./", "brand": BRAND}


def head(rel, title, desc, page_path, extra_ld=""):
    ld = """{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "@id": "%(site)s/#business",
  "name": "%(brand)s",
  "alternateName": "PowderTec",
  "description": "Powder coating, pretreatment, welding and fabrication for automotive, marine and industrial clients across North Alabama.",
  "url": "%(site)s/",
  "telephone": "%(tel)s",
  "email": "%(email)s",
  "image": "%(site)s/images/rims.jpg",
  "priceRange": "$$",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "%(street)s",
    "addressLocality": "%(city)s",
    "addressRegion": "%(state)s",
    "postalCode": "%(zip)s",
    "addressCountry": "US"
  },
  "areaServed": [%(areas)s]
}""" % {
        "site": SITE, "brand": BRAND, "tel": TEL, "email": EMAIL,
        "street": STREET, "city": CITY, "state": STATE, "zip": ZIP,
        "areas": ", ".join('{"@type": "AdministrativeArea", "name": "%s"}' % a for a in
                           ["Cullman County, Alabama", "Morgan County, Alabama",
                            "Madison County, Alabama", "Limestone County, Alabama",
                            "Jefferson County, Alabama", "Lauderdale County, Alabama",
                            "Colbert County, Alabama", "Marshall County, Alabama"]),
    }

    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<link rel="canonical" href="%(site)s/%(path)s">
<meta name="theme-color" content="#0A0A0A">

<meta property="og:type" content="website">
<meta property="og:site_name" content="%(brand)s">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(site)s/%(path)s">
<meta property="og:image" content="%(site)s/images/rims.jpg">
<meta name="twitter:card" content="summary_large_image">

<link rel="icon" href="%(rel)sfavicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="%(rel)sfavicon.svg">

<link rel="preload" href="%(rel)sassets/fonts/big-shoulders-display-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="%(rel)sassets/fonts/barlow-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="%(rel)sassets/css/fonts.css">
<link rel="stylesheet" href="%(rel)sassets/css/styles.css">

<script>document.documentElement.className += ' js';</script>
<script type="application/ld+json">%(ld)s</script>
%(extra)s</head>
<body>
<a class="skip" href="#main">Skip to content</a>
""" % {
        "title": title, "desc": desc, "site": SITE, "path": page_path,
        "rel": rel, "brand": BRAND, "ld": ld, "extra": extra_ld,
    }


def header(rel, current):
    links = "".join(
        '<a href="%s%s"%s>%s</a>' % (rel, href, ' aria-current="page"' if label == current else "", label)
        for label, href, _ in NAV
    )
    return """<header class="hdr" id="hdr">
<div class="hdr__inner wrap wrap--wide">
%(brand)s
<nav class="nav" id="nav" aria-label="Main">
%(links)s
<div class="nav__foot">
<a class="tel" href="tel:%(tel)s">%(pi)s%(phone)s</a>
<a class="btn btn--sm" href="%(rel)scontact/">Get a Quote</a>
</div>
</nav>
<div class="hdr__cta">
<a class="tel" href="tel:%(tel)s">%(pi)s%(phone)s</a>
<a class="btn btn--sm" href="%(rel)scontact/">Get a Quote</a>
</div>
<button class="burger" type="button" aria-expanded="false" aria-controls="nav">
<span></span><span class="sr">Menu</span>
</button>
</div>
</header>
<main id="main">
""" % {"brand": brand(rel), "links": links, "tel": TEL, "phone": PHONE, "pi": PHONE_ICON, "rel": rel}


def band(heading, btn_label, btn_href, rel):
    return """<section class="band">
<div class="band__inner wrap">
<h2 class="display display--2">%(h)s</h2>
<div class="band__side">
<a class="btn btn--dark" href="%(rel)s%(href)s">%(b)s %(arrow)s</a>
<a class="band__tel" href="tel:%(tel)s">%(phone)s</a>
</div>
</div>
</section>
""" % {"h": heading, "b": btn_label, "href": btn_href, "rel": rel,
       "tel": TEL, "phone": PHONE, "arrow": ARROW}


def footer(rel):
    links = "".join('<li><a href="%s%s">%s</a></li>' % (rel, href, label) for label, href, _ in NAV)
    services = "".join('<li><a href="%sservices/#%s">%s</a></li>' % (rel, slug, label) for label, slug in [
        ("Powder Coating", "capabilities"),
        ("Pretreat &amp; Preparation", "capabilities"),
        ("Renewal &amp; Fabrication", "capabilities"),
        ("Automotive Finishing", "automotive"),
        ("Marine Finishing", "marine"),
        ("Industrial Finishing", "industrial"),
    ])
    return """</main>
<div class="hazard" role="presentation"></div>
<footer class="foot">
<div class="wrap wrap--wide">
<div class="foot__grid">

<div class="foot__brand">
%(brand)s
<address>
%(street)s<br>%(city)s, %(state)s %(zip)s<br><br>
<a href="tel:%(tel)s" class="foot__tel">%(phone)s</a>
<a href="mailto:%(email)s">%(email)s</a>
</address>
</div>

<div>
<h3>Site</h3>
<ul class="foot__links">%(links)s</ul>
</div>

<div>
<h3>Services</h3>
<ul class="foot__links">%(services)s</ul>
</div>

<div>
<h3>Service Area</h3>
<p class="foot__areas">
Cullman County &#183; Morgan County &#183; Madison County &#183; Limestone County &#183;
Jefferson County &#183; The Shoals &#183; Guntersville Lakes &#8212; North Alabama
</p>
<a class="tlink" href="%(rel)slocations-served/" style="margin-top:16px">Full Service Area %(arrow)s</a>
</div>

</div>
<div class="foot__bar">
<p>&copy; <span data-year>2026</span> %(brandname)s. All rights reserved.</p>
<p>Powder coating &#183; Pretreatment &#183; Welding &amp; fabrication &#183; Cullman, Alabama</p>
</div>
</div>
</footer>
<div class="dock">
<div class="dock__row">
<a class="dock__call" href="tel:%(tel)s">%(pi)s Call Us</a>
<a class="dock__quote" href="%(rel)scontact/">Get a Quote</a>
</div>
</div>
<script src="%(rel)sassets/js/site.js" defer></script>
</body>
</html>
""" % {"brand": brand(rel), "street": STREET, "city": CITY, "state": STATE, "zip": ZIP,
       "tel": TEL, "phone": PHONE, "email": EMAIL, "links": links, "services": services,
       "rel": rel, "brandname": BRAND, "arrow": ARROW, "pi": PHONE_ICON}


def crumb(rel, label):
    return ('<nav class="crumb" aria-label="Breadcrumb">'
            '<a href="%s">Home</a><span aria-hidden="true">/</span><span>%s</span></nav>' % (rel or "./", label))


def breadcrumb_ld(label, path):
    return ('<script type="application/ld+json">{"@context":"https://schema.org",'
            '"@type":"BreadcrumbList","itemListElement":['
            '{"@type":"ListItem","position":1,"name":"Home","item":"%s/"},'
            '{"@type":"ListItem","position":2,"name":"%s","item":"%s/%s"}]}</script>\n'
            % (SITE, label, SITE, path))


def write(path, html):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    # collapse the blank lines the templates leave behind
    html = re.sub(r"\n{3,}", "\n\n", html)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("  wrote %-34s %6d bytes" % (path, len(html.encode("utf-8"))))


# ==========================================================================
# PAGE 1 — Home
# ==========================================================================
def build_home():
    rel = ""
    html = head(
        rel,
        "Powder Coating in Cullman, AL | Automotive, Marine &amp; Industrial",
        "North Alabama's premier powder coating facility &#8212; Alabama's largest oven, "
        "AWS-certified welders and Gema equipment. Automotive, marine and industrial finishing.",
        "",
    )
    html += header(rel, "Home")

    html += f"""
<!-- ============ HERO ============ -->
<section class="hero">
<div class="hero__media">
<img src="images/bn.jpg" alt="A powder-coated tube chassis in high-visibility green moving through the PowderTec line in Cullman, Alabama" fetchpriority="high" width="1536" height="2048">
</div>
<div class="hero__inner wrap wrap--wide">
<p class="eyebrow">Powder coating &amp; metal finishing &#183; Cullman, Alabama</p>
<h1 class="display display--hero">North Alabama&#8217;s Premier <em>Powder Coating Team</em></h1>
<p class="lower hero__sub">serving automotive, marine, and industrial clients across north alabama.</p>
<div class="hero__acts">
<a class="btn" href="contact/">Get a Quote {ARROW}</a>
<a class="btn btn--ghost" href="services/">View Services</a>
</div>
<p class="hero__tel"><span>Talk to a coater</span> <a href="tel:{TEL}">{PHONE}</a></p>
</div>
</section>

<!-- ============ CREDIBILITY STRIP ============ -->
<section class="creds" aria-label="Facility credentials">
<div class="wrap wrap--wide">
<div class="creds__grid">
<div class="cred">{icon('oven', 'x')}<p>Alabama&#8217;s Largest Oven<small>Large-format capacity for the parts most shops have to turn away.</small></p></div>
<div class="cred">{icon('shield', 'x')}<p>AWS Certified Welders<small>Certified welding and fabrication handled in-house, not subbed out.</small></p></div>
<div class="cred">{icon('target', 'x')}<p>Gema Application Systems<small>Even film build, repeatable colour and clean powder transfer.</small></p></div>
<div class="cred">{icon('compass', 'x')}<p>In-House CAD Design<small>Designed, fixtured, fabricated and finished under one roof.</small></p></div>
</div>
</div>
</section>

<!-- ============ INTRO ============ -->
<section class="section">
<div class="wrap wrap--wide">
<div class="split">
<div class="split__media" data-reveal>
<img src="images/metalwork.jpg" alt="Ornamental steel railing sections in a deep gloss black powder coat, staged on the shop floor" loading="lazy" width="960" height="540">
</div>
<div data-reveal style="--d:120ms">
<p class="eyebrow">Who we are</p>
<h2 class="lower">built for the toughest jobs in north&nbsp;alabama.</h2>
<div class="prose" style="margin-top:26px">
<p>PowderTec is a powder coating and metal finishing operation in Cullman, Alabama, built on a simple idea: <strong>finishing should be an asset to your operation, not a bottleneck in it.</strong> We run one of the most advanced facilities in the state &#8212; including the largest powder coating oven in Alabama &#8212; so the parts other shops have to turn away come here instead.</p>
<p>Every job moves through the same disciplined sequence: thorough pretreatment, precise electrostatic application on Gema equipment, and a controlled cure. Where a part needs more than a finish, our AWS-certified welders and fabricators repair, modify or build it from CAD before it ever reaches the booth.</p>
<p>The result is a finish that holds up &#8212; on a race chassis, on a trailer that lives in the water, on a fence line that has to still look right in twenty years.</p>
</div>
<a class="tlink" href="services/" style="margin-top:30px">See What We Do {ARROW}</a>
</div>
</div>
</div>
</section>

<!-- ============ THREE VERTICALS ============ -->
<section class="section section--panel section--edge" id="industries">
<div class="wrap wrap--wide">
<div class="head">
<p class="eyebrow">Who we serve</p>
<h2 class="lower">three industries. one standard of excellence.</h2>
</div>
<div class="grid grid--3" data-stagger>

<article class="card vcard" data-reveal>
<div class="vcard__img"><img src="images/rims.jpg" alt="A steel beadlock wheel finished in gloss black with a burnt-orange beadlock ring" loading="lazy" width="960" height="540"></div>
<div class="vcard__body">
{icon('wheel')}
<h3>Automotive</h3>
<p>After-market parts, chassis, wheels and restoration work finished to shrug off heat, road salt and stone chip &#8212; matched to just about any colour you can name.</p>
<a class="tlink" href="services/#automotive">Explore Services {ARROW}</a>
</div>
</article>

<article class="card vcard" data-reveal>
<div class="vcard__img"><img src="images/wetsteps.jpg" alt="Boat boarding steps and handrails powder coated in blue, red and black, ready for delivery" loading="lazy" width="2048" height="1536"></div>
<div class="vcard__body">
{icon('anchor')}
<h3>Marine</h3>
<p>Corrosion-resistant, water-tough finishes for boat hardware, trailers, boarding steps, rails and dock fixtures built for a life spent wet.</p>
<a class="tlink" href="services/#marine">Explore Services {ARROW}</a>
</div>
</article>

<article class="card vcard" data-reveal>
<div class="vcard__img"><img src="images/metalwork.jpg" alt="Powder-coated architectural steel scrollwork and framing with a uniform gloss black finish" loading="lazy" width="960" height="540"></div>
<div class="vcard__body">
{icon('gear')}
<h3>Industrial</h3>
<p>Heavy-duty coating for fencing, architectural metal, appliance housings, retail fixtures, extrusions and fabricated steel &#8212; at production volume.</p>
<a class="tlink" href="services/#industrial">Explore Services {ARROW}</a>
</div>
</article>

</div>
</div>
</section>

<!-- ============ PROCESS ============ -->
<section class="section">
<div class="wrap wrap--wide">
<div class="head">
<p class="eyebrow">How the work moves</p>
<h2 class="lower">three steps. no shortcuts.</h2>
</div>
<div class="steps" data-stagger>
<div class="step" data-reveal>
<p class="step__num">01</p>
<h3>Pretreat &amp; Prep</h3>
<p>Cleaning, media blasting and chemical pretreatment that strip contamination and give the powder something real to bond to. Skip this step and nothing after it matters.</p>
</div>
<div class="step" data-reveal>
<p class="step__num">02</p>
<h3>Powder Coat</h3>
<p>Electrostatic application on Gema equipment, then a controlled cure in the largest powder coating oven in Alabama &#8212; so big parts cure evenly instead of in sections.</p>
</div>
<div class="step" data-reveal>
<p class="step__num">03</p>
<h3>Renewal &amp; Fabrication</h3>
<p>AWS-certified welding, CAD-driven fabrication and the repair of worn or damaged parts &#8212; before or after the finish, whichever the job actually calls for.</p>
</div>
</div>
</div>
</section>

<!-- ============ SERVICE AREA TEASER ============ -->
<section class="section section--panel section--edge">
<div class="wrap wrap--wide">
<div class="split split--rev">
<div class="split__media" data-reveal style="background:#0A0A0A;padding:clamp(12px,2vw,28px)">
{radius_svg()}
</div>
<div data-reveal style="--d:120ms">
<p class="eyebrow">Where we work</p>
<h2 class="lower">proudly serving north alabama.</h2>
<div class="prose" style="margin-top:26px">
<p>From our facility on Alabama Highway 69 South in Cullman, we sit inside an easy haul of nearly every industrial corridor, automotive shop and lake community in the northern half of the state &#8212; Huntsville and Decatur to the north, Birmingham to the south, the Shoals to the west, Lake Guntersville to the east.</p>
<p>That central position matters more than it sounds. Shorter hauls mean less handling on large or heavy parts, quicker turnaround and a shop you can actually drive to when a job needs a conversation.</p>
</div>
<ul class="tags" style="margin-top:28px">
{"".join(f'<li><a class="tag" href="locations-served/">{a}</a></li>' for a in AREAS)}
</ul>
<a class="tlink" href="locations-served/" style="margin-top:30px">See Full Service Area {ARROW}</a>
</div>
</div>
</div>
</section>
"""

    html += band("Ready to get your project coated right?", "Request a Quote", "contact/", rel)
    html += footer(rel)
    write("index.html", html)


# ==========================================================================
# PAGE 2 — Services
# ==========================================================================
def build_services():
    rel = "../"
    path = "services/"
    html = head(
        rel,
        "Powder Coating Services | Automotive, Marine &amp; Industrial",
        "Powder coating, pretreatment, AWS-certified welding and CAD fabrication for automotive, "
        "marine and industrial parts. Based in Cullman, Alabama.",
        path,
        breadcrumb_ld("Services", path),
    )
    html += header(rel, "Services")

    html += f"""
<!-- ============ PAGE HERO ============ -->
<section class="phero">
<div class="phero__media">
<img src="../images/rims.jpg" alt="A freshly powder-coated beadlock wheel resting in the PowderTec shop" width="960" height="540">
</div>
<div class="wrap wrap--wide">
{crumb(rel, "Services")}
<h1 class="display display--1">Services</h1>
<p class="lede phero__sub">Precision powder coating and finishing for automotive, marine and industrial applications &#8212; from a single restoration part to a full production run.</p>
</div>
</section>

<!-- ============ CORE CAPABILITIES ============ -->
<section class="section" id="capabilities">
<div class="wrap wrap--wide">
<div class="head">
<p class="eyebrow">Core capabilities</p>
<h2 class="lower">everything the part needs, in one building.</h2>
</div>
<div class="grid grid--3" data-stagger>

<article class="card" data-reveal>
{icon('oven')}
<h3>Powder Coating</h3>
<p>Durable, long-lasting, custom colour-matched finishes applied with state-of-the-art Gema equipment. The largest powder coating oven in Alabama means large-format work cures in one piece rather than being sectioned, rehung and re-run &#8212; which is where inconsistency creeps in on big parts.</p>
</article>

<article class="card" data-reveal>
{icon('target')}
<h3>Pretreat &amp; Preparation</h3>
<p>A finish is only as good as what sits underneath it. We clean, media blast and chemically pretreat every part to strip oil, oxide, mill scale and old coating, then key the surface for maximum adhesion and long-term corrosion resistance.</p>
</article>

<article class="card" data-reveal>
{icon('compass')}
<h3>Renewal &amp; Fabrication</h3>
<p>AWS-certified welders and fabricators with in-house CAD design. We repair cracked, bent or corroded parts, modify assemblies, and build components from drawings &#8212; so a worn part can leave here renewed rather than replaced.</p>
</article>

</div>
</div>
</section>

<!-- ============ INDUSTRIES ============ -->
<section class="section section--panel section--edge" id="automotive">
<div class="wrap wrap--wide">
<div class="split">
<div class="split__media" data-reveal>
<img src="../images/rims.jpg" alt="Gloss black steel wheel with an orange beadlock ring, powder coated by PowderTec" loading="lazy" width="960" height="540">
</div>
<div data-reveal style="--d:120ms">
<p class="eyebrow">Automotive</p>
<h2 class="lower">automotive finishing that goes the distance.</h2>
<div class="prose" style="margin-top:24px">
<p>Road salt, brake heat, stone chip and UV will find every weak spot in a finish. Automotive work gets pretreatment matched to the substrate and a coating system chosen for the service conditions the part will actually see &#8212; not just the colour on the sample chip.</p>
<p>We colour-match to your specification, handle multi-stage finishes, and coat everything from a single restoration bracket to a complete chassis. Bare steel, cast aluminium and non-ferrous castings are all routine here.</p>
</div>
<ul class="ticks">
<li>Wheels &amp; rims, including beadlock and multi-piece assemblies</li>
<li>Frames, chassis, roll cages and suspension components</li>
<li>Brake calipers, brackets and engine-bay hardware</li>
<li>Trim, bumpers and after-market accessories</li>
<li>Classic and restoration parts stripped back to bare metal</li>
</ul>
<a class="tlink" href="../contact/" style="margin-top:30px">Quote an Automotive Job {ARROW}</a>
</div>
</div>
</div>
</section>

<section class="section" id="marine">
<div class="wrap wrap--wide">
<div class="split split--rev">
<div class="split__media" data-reveal>
<img src="../images/wetsteps.jpg" alt="Marine boarding steps and handrails finished in blue, red and black powder coat" loading="lazy" width="2048" height="1536">
</div>
<div data-reveal style="--d:120ms">
<p class="eyebrow">Marine</p>
<h2 class="lower">built to withstand the water.</h2>
<div class="prose" style="margin-top:24px">
<p>Marine hardware lives in the worst environment we coat for: constant moisture, trailer immersion, dissimilar metals bolted together and, on the coast, salt. Pretreatment and coating selection do the heavy lifting long before anyone notices the colour.</p>
<p>With Lake Guntersville, Smith Lake and the Tennessee River on our doorstep, marine work is a regular part of the schedule &#8212; from one-off repairs for a boat owner to production runs of boarding steps, rails and trailer components for builders and dealers.</p>
</div>
<ul class="ticks">
<li>Boat trailers, frames, bunks and trailer components</li>
<li>Boarding steps, ladders, rails and grab handles</li>
<li>Cleats, fittings and deck hardware</li>
<li>Dock hardware, gangways and lift components</li>
<li>Custom marine fabrication and repair work</li>
</ul>
<a class="tlink" href="../contact/" style="margin-top:30px">Quote a Marine Job {ARROW}</a>
</div>
</div>
</div>
</section>

<section class="section section--panel section--edge" id="industrial">
<div class="wrap wrap--wide">
<div class="split">
<div class="split__media" data-reveal>
<img src="../images/metalwork.jpg" alt="Architectural steel scrollwork and framing finished in uniform gloss black" loading="lazy" width="960" height="540">
</div>
<div data-reveal style="--d:120ms">
<p class="eyebrow">Industrial</p>
<h2 class="lower">heavy-duty coating for demanding environments.</h2>
<div class="prose" style="margin-top:24px">
<p>Industrial finishing is a volume and consistency problem as much as a coating one. Batch after batch has to come out the same, hit the schedule, and arrive packed so it does not need rework on the receiving dock.</p>
<p>We coat for fabricators, extruders, manufacturers, fencing contractors and architectural shops throughout North Alabama, and we are set up for the oversized work &#8212; long sections, tall frames and heavy weldments &#8212; that smaller ovens cannot take.</p>
</div>
<ul class="ticks">
<li>Fencing, gates, handrail and guardrail</li>
<li>Architectural panels, louvres and structural trim</li>
<li>Appliance housings and enclosures</li>
<li>Retail displays, racks and store fixtures</li>
<li>Sheet metal fabrication and aluminium extrusions</li>
<li>Non-ferrous castings and machined components</li>
</ul>
<a class="tlink" href="../contact/" style="margin-top:30px">Quote an Industrial Job {ARROW}</a>
</div>
</div>
</div>
</section>

<!-- ============ EQUIPMENT ============ -->
<section class="section">
<div class="wrap wrap--wide">
<div class="split" style="align-items:start">
<div data-reveal>
<p class="eyebrow">Equipment &amp; facility</p>
<h2 class="lower">scale is a quality decision.</h2>
<div class="prose" style="margin-top:24px">
<p>Oven size is not bragging rights &#8212; it is the difference between a part that cures in one continuous pass and one that gets sectioned, rehung and re-run. Alabama&#8217;s largest powder coating oven lets us take long, tall and heavy work in a single load, which keeps film build and gloss consistent from one end of a part to the other.</p>
<p>Pair that with Gema application systems, certified welders and in-house CAD, and most jobs never have to leave the building. Fewer hand-offs means fewer things to schedule around, and a shorter, more predictable turnaround for you.</p>
</div>
</div>
<div data-reveal style="--d:120ms">
<div class="specs">
<div class="spec"><p class="spec__k">Capacity</p><p class="spec__v">Largest Powder Coating Oven in Alabama</p></div>
<div class="spec"><p class="spec__k">Application</p><p class="spec__v">Gema Powder Coating Equipment</p></div>
<div class="spec"><p class="spec__k">Fabrication</p><p class="spec__v">AWS Certified Welding Team</p></div>
<div class="spec"><p class="spec__k">Design</p><p class="spec__v">In-House CAD Capability</p></div>
</div>
</div>
</div>
</div>
</section>
"""

    html += band("Get a quote for your project.", "Contact Us", "contact/", rel)
    html += footer(rel)
    write("services/index.html", html)


# ==========================================================================
# PAGE 3 — Locations Served
# ==========================================================================
REGIONS = [
    ("Cullman County", "Cullman &#183; Hanceville &#183; Good Hope &#183; Baileyton",
     "Home base. Our facility sits on Alabama Highway 69 South, which means same-week scheduling "
     "and easy drop-off for local automotive shops, fabricators and boat owners."),
    ("Morgan County", "Decatur &#183; Hartselle &#183; Priceville &#183; Somerville",
     "A short run up Highway 31 to Decatur&#8217;s manufacturing corridor. We coat for Morgan County "
     "fabricators, plants and automotive shops, plus Wheeler Lake marine work."),
    ("Madison County", "Huntsville &#183; Madison &#183; New Hope &#183; Gurley",
     "Supporting Huntsville-area manufacturers, precision and aerospace-adjacent suppliers, custom "
     "car builders and trailer owners with finishes held to a tight spec."),
    ("Limestone County", "Athens &#183; Ardmore &#183; Elkmont &#183; Mooresville",
     "Reliable powder coating for Athens and Limestone County manufacturing, agricultural equipment, "
     "fencing contractors and automotive restoration work."),
    ("Jefferson County", "Birmingham &#183; Gardendale &#183; Bessemer &#183; Hoover",
     "Premium finishing for Birmingham-area industrial clients, fabrication shops and after-market "
     "automotive builders &#8212; straight down I-65 from Cullman."),
    ("The Shoals", "Florence &#183; Muscle Shoals &#183; Sheffield &#183; Tuscumbia",
     "Industrial and automotive coating across the Shoals, including sheet metal, extrusions and "
     "fabricated assemblies for the region&#8217;s manufacturers."),
    ("Guntersville Lakes", "Guntersville &#183; Arab &#183; Albertville &#183; Scottsboro",
     "Specialised marine hardware, boarding step and trailer coating for the Lake Guntersville "
     "boating community, marinas and dealers."),
]


def build_locations():
    rel = "../"
    path = "locations-served/"
    html = head(
        rel,
        "Powder Coating Cullman, Morgan, Madison &amp; North Alabama | PowderTec",
        "Powder coating throughout North Alabama &#8212; Cullman, Morgan, Madison, Limestone and "
        "Jefferson counties, the Shoals and the Guntersville Lakes region.",
        path,
        breadcrumb_ld("Locations Served", path),
    )
    html += header(rel, "Locations Served")

    cards = "".join(f"""
<article class="loc" data-reveal>
{icon('pin', 'loc__pin')}
<h3>{name}</h3>
<span class="loc__towns">{towns}</span>
<p>{copy}</p>
</article>""" for name, towns, copy in REGIONS)

    html += f"""
<!-- ============ PAGE HERO ============ -->
<section class="phero">
<div class="phero__media">
<img src="../images/metalwork.jpg" alt="Powder-coated steel sections staged at the PowderTec facility in Cullman, Alabama" width="960" height="540">
</div>
<div class="wrap wrap--wide">
{crumb(rel, "Locations Served")}
<h1 class="display display--1">Locations Served</h1>
<p class="lede phero__sub">Proudly providing powder coating and finishing services throughout North Alabama.</p>
</div>
</section>

<!-- ============ RADIUS DIAGRAM + INTRO ============ -->
<section class="section">
<div class="wrap wrap--wide">
<div class="split">
<div class="split__media" data-reveal style="background:#0A0A0A;padding:clamp(12px,2vw,28px)">
{radius_svg()}
</div>
<div data-reveal style="--d:120ms">
<p class="eyebrow">Service area</p>
<h2 class="lower">cullman is the middle of north alabama&#8217;s map.</h2>
<div class="prose" style="margin-top:26px">
<p>PowderTec operates from {STREET} in {CITY}, {STATE} &#8212; roughly forty miles from Decatur, Huntsville, Athens and Guntersville, and about the same again to Birmingham and the Shoals. Nearly every industrial corridor, automotive shop and lake community in the northern half of the state sits inside a comfortable haul.</p>
<p>We take automotive, marine and industrial work from across that footprint. Large or awkward loads are worth a phone call before you hitch up &#8212; we will tell you straight away whether it fits the oven and what a realistic turnaround looks like.</p>
</div>
<p style="margin-top:26px"><a class="btn" href="../contact/">Get a Quote {ARROW}</a></p>
</div>
</div>
</div>
</section>

<!-- ============ REGION GRID ============ -->
<section class="section section--panel section--edge">
<div class="wrap wrap--wide">
<div class="head">
<p class="eyebrow">Counties &amp; regions</p>
<h2 class="lower">where our work ends up.</h2>
</div>
<div class="grid grid--3" data-stagger>{cards}
</div>
</div>
</section>

<!-- ============ WHY LOCATION MATTERS ============ -->
<section class="section">
<div class="wrap wrap--wide">
<div class="head">
<p class="eyebrow">Why it matters</p>
<h2 class="lower">a shorter haul is a better finish.</h2>
</div>
<div class="grid grid--3" data-stagger>

<article class="card" data-reveal>
{icon('oven')}
<h3>Less Handling</h3>
<p>Large and heavy parts pick up damage every time they are loaded, strapped and moved. A shorter trip means fewer touches between your floor and ours &#8212; and fewer touch-ups on the way back.</p>
</article>

<article class="card" data-reveal>
{icon('target')}
<h3>Faster Turnaround</h3>
<p>Being central to North Alabama keeps transit out of your lead time. For most of the region a job can leave, be coated and come back without a multi-day freight window built into the schedule.</p>
</article>

<article class="card" data-reveal>
{icon('shield')}
<h3>Local Accountability</h3>
<p>We know the industries here &#8212; the plants, the fab shops, the lake communities, the car builders. When something needs a conversation rather than an email thread, you can drive over and have it.</p>
</article>

</div>
</div>
</section>
"""

    html += band("Don&#8217;t see your area listed? We may still be able to help.",
                 "Contact Us", "contact/", rel)
    html += footer(rel)
    write("locations-served/index.html", html)


# ==========================================================================
# PAGE 4 — Contact
# ==========================================================================
def build_contact():
    rel = "../"
    path = "contact/"
    html = head(
        rel,
        "Contact PowderTec | Powder Coating Quotes | Cullman, AL",
        "Contact PowderTec Powder Coating in Cullman, Alabama. Call (256) 287-3031 or send a "
        "quote request for your automotive, marine or industrial project.",
        path,
        breadcrumb_ld("Contact", path),
    )
    html += header(rel, "Contact")

    maps_q = "2700+Alabama+Highway+69+South,+Cullman,+AL+35057"

    html += f"""
<!-- ============ PAGE HERO ============ -->
<section class="phero">
<div class="phero__media">
<img src="../images/bn.jpg" alt="Parts hanging on the line inside the PowderTec facility" width="1536" height="2048">
</div>
<div class="wrap wrap--wide">
{crumb(rel, "Contact")}
<h1 class="display display--1">Contact PowderTec</h1>
<p class="lede phero__sub">Get a quote, or just ask us about your next automotive, marine or industrial project.</p>
</div>
</section>

<!-- ============ CONTACT ============ -->
<section class="section">
<div class="wrap wrap--wide">
<div class="contact-grid">

<div data-reveal>
<p class="eyebrow">Direct line</p>
<h2 class="lower" style="margin-bottom:34px">talk to someone who runs the line.</h2>

<dl class="info">
<dt>Phone</dt>
<dd><a class="info__tel" href="tel:{TEL}">{PHONE}</a></dd>

<dt>Email</dt>
<dd><a class="info__email" href="mailto:{EMAIL}">{EMAIL}</a></dd>

<dt>Facility</dt>
<dd><address>{BRAND}<br>{STREET}<br>{CITY}, {STATE} {ZIP}</address></dd>

<!-- TODO: confirm exact opening hours with the client and replace this line. -->
<dt>Hours</dt>
<dd>Monday &#8211; Friday. Please call ahead to arrange drop-off and collection times.</dd>
</dl>

<p class="prose" style="color:var(--fog)"><strong>For direct service during business hours, please call us.</strong> A two-minute conversation about size, substrate and finish usually gets you a firmer number than a form ever will.</p>

<div class="mapframe" style="margin-top:30px">
<iframe title="Map showing the PowderTec facility area in Cullman, Alabama" loading="lazy" referrerpolicy="no-referrer-when-downgrade"
src="https://www.openstreetmap.org/export/embed.html?bbox=-86.9400%2C34.0900%2C-86.7500%2C34.2300&amp;layer=mapnik"></iframe>
</div>
<p style="margin-top:18px"><a class="btn btn--ghost btn--sm" href="https://www.google.com/maps/dir/?api=1&amp;destination={maps_q}" target="_blank" rel="noopener">Get Directions {ARROW}</a></p>
</div>

<div data-reveal style="--d:120ms">
<form class="form" id="quote-form" novalidate>
<p class="eyebrow">Quote request</p>
<h2 class="display display--2" style="font-size:clamp(1.9rem,3.2vw,2.6rem);margin-bottom:28px">Tell us about the job</h2>

<p class="form__status"></p>

<div class="form__row">
<div class="field">
<label for="f-name">Name <span class="req" aria-hidden="true">*</span></label>
<input id="f-name" name="name" type="text" autocomplete="name" required placeholder="Jane Smith">
<p class="err" id="e-name"></p>
</div>
<div class="field">
<label for="f-company">Company</label>
<input id="f-company" name="company" type="text" autocomplete="organization" placeholder="Optional">
<p class="err"></p>
</div>
</div>

<div class="form__row">
<div class="field">
<label for="f-email">Email <span class="req" aria-hidden="true">*</span></label>
<input id="f-email" name="email" type="email" autocomplete="email" required placeholder="you@company.com">
<p class="err"></p>
</div>
<div class="field">
<label for="f-phone">Phone</label>
<input id="f-phone" name="phone" type="tel" autocomplete="tel" placeholder="(256) 000-0000">
<p class="err"></p>
</div>
</div>

<div class="field">
<label for="f-project">Project type <span class="req" aria-hidden="true">*</span></label>
<select id="f-project" name="project" required>
<option value="">Select one&#8230;</option>
<option>Automotive</option>
<option>Marine</option>
<option>Industrial</option>
<option>Other</option>
</select>
<p class="err"></p>
</div>

<div class="field">
<label for="f-message">Project details <span class="req" aria-hidden="true">*</span></label>
<textarea id="f-message" name="message" required placeholder="What is the part, roughly how big, what material, how many, and what finish are you after? Rough dimensions and quantity help us quote faster."></textarea>
<p class="err"></p>
</div>

<button class="btn btn--wide" type="submit">Send Message</button>
<p class="form__note">Fields marked <span class="yel">*</span> are required. Prefer to talk it through? Call <a class="yel" href="tel:{TEL}" style="text-decoration:none;font-weight:600">{PHONE}</a>.</p>
</form>
</div>

</div>
</div>
</section>

<!-- ============ SERVICE AREA REMINDER ============ -->
<section class="section--tight" style="border-top:1px solid var(--line-soft);background:var(--panel)">
<div class="wrap wrap--wide" style="text-align:center">
<p class="eyebrow eyebrow--center">Service area</p>
<p class="lower" style="max-width:34ch;margin-inline:auto">serving cullman, morgan, madison, limestone, jefferson, the shoals and the guntersville lakes region of north alabama.</p>
<ul class="tags" style="justify-content:center;margin-top:28px">
{"".join(f'<li><a class="tag" href="../locations-served/">{a}</a></li>' for a in AREAS)}
</ul>
</div>
</section>

<!-- ============ REASSURANCE ============ -->
<section class="creds" aria-label="Facility credentials">
<div class="wrap wrap--wide">
<div class="creds__grid creds__grid--3">
<div class="cred">{icon('oven', 'x')}<p>Alabama&#8217;s Largest Oven<small>Large-format capacity most shops have to turn away.</small></p></div>
<div class="cred">{icon('shield', 'x')}<p>AWS Certified Welders<small>Certified welding and fabrication handled in-house.</small></p></div>
<div class="cred">{icon('target', 'x')}<p>Gema Application Systems<small>Even film build and repeatable, matched colour.</small></p></div>
</div>
<p class="lede" style="text-align:center;padding-block:clamp(34px,4vw,52px);max-width:56ch;margin-inline:auto">Alabama&#8217;s most advanced powder coating facility &#8212; ready to exceed your expectations.</p>
</div>
</section>
"""

    html += footer(rel)
    write("contact/index.html", html)


# ==========================================================================
# robots / sitemap
# ==========================================================================
def build_meta():
    write("robots.txt", "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE)

    urls = [("", "1.0"), ("services/", "0.9"), ("locations-served/", "0.8"), ("contact/", "0.8")]
    body = "".join(
        '  <url>\n    <loc>%s/%s</loc>\n    <changefreq>monthly</changefreq>\n    <priority>%s</priority>\n  </url>\n'
        % (SITE, u, p) for u, p in urls
    )
    write("sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + '</urlset>\n')


def build_404():
    rel = ""
    html = head(rel, "Page Not Found | %s" % BRAND,
                "That page could not be found. Head back to the PowderTec home page or call (256) 287-3031.", "404.html")
    html += header(rel, "")
    html += f"""
<section class="section" style="padding-block:clamp(110px,16vh,190px)">
<div class="wrap wrap--wide">
<p class="eyebrow">Error 404</p>
<h1 class="display display--1">This page came off<br>the line</h1>
<p class="lede" style="margin-top:24px;max-width:46ch">The page you were after does not exist. Try one of these instead &#8212; or call us on <a class="yel" href="tel:{TEL}" style="text-decoration:none;font-weight:600">{PHONE}</a>.</p>
<div class="hero__acts" style="margin-top:36px">
<a class="btn" href="./">Home</a>
<a class="btn btn--ghost" href="services/">Services</a>
<a class="btn btn--ghost" href="contact/">Contact</a>
</div>
</div>
</section>
"""
    html += footer(rel)
    write("404.html", html)


if __name__ == "__main__":
    print("Building PowderTec site…")
    build_home()
    build_services()
    build_locations()
    build_contact()
    build_404()
    build_meta()
    print("Done.")
