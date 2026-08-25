"""
Statutory Mapping Service — IPC ↔ BNS cross-reference
TODO: Replace with a full DB-backed lookup table (SCC Online / Manupatra).
"""
from schemas.statutes import StatuteMapResponse

# Sample IPC → BNS mapping table
_IPC_TO_BNS: dict[str, StatuteMapResponse] = {
    "302": StatuteMapResponse(
        input_section="IPC 302",
        mapped_section="BNS 101",
        notes="Punishment for murder. BNS 101 retains the same penalty (death or life imprisonment).",
    ),
    "420": StatuteMapResponse(
        input_section="IPC 420",
        mapped_section="BNS 318",
        notes="Cheating and dishonestly inducing delivery of property. Penalty largely unchanged.",
    ),
    "376": StatuteMapResponse(
        input_section="IPC 376",
        mapped_section="BNS 63",
        notes="Rape. BNS 63 introduces additional aggravated categories with stricter sentencing.",
    ),
    "498a": StatuteMapResponse(
        input_section="IPC 498A",
        mapped_section="BNS 84",
        notes="Cruelty by husband or relatives. Equivalent provision retained under BNS.",
    ),
}


def map_statute(section: str) -> StatuteMapResponse:
    key = section.lower().replace("ipc ", "").replace("bns ", "").strip()
    if key in _IPC_TO_BNS:
        return _IPC_TO_BNS[key]
    return StatuteMapResponse(
        input_section=section,
        mapped_section="Not found in sample mapping table",
        notes="Full statutory cross-reference database not yet integrated. Check SCC Online / Manupatra.",
    )
