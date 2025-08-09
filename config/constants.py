# Centralized constants and mappings used across the app.
# Behaviour-preserving refactor: content identical to previous inline definitions.

NOTICE_TYPE_MAP = {
    "Contract notice": "cn-standard",
    "Contract award notice": "can-standard",
    "Prior information notice": "pin-standard",
    "Design contest notice": "cn-desg",
    "Design contest results": "can-desg",
    "Modification notice": "can-modif",
    "Social and other specific services – public contracts": "cn-social",
    "Social and other specific services – utilities": "cn-social",
    "Social and other specific services – concessions": "cn-social",
    "Result of contest": "can-social",
    "Concession notice": "cn-standard",
    "Concession award notice": "can-standard",
    "Voluntary ex ante transparency notice": "veat",
    "Buyer profile": "pin-buyer",
    "Qualification system – utilities": "pin-standard",
    "Periodic indicative notice – utilities": "pin-standard",
}

PROCEDURE_TYPE_MAP = {
    "Open procedure": "pt-open",
    "Restricted procedure": "pt-restricted",
    "Competitive procedure with negotiation": "pt-competitive-negotiation",
    "Competitive dialogue": "pt-competitive-dialogue",
    "Innovation partnership": "pt-innovation",
    "Negotiated procedure without prior publication": "pt-negotiated-without-call",
    "Award of a contract without prior publication": "pt-award-wo-prior-call",
    "Not specified": None,
}

CONTRACT_TYPE_MAP = {
    "Works": "works",
    "Supplies": "supplies",
    "Services": "services",
    "Not specified": None,
}
