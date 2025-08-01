
from dateutil import parser
import re

def extract_cutoff_date_from_question(question: str) -> str | None:
    date_patterns = [
        r'\b(\d{4}-\d{1,2}-\d{1,2})\b',     # e.g. 2025-04-25
        r'\b(\d{1,2}-\d{1,2}-\d{2,4})\b',   # e.g. 5-04-25
        r'\b(?:after|since)\s+([A-Za-z0-9,\s:-]+)',  # e.g. "after May 4"
    ]

    for pattern in date_patterns:
        matches = re.findall(pattern, question, flags=re.IGNORECASE)
        for match in matches:
            try:
                dt = parser.parse(match, fuzzy=True, yearfirst=True)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                continue
    return None

def format_shipments_for_prompt(shipments):
    return "\n\n".join([
        f"Shipment ID: {s['shipment_id']}\n"
        f"- Shipper ID: {s['shipper_id']}\n"
        f"- Pickup: {s['pickup_time']} by {s['pickup_contact']}\n"
        f"- Delivery: {s['delivery_time']} received by {s['receiver']}\n"
        f"- Transit Time: {s['transit_time_hours']} hours\n"
        f"- Evaporation Rate: {s['evaporation_rate_kg_per_hour']} kg/hour"
        for s in shipments
    ])