import pytest
from cryotrace_sg.server.cryotrace_ai_class import CryoTraceAI
from cryotrace_sg.server.main import build_where_filter
from datetime import datetime
import sys
import os

# Add project root (3 levels up from this test file) to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))


# 🔧 Sample mock data
MOCK_LOGS = [
    "Shipper shipper-ln2-20-0007 (MAN-000074) was picked up from origin by Dr. Gomez on 2025-05-05 05:52 and delivered to destination (received by Nurse Jenkins) on 2025-05-05 08:52. Transit time was 3.00 hours. Evaporation rate: 0.4567 kg/hour.",
    "Shipper shipper-ln2-20-0007 (MAN-000073) was picked up from origin by Dr. Shaw on 2025-05-03 12:52 and delivered to destination (received by Nurse Jenkins) on 2025-05-03 20:52. Transit time was 8.00 hours. Evaporation rate: 0.2487 kg/hour."
]

def test_sanity_check():
    assert 2 + 2 == 4


def test_build_where_filter_with_date():
    filters = build_where_filter(shipper_id="shipper-ln2-20-0007", cutoff_date="2025-05-04")
    assert filters["operator"] == "And"
    assert {"path": ["pickup_time"], "operator": "GreaterThan", "valueDate": "2025-05-04T00:00:00Z"} in filters["operands"]

def test_cryo_trace_ai_filters_logs():
    from openai import OpenAI
    mock_openai = OpenAI(api_key="test")  # Will not be called in this test

    analyzer = CryoTraceAI(openai_client=mock_openai, cutoff_date="2025-05-04")
    filtered, _ = analyzer.analyze_shipments(MOCK_LOGS)

    assert len(filtered) == 1
    assert filtered[0]["shipment_id"] == "MAN-000074"

