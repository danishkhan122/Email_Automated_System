from config import PROPOSALS_DIR

# Actual proposal PDFs uploaded by admin
PROPOSAL_MAP = {
    "ai_recruiter": "Business Proposal AI Recruiter System By Sprectex AI.pdf",
    "supply_chain": "AI Forecasting Solution For Industries By Sprectex AI.pdf",
    "poultry_farms": "Business Proposal For Chicken Video Analytics Solution By Sprectex AI.pdf",
    "sports_organizations": "Business Proposal Sports Video Analytics Solution By Sprectex AI.pdf",
}

VIDEO_ANALYTICS_GENERAL = "Business Propsal Video Analytics Solution By Sprectex AI.pdf"

# Optional demo video links included in the email body (not file attachments).
PRODUCT_VIDEO_LINKS = {
    "ai_recruiter": {
        "url": "https://drive.google.com/file/d/18KAShPcRqNe8rvdxReplrmhLexTep6M9/view?usp=sharing",
        "label": "AI Recruiter System Demo",
    },
}

INDUSTRY_VIDEO_LINKS = {
    "sports_organizations": {
        "url": "https://drive.google.com/file/d/1UBHfsknS9KPYiuMjk-s3CHdn6e8NmYx9/view?usp=sharing",
        "label": "Cricket Video Analytics Demo",
    },
}


def resolve_video_link(product_slug, industry_slug=None):
    if product_slug in PRODUCT_VIDEO_LINKS:
        return PRODUCT_VIDEO_LINKS[product_slug]
    if product_slug == "video_analytics" and industry_slug:
        return INDUSTRY_VIDEO_LINKS.get(industry_slug)
    return None


def resolve_proposal_filename(product_slug, industry_slug=None):
    """Pick the best proposal PDF for product + industry."""
    if industry_slug and industry_slug in PROPOSAL_MAP:
        return PROPOSAL_MAP[industry_slug]

    if product_slug in PROPOSAL_MAP:
        return PROPOSAL_MAP[product_slug]

    if product_slug == "video_analytics":
        return VIDEO_ANALYTICS_GENERAL

    return None


def _find_file_case_insensitive(filename):
    """Match a filename inside PROPOSALS_DIR ignoring case (Linux-safe)."""
    target = PROPOSALS_DIR / filename
    if target.exists():
        return target
    if not PROPOSALS_DIR.is_dir():
        return None
    lower = filename.lower()
    for entry in PROPOSALS_DIR.iterdir():
        if entry.is_file() and entry.name.lower() == lower:
            return entry
    return None


def resolve_proposal_path(product_slug, industry_slug=None):
    filename = resolve_proposal_filename(product_slug, industry_slug)
    if not filename:
        return None
    return _find_file_case_insensitive(filename)


def list_available_proposals():
    return {k: (PROPOSALS_DIR / v).exists() for k, v in {
        **PROPOSAL_MAP,
        "video_analytics_general": VIDEO_ANALYTICS_GENERAL,
    }.items()}
