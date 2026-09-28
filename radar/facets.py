"""Evidence-backed business workflows and project-domain suggestions.

Industry suggestions describe plausible projects, not verified deployments.
They are deliberately derived only from concrete documented workflows.
"""

import re


WORKFLOWS = {
    "appointments": ("预约与排期", "Appointments & scheduling", [r"\bappointment(s)?\b", r"\bbooking(s)?\b", r"\bschedul(e|ing) (meetings?|events?|appointments?|platform)\b", r"预约"]),
    "accounting": ("记账与财务报表", "Accounting & financial reports", [r"\baccounting\b.{0,4}:\s", r"\baccounting (software|system|reports?|records?|entries|module|features?)\b", r"\bfinancial reports?\b", r"\bcash flow\b", r"记账", r"财务报表"]),
    "invoicing": ("发票与账单", "Invoicing & billing", [r"\b(manag(e|ing)|generat(e|ing)|creat(e|ing)|handl(e|ing)) (customer )?invoices?\b", r"\binvoice management\b", r"发票管理", r"开具发票"]),
    "payments": ("支付与收款", "Payments & collection", [r"\bpayment (execution|processing|gateway|integration|collection)\b", r"\bprocess (online )?payments\b", r"\bcollect payments\b", r"支付执行", r"支付处理", r"收款管理"]),
    "inventory": ("库存与订单", "Inventory & orders", [r"\binventory (levels?|management|tracking|control)\b", r"\bstock levels?\b", r"\border management\b", r"库存", r"订单管理"]),
    "customer-service": ("客户服务", "Customer service", [r"\bcustomer support (agent|platform|automation|workflow)\b", r"\bcustomer service (agent|platform|automation|workflow)\b", r"\bhelpdesk platform\b", r"智能客服", r"客服系统", r"客服机器人"]),
    "customer-management": ("客户管理", "Customer management", [r"\bcrm\b", r"\bcustomer management\b", r"\bmanage (clients|customers)\b", r"客户管理"]),
    "marketing-content": ("营销内容", "Marketing content", [r"\bmarketing content\b", r"\bad campaign\b", r"\bseo content\b", r"\bpromotional video\b", r"营销内容", r"广告投放"]),
    "product-images": ("商品图片", "Product images", [r"\bproduct (images?|photos?|photography)\b", r"\be-?commerce (images?|photos?)\b", r"\bvirtual try-on\b", r"商品图片", r"电商图片"]),
    "data-reporting": ("数据分析与报表", "Data analysis & reporting", [r"\bdata analysis\b", r"\bfinancial reports?\b", r"\banalytics reports?\b", r"\b(reporting|analytics) dashboard\b", r"数据分析", r"经营报表"]),
    "education": ("教学与课程", "Teaching & courses", [r"\blesson plans?\b", r"\bcourse creation\b", r"\btutoring\b", r"教学", r"课程设计"]),
    "research": ("资料研究", "Research", [r"\bliterature review\b", r"\bweb research\b", r"\bresearch papers?\b", r"文献综述", r"资料研究"]),
}

INDUSTRIES = {
    "finance": ("财务与会计", "Finance & accounting", [r"\baccounting\b", r"\bfinancial reports?\b", r"财务", r"会计"], {"accounting"}),
    "beauty": ("理发与美容", "Barbering & beauty", [r"\bbarber(shop)?\b", r"\bhair salon\b", r"\bbeauty salon\b", r"理发", r"美容院"], {"appointments"}),
    "professional-services": ("专业服务", "Professional services", [r"\bconsulting firm\b", r"\bconsulting practice\b", r"咨询公司"], {"appointments"}),
    "retail": ("零售与电商", "Retail & e-commerce", [r"\bretail\b", r"\be-?commerce\b", r"零售", r"电商"], {"inventory", "product-images"}),
    "manufacturing": ("制造业", "Manufacturing", [r"\bmanufactur", r"\bproduction cycle\b", r"制造业", r"生产管理"], set()),
    "education": ("教育培训", "Education & training", [r"\beducation\b", r"\bschool\b", r"教育培训", r"学校"], {"education"}),
    "healthcare": ("医疗健康", "Healthcare", [r"\bhealthcare\b", r"\bclinic\b", r"\bmedical practice\b", r"医疗", r"诊所"], set()),
    "hospitality": ("酒店与餐饮", "Hospitality & food", [r"\bfor (hotels|restaurants)\b", r"\bhotel booking\b", r"\brestaurant reservations?\b", r"酒店预订", r"餐饮管理"], set()),
    "real-estate": ("房地产", "Real estate", [r"\breal estate\b", r"\bproperty management\b", r"房地产", r"物业管理"], set()),
}

WORKFLOW_LABELS_ZH = {slug: row[0] for slug, row in WORKFLOWS.items()}
WORKFLOW_LABELS_EN = {slug: row[1] for slug, row in WORKFLOWS.items()}
INDUSTRY_LABELS_ZH = {slug: row[0] for slug, row in INDUSTRIES.items()}
INDUSTRY_LABELS_EN = {slug: row[1] for slug, row in INDUSTRIES.items()}
FACETS_VERSION = 5

DIRECT_REQUIRES = {
    "finance": {"accounting"},
    "beauty": {"appointments"},
    "professional-services": {"appointments", "customer-management"},
    "retail": {"inventory", "product-images"},
    "manufacturing": {"inventory"},
    "education": {"education"},
}


def _first_match(documents, patterns, exclude_examples=False):
    for path, content in documents.items():
        # Inspect overview and feature prose, ignoring badges, image alt text,
        # navigation links and code. Those frequently contain incidental words.
        in_code = False
        window = 6000 if path.lower().endswith(("readme.md", "readme.markdown")) else 1800
        for raw_line in content[:window].splitlines():
            line = raw_line.strip()
            if line.startswith(("```", "~~~")):
                in_code = not in_code
                continue
            if in_code or not line or line.startswith(("<!--", "> [!", "<img", "![", "name:", "en_name:")):
                continue
            if re.search(r"\b(not for|not intended|does not support|never use)\b|不适用于|不要用于", line, re.IGNORECASE):
                continue
            if re.search(r"!\[[^]]*\]\(", line) or "shields.io" in line or "badge" in line.lower():
                continue
            if exclude_examples and re.search(r"\be\.g\.|\bfor example\b|例如|比如", line, re.IGNORECASE):
                continue
            if line.startswith("[") and "](" in line and not re.search(r"\w{40}", line):
                continue
            prose = re.sub(r"<[^>]+>", " ", line)
            if len(prose.strip(" -*#\t")) < 18:
                continue
            for pattern in patterns:
                if re.search(pattern, prose, re.IGNORECASE):
                    return {"path": path, "excerpt": re.sub(r"\s+", " ", line)[:220]}
    return None


def classify_facets(documents):
    """Return multi-label workflow and industry facets with original quotes."""
    workflow_evidence = []
    for slug, (_, _, patterns) in WORKFLOWS.items():
        quote = _first_match(documents, patterns)
        if quote and len(quote["excerpt"]) >= 8:
            workflow_evidence.append({"tag": slug, **quote})
    workflow_by_tag = {row["tag"]: row for row in workflow_evidence}
    industry_matches = []
    for slug, (_, _, patterns, inferred_from) in INDUSTRIES.items():
        direct = _first_match(documents, patterns, exclude_examples=True)
        has_relevant_workflow = not DIRECT_REQUIRES.get(slug) or bool(DIRECT_REQUIRES[slug] & workflow_by_tag.keys())
        if direct and len(direct["excerpt"]) >= 8 and has_relevant_workflow:
            industry_matches.append({"tag": slug, "basis": "explicit", **direct})
            continue
        source = next((workflow_by_tag[tag] for tag in inferred_from if tag in workflow_by_tag), None)
        if source and slug in {"beauty", "professional-services"}:
            appointment_context = re.search(r"\b(booking|appointments?|clients?|customers?|service providers?|scheduling platform|event types?)\b|预约", source["excerpt"], re.IGNORECASE)
            logistics_context = re.search(r"\b(freight|carrier|truck|delivery|shipping|logistics)\b|货运|物流", source["excerpt"], re.IGNORECASE)
            if not appointment_context or logistics_context:
                source = None
        if source:
            industry_matches.append({"tag": slug, "basis": "inferred", "workflow": source["tag"], "path": source["path"], "excerpt": source["excerpt"]})
    return {
        "workflows": [row["tag"] for row in workflow_evidence],
        "workflow_evidence": workflow_evidence,
        "industry_matches": industry_matches,
        "facets_source": "full_document",
        "facets_version": FACETS_VERSION,
    }
