import time
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

_CACHE = {"data": None, "ts": 0}
CACHE_TTL = 1800  # 30 minutes

INDUSTRY_INTEL = [
    {
        "slug": "ai_recruiter",
        "name": "AI Recruiter System",
        "product": "ai_recruiter",
        "queries": ["AI recruitment technology hiring", "AI talent acquisition HR"],
        "opportunity": "Companies announcing hiring drives or HR digitization are strong leads for AI Recruiter.",
        "pitch_when": "Pitch after hiring expansion or HR automation news in their sector.",
        "best_time": "Tue-Thu, 10:00 AM - 12:00 PM (recipient timezone)",
        "pitch_to": "HR Directors, Talent Acquisition, CHRO",
    },
    {
        "slug": "supply_chain",
        "name": "Supply Chain Forecasting",
        "product": "supply_chain",
        "queries": ["AI supply chain forecasting", "demand planning artificial intelligence"],
        "opportunity": "Inventory shortages, demand volatility, and logistics disruptions create urgency for AI forecasting.",
        "pitch_when": "Pitch when news mentions stockouts, overstock, or supply chain disruption.",
        "best_time": "Mon-Wed, 9:00 AM - 11:00 AM",
        "pitch_to": "Supply Chain Heads, Operations Directors, CFO",
    },
    {
        "slug": "poultry_farms",
        "name": "Poultry Farms",
        "product": "video_analytics",
        "queries": ["poultry farm technology AI", "livestock monitoring smart farming"],
        "opportunity": "Biosecurity and flock health news = perfect moment for video analytics pitch.",
        "pitch_when": "Pitch after avian health, farm automation, or food safety coverage.",
        "best_time": "Tue-Thu, 8:00 AM - 10:00 AM",
        "pitch_to": "Farm Owners, Operations Managers, Agri-tech leads",
    },
    {
        "slug": "sports_organizations",
        "name": "Sports Organizations",
        "product": "video_analytics",
        "queries": ["sports analytics AI video", "cricket football performance analysis AI"],
        "opportunity": "Teams investing in performance tech after tournament seasons are ideal prospects.",
        "pitch_when": "Pitch before/after league seasons and major tournament cycles.",
        "best_time": "Mon-Fri, 11:00 AM - 1:00 PM",
        "pitch_to": "Coaches, Performance Analysts, Club Directors",
    },
    {
        "slug": "fitness_gyms",
        "name": "Fitness & Gyms",
        "product": "video_analytics",
        "queries": ["gym fitness technology AI", "health club smart operations"],
        "opportunity": "Gyms expanding locations or focusing on member experience need ops intelligence.",
        "pitch_when": "Pitch when fitness chains announce expansion or digital transformation.",
        "best_time": "Tue-Thu, 10:00 AM - 12:00 PM",
        "pitch_to": "Gym Owners, Franchise Managers, Operations Leads",
    },
    {
        "slug": "manufacturing",
        "name": "Manufacturing",
        "product": "video_analytics",
        "queries": ["manufacturing AI computer vision", "factory automation quality control AI"],
        "opportunity": "Quality defects and safety incidents in news highlight need for real-time monitoring.",
        "pitch_when": "Pitch after safety compliance or production efficiency headlines.",
        "best_time": "Mon-Wed, 9:00 AM - 11:00 AM",
        "pitch_to": "Plant Managers, Quality Heads, EHS Directors",
    },
    {
        "slug": "smart_cities",
        "name": "Smart Cities",
        "product": "video_analytics",
        "queries": ["smart city AI surveillance traffic", "urban AI video analytics"],
        "opportunity": "Municipal smart city tenders and traffic management projects are high-intent opportunities.",
        "pitch_when": "Pitch when cities announce surveillance, traffic AI, or public safety budgets.",
        "best_time": "Mon-Thu, 10:00 AM - 12:00 PM",
        "pitch_to": "City Officials, Traffic Police, Smart City PMs",
    },
    {
        "slug": "retail_stores",
        "name": "Retail Stores",
        "product": "video_analytics",
        "queries": ["retail AI footfall analytics", "store video analytics customer behavior"],
        "opportunity": "Retailers fighting shrinkage or optimizing layouts respond well to footfall analytics.",
        "pitch_when": "Pitch after retail earnings, loss prevention, or customer experience news.",
        "best_time": "Tue-Thu, 10:00 AM - 12:00 PM",
        "pitch_to": "Store Operations, Retail CEOs, Loss Prevention",
    },
    {
        "slug": "warehouses_logistics",
        "name": "Warehouses & Logistics",
        "product": "video_analytics",
        "queries": ["warehouse AI logistics automation", "supply chain warehouse technology"],
        "opportunity": "Warehouse bottlenecks and labor shortages drive demand for visual ops monitoring.",
        "pitch_when": "Pitch when logistics firms announce hub expansion or automation projects.",
        "best_time": "Mon-Wed, 9:00 AM - 11:00 AM",
        "pitch_to": "Warehouse Managers, Logistics Directors",
    },
    {
        "slug": "security_surveillance",
        "name": "Security & Surveillance",
        "product": "video_analytics",
        "queries": ["AI security surveillance analytics", "intelligent video monitoring"],
        "opportunity": "Security breaches and smart surveillance mandates open doors for AI analytics.",
        "pitch_when": "Pitch after security incidents or new compliance requirements.",
        "best_time": "Mon-Thu, 9:00 AM - 11:00 AM",
        "pitch_to": "Security Managers, Facility Heads, CISO",
    },
    {
        "slug": "healthcare_facilities",
        "name": "Healthcare Facilities",
        "product": "video_analytics",
        "queries": ["healthcare AI patient monitoring", "hospital AI safety technology"],
        "opportunity": "Patient safety and hospital efficiency news create openings for video AI solutions.",
        "pitch_when": "Pitch when hospitals announce digital health or safety upgrades.",
        "best_time": "Tue-Thu, 10:00 AM - 12:00 PM",
        "pitch_to": "Hospital Admins, Patient Safety Officers",
    },
    {
        "slug": "agriculture",
        "name": "Agriculture",
        "product": "video_analytics",
        "queries": ["agriculture AI crop monitoring", "smart farming computer vision"],
        "opportunity": "Crop disease and precision farming headlines signal readiness for field monitoring AI.",
        "pitch_when": "Pitch after agri-tech funding or climate impact on farming news.",
        "best_time": "Mon-Wed, 8:00 AM - 10:00 AM",
        "pitch_to": "Farm Operators, Agri-tech Managers",
    },
    {
        "slug": "education_training",
        "name": "Education & Training",
        "product": "video_analytics",
        "queries": ["education AI campus safety", "school smart surveillance technology"],
        "opportunity": "Campus safety and hybrid learning investments drive video analytics demand.",
        "pitch_when": "Pitch at start of academic terms and after campus safety incidents.",
        "best_time": "Tue-Thu, 10:00 AM - 12:00 PM",
        "pitch_to": "School Admins, Campus Security, Training Directors",
    },
    {
        "slug": "construction_sites",
        "name": "Construction Sites",
        "product": "video_analytics",
        "queries": ["construction site AI safety monitoring", "building site computer vision"],
        "opportunity": "Worksite accidents and compliance audits make safety monitoring a priority.",
        "pitch_when": "Pitch after construction safety regulation or major project announcements.",
        "best_time": "Mon-Wed, 9:00 AM - 11:00 AM",
        "pitch_to": "Site Managers, HSE Officers, Project Directors",
    },
    {
        "slug": "hotels_hospitality",
        "name": "Hotels & Hospitality",
        "product": "video_analytics",
        "queries": ["hotel hospitality AI guest experience", "resort smart operations technology"],
        "opportunity": "Hotels improving guest experience and security need intelligent monitoring.",
        "pitch_when": "Pitch before peak travel seasons and after hospitality expansion news.",
        "best_time": "Tue-Thu, 11:00 AM - 1:00 PM",
        "pitch_to": "Hotel GMs, Operations Managers, Security Heads",
    },
    {
        "slug": "airports_transport",
        "name": "Airports & Transport",
        "product": "video_analytics",
        "queries": ["airport AI passenger flow analytics", "transport hub smart surveillance"],
        "opportunity": "Passenger congestion and terminal upgrades create demand for flow analytics.",
        "pitch_when": "Pitch when airports announce expansion or passenger experience initiatives.",
        "best_time": "Mon-Thu, 9:00 AM - 11:00 AM",
        "pitch_to": "Airport Ops, Terminal Managers, Transport Authorities",
    },
]

MARKET_QUERIES = [
    "artificial intelligence business news",
    "AI startup enterprise adoption",
    "machine learning industry trends",
]


def _fetch_rss(query, limit=4):
    url = (
        "https://news.google.com/rss/search?q="
        + quote_plus(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )
    req = Request(url, headers={"User-Agent": "SprectexDashboard/1.0"})
    try:
        with urlopen(req, timeout=8) as resp:
            root = ET.fromstring(resp.read())
    except Exception:
        return []

    items = []
    for item in root.findall(".//item")[:limit]:
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "").strip()
        pub = item.findtext("pubDate", "").strip()
        if title and link:
            items.append({"title": title, "link": link, "published": pub, "query": query})
    return items


def _parse_date(pub):
    if not pub:
        return ""
    try:
        dt = datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %Z")
        return dt.strftime("%d %b %Y")
    except ValueError:
        return pub[:16]


def get_dashboard_intelligence(stats_rows=None):
    now = time.time()
    if _CACHE["data"] and now - _CACHE["ts"] < CACHE_TTL:
        return _CACHE["data"]

    all_news = []
    seen_titles = set()

    for q in MARKET_QUERIES:
        for item in _fetch_rss(q, limit=3):
            key = item["title"][:80].lower()
            if key in seen_titles:
                continue
            seen_titles.add(key)
            item["category"] = "AI Market"
            item["date"] = _parse_date(item["published"])
            all_news.append(item)

    industry_news = []
    for intel in INDUSTRY_INTEL[:8]:
        for item in _fetch_rss(intel["queries"][0], limit=2):
            key = item["title"][:80].lower()
            if key in seen_titles:
                continue
            seen_titles.add(key)
            item["category"] = intel["name"]
            item["industry_slug"] = intel["slug"]
            item["product"] = intel["product"]
            item["date"] = _parse_date(item["published"])
            industry_news.append(item)

    all_news.extend(industry_news)
    all_news = all_news[:18]

    suggestions = _build_suggestions(stats_rows or [])

    data = {
        "news": all_news,
        "suggestions": suggestions,
        "intel": INDUSTRY_INTEL,
        "updated": datetime.now().strftime("%I:%M %p"),
    }
    _CACHE["data"] = data
    _CACHE["ts"] = now
    return data


def _build_suggestions(stats_rows):
    suggestions = []

    pending_by_industry = {}
    for row in stats_rows:
        pending = row["pending"] or 0
        if pending > 0:
            pending_by_industry[row["industry_name"]] = {
                "pending": pending,
                "product": row["product_name"],
                "industry_slug": row["industry_slug"] if "industry_slug" in row.keys() else "",
            }

    if pending_by_industry:
        top = max(pending_by_industry.items(), key=lambda x: x[1]["pending"])
        suggestions.append({
            "priority": "high",
            "title": f"Send to {top[0]} first",
            "detail": f"You have {top[1]['pending']} pending contacts for {top[1]['product']}. Start individual sends today while news is fresh.",
            "action": "individual",
        })

    suggestions.append({
        "priority": "medium",
        "title": "AI Recruiter - Q2 hiring season",
        "detail": "Many companies ramp hiring in Q2. Pitch HR teams with your AI Recruiter proposal this week.",
        "action": "compose",
        "product": "ai_recruiter",
    })

    suggestions.append({
        "priority": "medium",
        "title": "Sports - pre-season window",
        "detail": "Sports clubs plan tech budgets before new seasons. Reach sports organizations with video analytics now.",
        "action": "individual",
        "product": "video_analytics",
        "industry": "sports_organizations",
    })

    suggestions.append({
        "priority": "low",
        "title": "Supply Chain - budget planning",
        "detail": "Ops leaders plan next quarter forecasts in June. Supply chain forecasting emails work best early in the week.",
        "action": "batch",
        "product": "supply_chain",
    })

    suggestions.append({
        "priority": "low",
        "title": "Use Direct Email for hot leads",
        "detail": "When you spot a strong news article, use Direct Email within 24 hours for maximum relevance.",
        "action": "compose",
    })

    return suggestions[:5]
