from config import BASE_DIR

LOGO_PATH = BASE_DIR / "static" / "email" / "logo.png"

SIGNATURE_PLAIN = """Best Regards,
Syeda Shamaim Shah
Chief Executive Officer | Sprectex AI
www.sprectexai.com
sales@sprectexai.com | shamaim@sprectexai.com
+92 328 2736246 | +92 320 2710923"""

SIGNATURE_HTML = """
<table cellpadding="0" cellspacing="0" style="margin-top:28px;border-top:2px solid #e11d2a;padding-top:18px;font-family:Arial,Helvetica,sans-serif;">
  <tr>
    <td style="font-size:15px;color:#1a1a1f;font-weight:700;">Best Regards,</td>
  </tr>
  <tr>
    <td style="padding-top:10px;font-size:15px;color:#1a1a1f;font-weight:700;">Syeda Shamaim Shah</td>
  </tr>
  <tr>
    <td style="padding-top:4px;font-size:13px;color:#e11d2a;font-weight:600;">Chief Executive Officer | Sprectex AI</td>
  </tr>
  <tr>
    <td style="padding-top:10px;font-size:13px;color:#555;">
      <a href="https://www.sprectexai.com" style="color:#e11d2a;text-decoration:none;">www.sprectexai.com</a>
    </td>
  </tr>
  <tr>
    <td style="padding-top:6px;font-size:13px;color:#555;">
      <a href="mailto:sales@sprectexai.com" style="color:#555;text-decoration:none;">sales@sprectexai.com</a>
      &nbsp;|&nbsp;
      <a href="mailto:shamaim@sprectexai.com" style="color:#555;text-decoration:none;">shamaim@sprectexai.com</a>
    </td>
  </tr>
  <tr>
    <td style="padding-top:6px;font-size:13px;color:#555;">
      +92 328 2736246 &nbsp;|&nbsp; +92 320 2710923
    </td>
  </tr>
</table>
"""


def _first_name(full_name):
    name = (full_name or "").strip()
    if not name:
        return "there"
    return name.split()[0]


def _company_label(company):
    company = (company or "").strip()
    if company:
        return company
    return "your organization"


def _wrap_html(body_paragraphs_html):
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f6f7f9;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f6f7f9;padding:24px 12px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.06);">
          <tr>
            <td style="background:#ffffff;padding:28px 32px 16px;text-align:center;border-bottom:3px solid #e11d2a;">
              <img src="cid:sprectex_logo" alt="Sprectex AI" width="180" style="display:block;margin:0 auto;max-width:180px;height:auto;">
            </td>
          </tr>
          <tr>
            <td style="padding:32px 36px 28px;color:#333;font-size:15px;line-height:1.7;">
              {body_paragraphs_html}
              {SIGNATURE_HTML}
            </td>
          </tr>
          <tr>
            <td style="background:#1a1a1f;padding:14px 36px;text-align:center;">
              <span style="color:#999;font-size:11px;">&copy; Sprectex AI - Intelligent Solutions for Modern Business</span>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _p(text):
    return f'<p style="margin:0 0 16px;color:#333;font-size:15px;line-height:1.7;">{text}</p>'


def _build(name, company, industry, subject, paragraphs_plain, paragraphs_html, product_slug=None, industry_slug=None):
    first = _first_name(name)
    org = _company_label(company)
    ind = industry or "your sector"

    replacements = {
        "{first_name}": first,
        "{name}": (name or "").strip() or "there",
        "{company}": org,
        "{industry}": ind,
    }

    def apply(text):
        for key, val in replacements.items():
            text = text.replace(key, val)
        return text

    from proposals_config import resolve_proposal_filename

    proposal_file = resolve_proposal_filename(product_slug, industry_slug)
    plain_body = "\n\n".join(apply(p) for p in paragraphs_plain) + "\n\n" + SIGNATURE_PLAIN
    html_body = _wrap_html("\n".join(_p(apply(p)) for p in paragraphs_html))

    return {
        "subject": apply(subject),
        "html": html_body,
        "plain": plain_body,
    }


# ---------------------------------------------------------------------------
# Product-level templates (AI Recruiter & Supply Chain)
# ---------------------------------------------------------------------------

PRODUCT_TEMPLATES = {
    "ai_recruiter": {
        "subject": "A smarter way to hire for {company}",
        "paragraphs": [
            "Hi {first_name},",
            "I came across {company} and thought it might be worth a quick conversation. At Sprectex AI, we have been helping teams in the {industry} space hire faster without compromising on candidate quality.",
            "Our AI Recruiter System takes care of the heavy lifting - screening applications, shortlisting the right profiles, and helping your team move from posting to offer letter in far less time. Several HR teams we work with have cut their time-to-hire significantly while actually improving the quality of candidates reaching interview stage.",
            "I have attached a short proposal that outlines how this could work for {company}. If it looks relevant, I would genuinely love to set up a brief 15-minute call at your convenience - no pressure, just a friendly walkthrough.",
        ],
    },
    "supply_chain": {
        "subject": "Better demand forecasting for {company}?",
        "paragraphs": [
            "Hi {first_name},",
            "I hope this message finds you well. I have been following how companies in {industry} are dealing with demand uncertainty, and I felt {company} might benefit from what we are building at Sprectex AI.",
            "We help supply chain and operations teams forecast demand with far greater accuracy using AI - which typically means less excess inventory sitting on shelves, fewer stockouts, and planning decisions your team can actually trust.",
            "I have put together a proposal specifically for organizations like yours. Would you be open to a short call this week or next? I think you will find the results we have achieved for similar businesses quite interesting.",
        ],
    },
}

# ---------------------------------------------------------------------------
# Video Analytics - industry-specific templates
# ---------------------------------------------------------------------------

INDUSTRY_TEMPLATES = {
    "poultry_farms": {
        "subject": "Helping poultry farms like yours monitor flock health smarter",
        "paragraphs": [
            "Hi {first_name},",
            "I wanted to reach out because we have been working with several poultry operations, and I believe what we have built at Sprectex AI could be genuinely useful for {company}.",
            "Our AI video analytics platform watches your flock around the clock - tracking movement patterns, feeding behaviour, and early signs of stress or illness that are easy to miss during manual rounds. Farms using our system tell us it has helped them respond to issues days earlier and reduce losses they did not see coming.",
            "I have attached a proposal tailored for poultry operations. If you have 15 minutes this week, I would love to show you a quick demo on how it works in a real farm environment.",
        ],
    },
    "sports_organizations": {
        "subject": "Performance insights for {company} - without extra manual work",
        "paragraphs": [
            "Hi {first_name},",
            "I have been speaking with a number of sports organizations lately, and one challenge keeps coming up - getting meaningful performance data from match and training footage without spending hours on manual review.",
            "That is exactly what our AI video analytics platform does for teams like {company}. It automatically tracks player movements, generates performance reports, and gives coaches actionable insights they can use in the next training session - not next month.",
            "I have attached a proposal for sports organizations. Would you be open to a brief call? I think you will find the demo quite relevant to what your coaching staff is trying to achieve.",
        ],
    },
    "fitness_gyms": {
        "subject": "Could {company} benefit from smarter facility insights?",
        "paragraphs": [
            "Hi {first_name},",
            "I hope you are doing well. I wanted to share something we have been building at Sprectex AI that several gym and fitness centre owners have found surprisingly useful.",
            "Our video analytics platform helps you understand how members actually use your facility - peak hours, equipment demand, floor traffic, and safety oversight - without adding extra staff. It gives managers real data to make decisions about layout, staffing, and member experience.",
            "I have attached a short proposal for fitness centres. If this sounds relevant to {company}, I would be happy to walk you through a quick demo at a time that suits you.",
        ],
    },
    "manufacturing": {
        "subject": "Catching production issues earlier at {company}",
        "paragraphs": [
            "Hi {first_name},",
            "I wanted to connect because manufacturers like {company} are under constant pressure to maintain quality and safety on the production floor - often with limited visibility between manual inspections.",
            "Our AI video analytics solution monitors your production lines in real time, flagging defects, safety risks, and process bottlenecks as they happen. Plants we work with have reduced unplanned downtime and improved compliance without hiring additional supervisors.",
            "Please find a proposal attached. I would welcome the chance to show you how this works on a real production floor - even a 15-minute call would give you a clear picture.",
        ],
    },
    "smart_cities": {
        "subject": "Smarter urban monitoring for {company}",
        "paragraphs": [
            "Hi {first_name},",
            "As cities and municipalities invest more in smart infrastructure, the challenge of turning camera feeds into actionable intelligence keeps growing. I thought {company} might find our work at Sprectex AI relevant.",
            "Our AI video analytics platform helps urban authorities monitor traffic flow, public safety, and pedestrian movement in real time - giving planning and operations teams data they can act on immediately rather than reviewing footage after the fact.",
            "I have attached a proposal for smart city projects. Would you be open to a short conversation about how this could support your current initiatives?",
        ],
    },
    "retail_stores": {
        "subject": "Understanding your customers better at {company}",
        "paragraphs": [
            "Hi {first_name},",
            "Retail is tougher than ever, and I imagine {company} is always looking for better ways to understand customer behaviour and protect margins.",
            "Our AI video analytics helps retail stores track footfall, dwell time, and in-store movement patterns - giving you the kind of insight that helps with layout decisions, staffing, and loss prevention. No extra hardware beyond your existing cameras in most cases.",
            "I have attached a proposal for retail businesses. If you have a few minutes this week, I would love to show you what the dashboard looks like with real store data.",
        ],
    },
    "warehouses_logistics": {
        "subject": "More visibility across your warehouse operations",
        "paragraphs": [
            "Hi {first_name},",
            "Warehouse and logistics teams at companies like {company} often struggle with visibility - knowing what is happening across loading bays, storage zones, and pick lines without being physically present everywhere.",
            "Our AI video analytics platform gives operations managers a real-time view of activity across the facility, helping identify bottlenecks, safety risks, and inefficiencies before they become costly problems.",
            "Please find a tailored proposal attached. I would be glad to arrange a brief demo if this aligns with your operational priorities.",
        ],
    },
    "security_surveillance": {
        "subject": "Reducing false alarms and improving response times",
        "paragraphs": [
            "Hi {first_name},",
            "Security teams are overwhelmed with footage but short on actionable alerts - I hear this from organisations like {company} regularly.",
            "Our AI video analytics filters out noise and surfaces genuine threats: unauthorised access, unusual activity, and perimeter breaches in real time. Security teams we work with report faster response times and far fewer false alarms keeping staff up at night.",
            "I have attached a proposal for your review. Would a short call make sense to explore whether this fits your current security setup?",
        ],
    },
    "agriculture": {
        "subject": "Remote monitoring that actually works for farms like yours",
        "paragraphs": [
            "Hi {first_name},",
            "Running agricultural operations means you cannot be everywhere at once - and I imagine that is a daily reality for {company}.",
            "Our AI video analytics platform helps farms monitor crops, livestock, irrigation, and field activity remotely. It flags issues early - whether that is equipment problems, irrigation failures, or unusual animal behaviour - so your team can respond before losses add up.",
            "I have attached a proposal for agricultural operations. If you are open to it, I would love to show you a quick demo using scenarios relevant to your type of farming.",
        ],
    },
    "education_training": {
        "subject": "Safer, smarter campuses for {company}",
        "paragraphs": [
            "Hi {first_name},",
            "Schools and training institutions carry a real responsibility for student safety and engagement - and I know {company} takes that seriously.",
            "Our AI video analytics helps educational institutions monitor campus activity, improve access control, and gain insights into classroom and training session engagement. Administrators get a clearer picture without adding burden to teaching staff.",
            "Please find an attached proposal. I would welcome a brief conversation about how this could support your institution's goals.",
        ],
    },
    "healthcare_facilities": {
        "subject": "Improving patient safety and flow at {company}",
        "paragraphs": [
            "Hi {first_name},",
            "Healthcare facilities like {company} operate under constant pressure - patient safety, staff compliance, and operational efficiency all matter every single day.",
            "Our AI video analytics platform helps hospitals and clinics monitor patient flow, waiting areas, and safety compliance in real time. It can also assist in detecting falls and emergency situations faster, giving staff critical extra minutes when they matter most.",
            "I have attached a proposal for healthcare facilities. Would you be open to a short call to see if this is relevant to your current priorities?",
        ],
    },
    "construction_sites": {
        "subject": "Keeping construction sites safer at {company}",
        "paragraphs": [
            "Hi {first_name},",
            "Construction site safety and progress tracking is one of those problems that every project manager wishes they had better visibility on - I imagine that resonates at {company}.",
            "Our AI video analytics monitors sites for PPE compliance, unauthorised access, and safety hazards in real time. Project teams also use it to track progress across multiple sites without constant physical visits.",
            "I have attached a proposal for construction companies. A brief demo would give you a clear sense of how this works on an active site - happy to arrange at your convenience.",
        ],
    },
    "hotels_hospitality": {
        "subject": "Elevating guest experience at {company}",
        "paragraphs": [
            "Hi {first_name},",
            "In hospitality, the details guests do not see often matter most - staffing levels, lobby flow, and security across a large property. I thought our work at Sprectex AI might be relevant for {company}.",
            "Our AI video analytics helps hotels monitor guest areas, optimise staff allocation during busy periods, and maintain security standards across the property - all without making guests feel watched.",
            "Please find a proposal attached. I would love to share a quick walkthrough if you have 15 minutes this week.",
        ],
    },
    "airports_transport": {
        "subject": "Smoother passenger flow for {company}",
        "paragraphs": [
            "Hi {first_name},",
            "Airports and transport hubs face a unique challenge - thousands of passengers, strict security requirements, and operations that cannot afford delays. I believe {company} would find our platform relevant.",
            "Our AI video analytics helps transport operators manage passenger queues, monitor terminal activity, and support security teams with real-time intelligence - improving both efficiency and the passenger experience.",
            "I have attached a proposal for airports and transport operators. Would you be open to a short introductory call?",
        ],
    },
}


def build_email(name, company, industry_name, product_slug, industry_slug=None):
    if product_slug == "video_analytics" and industry_slug:
        tmpl = INDUSTRY_TEMPLATES.get(industry_slug)
        if tmpl:
            return _build(
                name, company, industry_name,
                tmpl["subject"], tmpl["paragraphs"], tmpl["paragraphs"],
                product_slug, industry_slug,
            )

    tmpl = PRODUCT_TEMPLATES.get(product_slug)
    if tmpl:
        return _build(
            name, company, industry_name,
            tmpl["subject"], tmpl["paragraphs"], tmpl["paragraphs"],
            product_slug, industry_slug,
        )

    return _build(
        name, company, industry_name,
        "Introduction from Sprectex AI",
        [
            "Hi {first_name},",
            "I hope this email finds you well. I wanted to reach out from Sprectex AI regarding a solution that may be relevant for {company} in the {industry} space.",
            "We would love the opportunity to share more details at your convenience.",
        ],
        [
            "Hi {first_name},",
            "I hope this email finds you well. I wanted to reach out from Sprectex AI regarding a solution that may be relevant for {company} in the {industry} space.",
            "We would love the opportunity to share more details at your convenience.",
        ],
        product_slug, industry_slug,
    )


def preview_email(name, company, industry_name, product_slug, industry_slug=None):
    return build_email(name, company, industry_name, product_slug, industry_slug)
