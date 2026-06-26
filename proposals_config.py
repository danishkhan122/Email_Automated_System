from config import PROPOSALS_DIR

# Actual proposal PDFs uploaded by admin
PROPOSAL_MAP = {
    "ai_recruiter": "Business Proposal AI Recruiter System By Sprectex AI.pdf",
    "supply_chain": "AI Forecasting Solution For Industries By Sprectex AI.pdf",
    "poultry_farms": "Business Proposal For Chicken Video Analytics Solution By Sprectex AI.pdf",
    "sports_organizations": "Business Proposal Sports Video Analytics Solution By Sprectex AI.pdf",
}

VIDEO_ANALYTICS_GENERAL = "Business Propsal Video Analytics Solution By Sprectex AI.pdf"


def resolve_proposal_filename(product_slug, industry_slug=None):
    """Pick the best proposal PDF for product + industry."""
    if industry_slug and industry_slug in PROPOSAL_MAP:
        return PROPOSAL_MAP[industry_slug]

    if product_slug in PROPOSAL_MAP:
        return PROPOSAL_MAP[product_slug]

    if product_slug == "video_analytics":
        return VIDEO_ANALYTICS_GENERAL

    return None


def resolve_proposal_path(product_slug, industry_slug=None):
    filename = resolve_proposal_filename(product_slug, industry_slug)
    if not filename:
        return None
    path = PROPOSALS_DIR / filename
    return path if path.exists() else None


def list_available_proposals():
    return {k: (PROPOSALS_DIR / v).exists() for k, v in {
        **PROPOSAL_MAP,
        "video_analytics_general": VIDEO_ANALYTICS_GENERAL,
    }.items()}
