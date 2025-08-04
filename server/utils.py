
from dateutil import parser
import re
from datetime import datetime

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

from datetime import timedelta

def format_hours_minutes(seconds: float) -> str:
    """
    Converts seconds to a string like '2:30' (2 hours, 30 minutes).
    
    Args:
        seconds: Total seconds (from timedelta.total_seconds())
    
    Returns:
        A string in H:MM format
    """
    total_minutes = int(seconds // 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}:{minutes:02d}"

def format_shipments_brief(shipments: list[dict]) -> str:
    lines = []
    for s in shipments:
        lines.append(f"- ID: {s['shipment_id']}")
        lines.append(f"  Pickup: {s['pickup_time']} by {s['pickup_contact']}")
        lines.append(f"  Dropoff: {s['delivery_time']} to {s['receiver']}")
        lines.append(f"  Transit Time (hrs): {s['transit_time_hours']}")
        lines.append(f"  Evap Rate: {s['evaporation_rate_kg_per_hour']} kg/hr")
        lines.append("")
    return "\n".join(lines)
    

def format_shipments_for_prompt(shipments):
    sorted_shipments = sorted(shipments, key=lambda s: s["pickup_time"])
    lines = []
    
    for s in shipments:
        #evap_rate = compute_evaporation_volume(s['pickup_weight'] - s['dropoff_weight'])

        lines.append(f"- Shipment ID: {s['shipment_id']}")
        lines.append(f"  - Pickup: {s['pickup_time']} by {s['pickup_contact']}")
        lines.append(f"  - Delivery: {s['delivery_time']} received by {s['receiver']}")
        if s.get("transit_time_hours") is None:
            lines.append(f"  - Transit Time: {transit_time}")
        if s.get("evaporation_rate_kg_per_hour") is None:
            lines.append(f"  - Evaporation Rate: {evap_rate} kg/hr")
        lines.append("")  # Add spacing between shipments
    return "\n".join(lines)

def compute_evaporation_volume(ship_weight_kg: float, receive_weight_kg: float) -> float:
    """
    Computes volume of LN2 lost (in liters) between shipping and receiving weights.

    Args:
        ship_weight_kg: Weight at time of shipping (kg)
        receive_weight_kg: Weight at time of receiving (kg)

    Returns:
        Volume of liquid nitrogen lost, in liters
    """
    HEAT_OF_VAPORIZATION = 1.992e5     # J/kg (not used here, but kept for context)
    DENSITY_LN2 = 808                  # kg/m³
    CUBIC_METERS_TO_LITERS = 1000

    weight_loss = ship_weight_kg - receive_weight_kg
    if weight_loss <= 0:
        print("⚠️ No weight loss detected or invalid input.")
        return 0.0

    volume_m3 = weight_loss / DENSITY_LN2
    volume_liters = volume_m3 * CUBIC_METERS_TO_LITERS

    print(f"Evaporation volume: {volume_liters:.2f} L from {weight_loss:.2f} kg lost")
    return volume_liters