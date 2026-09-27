from apps.shared.ocsf import outcome_from_disposition, verdict_data


def test_missing_disposition_returns_no_data():
    """Verify that empty string and 'None' dispositions return 'No Data'."""
    assert outcome_from_disposition(None) == "No Data"
    assert outcome_from_disposition("None") == "No Data"


def test_verdict_data_missing_disposition():
    """Verify verdict_data output when event has no disposition key."""
    event = {
        "class_uid": 3002,
        "class_name": "Authentication",
        "category_uid": 3,
        "status_id": 1,
        "status": "Success",
    }
    result = verdict_data(
        event=event,
        verdict_id="vrd-001",
        engagement_id="eng-001",
    )
    assert result["outcome"] == "No Data"
