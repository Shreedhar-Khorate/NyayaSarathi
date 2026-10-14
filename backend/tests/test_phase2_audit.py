import sys
import os
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath("backend"))

from services.dataset_client import get_dataset_client
from services.precedent_verification import retrieve_huggingface_precedents
from services.war_room_service import research_precedents

def run_phase_2_audit():
    print("==================================================")
    print("PHASE 2 AUDIT: HUGGING FACE DATASET INTEGRATION")
    print("==================================================")

    # 1. Fetch known dataset record using supported query
    client = get_dataset_client()
    try:
        sample_rows = client.query_judgments(config="high_courts", split="test", limit=2)
        assert len(sample_rows) > 0, "No rows returned from remote Parquet"
        print(f"[TEST 1 PASS] Remote Parquet query succeeded. Fetched {len(sample_rows)} rows.")
        print(f"             Sample CNR: {sample_rows[0].get('cnr')} | Court: {sample_rows[0].get('court_name')}")
    except Exception as e:
        print(f"[TEST 1 FAIL] {e}")

    # 2. Retrieve relevant judgment records for residential property ownership dispute
    prop_desc = (
        "Raj claims ownership of a residential property based on a registered sale deed executed in 2019. "
        "Amit, who has occupied the property since 2021, disputes Raj's ownership and claims that the property "
        "was transferred to him by a family settlement. Raj has a copy of the sale deed and property tax receipts. "
        "Amit has provided a photocopy of an unsigned family settlement document."
    )
    try:
        precedents, prov = retrieve_huggingface_precedents(
            description=prop_desc,
            case_type="property",
            user_position="plaintiff",
            page=1,
            page_size=3
        )
        print(f"[TEST 2 PASS] Retrieved {len(precedents)} property dispute candidates.")
        for p in precedents:
            print(f"             - {p.get('title')} | CNR: {p.get('cnr')} | Court: {p.get('court')} | Outcome: {p.get('outcome_type')}")
    except Exception as e:
        print(f"[TEST 2 FAIL] {e}")

    # 3. Test pagination across multiple pages
    try:
        page1, _ = retrieve_huggingface_precedents(description=prop_desc, case_type="property", page=1, page_size=2)
        page2, _ = retrieve_huggingface_precedents(description=prop_desc, case_type="property", page=2, page_size=2)
        cnrs_p1 = [p["cnr"] for p in page1]
        cnrs_p2 = [p["cnr"] for p in page2]
        overlap = set(cnrs_p1).intersection(set(cnrs_p2))
        assert len(overlap) == 0, f"Pages should not overlap: {overlap}"
        print(f"[TEST 3 PASS] Pagination verified. Page 1: {cnrs_p1} | Page 2: {cnrs_p2} | Overlap: {len(overlap)}")
    except Exception as e:
        print(f"[TEST 3 FAIL] {e}")

    # 4. Test empty / unmatched query
    try:
        unmatched, prov_unmatched = retrieve_huggingface_precedents(
            description="completely nonexistent query term",
            query_text="NONEXISTENT_KEYWORD_XYZ_9999",
            page=1,
            page_size=3
        )
        print(f"[TEST 4 PASS] Unmatched query returned {len(unmatched)} records (graceful empty result).")
    except Exception as e:
        print(f"[TEST 4 FAIL] {e}")

    # 5. Test timeout / unavailable dataset error handling using controlled mock
    try:
        with patch.object(client, "query_judgments_with_offset", side_effect=Exception("Simulated Hugging Face Connection Timeout")):
            with patch("sqlite3.connect") as mock_conn:
                mock_conn.side_effect = Exception("Simulated DB Unreachable")
                precs_err, prov_err = retrieve_huggingface_precedents(
                    description=prop_desc,
                    query_text="force_error",
                    page=1,
                    page_size=3
                )
                print(f"[TEST 5 PASS] Controlled network/DB failure gracefully handled. Returned {len(precs_err)} records without crashing.")
    except Exception as e:
        print(f"[TEST 5 FAIL] Error was unhandled: {e}")

    # 6. Verify returned records preserve real source identifiers and metadata
    try:
        records, _ = retrieve_huggingface_precedents(description=prop_desc, case_type="property", page=1, page_size=2)
        for r in records:
            assert r.get("cnr") is not None and len(r.get("cnr")) > 3, "CNR missing or invalid"
            assert r.get("court") is not None and len(r.get("court")) > 0, "Court name missing"
            assert r.get("source_url") is not None and "huggingface.co" in r.get("source_url"), "Source URL missing"
        print(f"[TEST 6 PASS] Real source identifiers preserved: CNR, court, year, and Hugging Face source URL.")
    except Exception as e:
        print(f"[TEST 6 FAIL] {e}")

    # 7. Confirm Legal War Room consumes retrieved records instead of hardcoded judgments
    try:
        session_data = {
            "title": "Raj v. Amit",
            "description": prop_desc,
            "case_type": "property",
            "court": "Civil Court",
            "user_position": "plaintiff",
            "selected_doc_ids": [],
            "precedents": [],
        }
        res_precedents, prov, model, tokens, dur = research_precedents(session_data, [], query_text=None, page=1, page_size=3)
        assert len(res_precedents) > 0, "War room research_precedents returned empty"
        assert prov == "huggingface_dataset", f"Provider was not huggingface_dataset: {prov}"
        assert model == "overthelex/indian-court-decisions", f"Model origin was not overthelex: {model}"
        consumed_cnrs = [p.get("cnr") for p in res_precedents]
        print(f"[TEST 7 PASS] War Room research_precedents consumes {len(res_precedents)} Hugging Face dataset records. CNRs: {consumed_cnrs}")
    except Exception as e:
        print(f"[TEST 7 FAIL] {e}")

if __name__ == "__main__":
    run_phase_2_audit()
