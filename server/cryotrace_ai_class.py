from datetime import datetime
import re
import json
from dateutil import parser
from typing import Optional, Tuple
from utils import  format_hours_minutes

class CryoTraceAI:
    def __init__(self, openai_client, cutoff_date: str = None):
        self.client = openai_client
        self.cutoff_date_str = cutoff_date
        if cutoff_date is None:
            self.cutoff_dt = (
                datetime.strptime(cutoff_date, "%Y-%m-%d") if cutoff_date
                else None
            )
        else:
            self.cutoff_dt = cutoff_date

    def _call_model(self, prompt: str, model: str = "gpt-3.5-turbo") -> str:
        try:
            response = self.client.chat.completions.create(
                model=model,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
                timeout=30
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ Failed with {model}. Error:", e)
            return None

    @staticmethod
    def parse_cutoff_date_and_direction(prompt: str) -> Tuple[Optional[datetime], str]:
        import re
        from dateutil import parser

        prompt_lower = prompt.lower()

        if "after" in prompt_lower or "since" in prompt_lower:
            direction = "after"
        elif "before" in prompt_lower or "prior to" in prompt_lower:
            direction = "before"
        else:
            direction = "all"

        # Match YYYY-MM-DD optionally followed by time
        match = re.search(r"(20\d{2}-\d{2}-\d{2}(?:[ Tt]\d{2}:\d{2}(?::\d{2})?)?)", prompt)
        if match:
            try:
                cutoff = parser.parse(match.group(1))
                return cutoff, direction
            except Exception as e:
                print("❌ Failed to parse date:", e)

        return None, direction


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

    def _call_model(self, prompt: str, model: str = "gpt-3.5-turbo") -> str:
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
        filtered = []
        for s in shipment_logs:
            pickup_time_str = s.get("pickup_time")
            if not pickup_time_str:
                continue

            try:
                pickup_dt = datetime.fromisoformat(pickup_time_str.replace("Z", ""))
            except ValueError:
                continue

            if self.cutoff_dt and pickup_dt < self.cutoff_dt:
                continue

            transit_time = format_hours_minutes((datetime.strptime(s['dropoff_time'] , "%Y-%m-%dT%H:%M:%SZ") - \
                datetime.strptime(s['pickup_time'], "%Y-%m-%dT%H:%M:%SZ")).seconds)


            filtered.append({
                "shipment_id": s.get("manifest_id"),
                "shipper_id": s.get("shipper_id"),
                "pickup_time": pickup_time_str,
                "pickup_contact": s.get("origin_contact"),
                "delivery_time": s.get("dropoff_time"),
                "receiver": s.get("destination_contact"),
                "transit_time_hours": transit_time,
                "evaporation_rate_kg_per_hour": s.get("evaporation_rate"),
            })

        return filtered