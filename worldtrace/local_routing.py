"""Conservative deterministic task selection for synthetic local missions.

This is keyword routing, NOT model reasoning. Broad missions retain all nine
checks; narrow missions select only explicitly named technical domains.
"""
from .tools import AVAILABLE

DOMAINS = (
    ("pdf_inspect", ("pdf", "document", "signature", "signed")),
    ("email_inspect", ("email", "mail", "message notice")),
    ("network_inspect", ("har", "network", "http", "traffic")),
    ("etl_compare", ("etl", "csv", "pipeline", "source and target")),
    ("database_check", ("database", "sqlite", "sql", "database records")),
    ("api_virtualize", ("api contract", "mock api", "virtualization", "mocked api")),
    ("performance_probe", ("performance", "latency", "benchmark")),
    ("middleware_test", ("middleware", "queue", "duplicate event", "idempotency")),
    ("mainframe_contract", ("mainframe", "fixed-width", "legacy record")),
)
BROAD_TERMS = ("supplier onboarding", "all tools", "all checks", "end-to-end", "comprehensive", "entire workflow")

def select_local_tools(goal):
    text = " ".join(goal.lower().split())
    if any(term in text for term in BROAD_TERMS):
        return sorted(AVAILABLE), "Broad mission: execute all available local fixture checks."
    selected = [name for name, terms in DOMAINS if any(term in text for term in terms)]
    if len(selected) < 2:
        return sorted(AVAILABLE), "No unambiguous multi-tool scope: use full local fixture coverage."
    return selected, "Deterministic keyword routing from stated technical domains; NOT AI planning."
