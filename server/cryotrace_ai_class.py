from datetime import datetime
import re
import json
from dateutil import parser

class CryoTraceAI:
    def __init__(self, openai_client, cutoff_date: str = None):
        self.client = openai_client
        self.cutoff_date_str = cutoff_date
        self.cutoff_dt = (
            datetime.strptime(cutoff_date, "%Y-%m-%d") if cutoff_date
            else None
        )

    def _filter_logs_by_date(self, raw_logs: list[str]) -> list[str]:
        if not self.cutoff_dt:
            return raw_logs

        filtered = []
        for entry in raw_logs:
            try:
                pickup_text = entry.split("picked up from origin by")[1].split("on")[1].split("and")[0].strip()
                pickup_time = parser.parse(pickup_text)
                if pickup_time > self.cutoff_dt:
                    filtered.append(entry)
            except Exception as e:
                print("❌ Failed to parse log:", entry)
                print("   Reason:", e)
                continue
        return filtered

    def _build_prompt(self, logs: list[str]) -> str:
        log_text = "\n---\n".join(logs)
        return f"""
            You are a precise data extraction assistant.

            Extract structured information from each shipment log below. Return your answer as a JSON array with one object per shipment using this format:

            [
            {{
                "shipment_id": "MAN-xxxxx",
                "shipper_id": "shipper-ln2-20-0007",
                "pickup_time": "YYYY-MM-DD HH:MM",
                "pickup_contact": "Full name, role",
                "delivery_time": "YYYY-MM-DD HH:MM",
                "receiver": "Full name, role",
                "transit_time_hours": float,
                "evaporation_rate_kg_per_hour": float
            }},
            ...
            ]

            Shipment Logs:
            {log_text}
            """.strip()

    def _call_model(self, prompt: str, model: str) -> str:
        response = self.client.chat.completions.create(
            model=model,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

    def _safe_parse_json(self, raw_response: str) -> list[dict]:
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            print("⚠️ JSON decode failed. Raw response:\n", raw_response)
            return []

    def analyze_shipments(self, shipment_logs):
        """Filter shipments based on pickup_time and return structured results."""

        cutoff = self.cutoff_dt

        filtered = []
        for s in shipment_logs:
            pickup_time_str = s.get("pickup_time")
            if not pickup_time_str:
                continue

            try:
                pickup_dt = datetime.fromisoformat(pickup_time_str.replace("Z", ""))
            except ValueError:
                continue  # skip badly formatted dates

            if cutoff and pickup_dt < cutoff:
                continue

            filtered.append({
                "shipment_id": s.get("manifest_id"),
                "shipper_id": s.get("shipper_id"),
                "pickup_time": pickup_time_str,
                "pickup_contact": s.get("origin_contact"),
                "delivery_time": s.get("dropoff_time"),
                "receiver": s.get("destination_contact"),
                "transit_time_hours": s.get("transit_time"),
                "evaporation_rate_kg_per_hour": s.get("evaporation_rate"),
            })

        return filtered