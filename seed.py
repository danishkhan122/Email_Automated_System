"""Force re-seed products, industries, and countries.

Run this once on the server (cPanel "Execute python script" -> seed.py)
after pulling new code, to add any newly added industries like Car Industry.
"""
from database import init_db, get_db, VIDEO_ANALYTICS_INDUSTRIES

if __name__ == "__main__":
    init_db()

    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT i.slug, i.name
            FROM industries i
            JOIN products p ON p.id = i.product_id
            WHERE p.slug = 'video_analytics'
            ORDER BY i.sort_order
            """
        ).fetchall()

    print("Video Analytics industries currently in DB:")
    for r in rows:
        print(" -", r["slug"], "|", r["name"])

    slugs = {r["slug"] for r in rows}
    expected = {s for s, _ in VIDEO_ANALYTICS_INDUSTRIES}
    missing = expected - slugs
    if missing:
        print("MISSING:", missing)
    else:
        print("All industries present (including car_industry).")
