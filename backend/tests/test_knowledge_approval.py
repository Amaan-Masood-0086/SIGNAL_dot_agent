import base64
import datetime as dt

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from app.services.knowledge_approval import ReviewReceipt, signing_bytes, verify_approved_subset
from app.services.knowledge_release import review_manifest


@pytest.fixture
def packet():
    manifest = review_manifest()
    item = manifest["entries"][0]
    receipt = {
        "schema_version": "1.0", "release_id": manifest["release_id"],
        "release_sha256": manifest["content_sha256"], "reviewer": "TEST ONLY",
        "reviewer_credentials": "Synthetic test, not a clinician", "reviewed_on": "2026-09-11",
        "review_document": "test://review", "scoring_policy_document": "test://policy",
        "r14_decision_document": "test://r14",
        "legacy_decisions": {ref: "Synthetic test exclusion" for ref in manifest["blockers"]["legacy_specific_review"]},
        "entries": [{"citation_ref": item["citation_ref"], "content_sha256": item["content_sha256"], "clinical": "approved", "translation": "approved", "rationale": "Synthetic fixture only"}],
    }
    key = Ed25519PrivateKey.generate()
    def check(data, *, sign=True, trust=True):
        signature = key.sign(signing_bytes(ReviewReceipt.model_validate(data if sign else receipt)))
        return verify_approved_subset(data, signature_base64=base64.b64encode(signature).decode(), key_id="test", trusted_keys={"test": key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)} if trust else {}, today=dt.date(2026, 9, 11))
    return receipt, check


def test_signed_subset_does_not_activate_runtime(packet):
    receipt, check = packet
    result = check(receipt)
    assert len(result["entries"]) == 1
    assert result["runtime_enabled"] is False
    assert result["remaining_gates"]


def test_unknown_reviewer_rejected(packet):
    receipt, check = packet
    with pytest.raises(ValueError, match="not trusted"):
        check(receipt, trust=False)


@pytest.mark.parametrize("change", [
    {"release_sha256": "0" * 64}, {"legacy_decisions": {}}, {"reviewed_on": "2099-01-01"},
])
def test_signed_but_invalid_approval_rejected(packet, change):
    receipt, check = packet
    with pytest.raises(ValueError):
        check({**receipt, **change})


def test_tampered_receipt_rejected(packet):
    receipt, check = packet
    with pytest.raises(ValueError, match="signature"):
        check({**receipt, "review_document": "tampered"}, sign=False)


def test_duplicate_and_untranslated_entries_rejected(packet):
    receipt, check = packet
    with pytest.raises(ValueError, match="Duplicate"):
        check({**receipt, "entries": receipt["entries"] * 2})
    with pytest.raises(ValueError, match="No jointly approved"):
        check({**receipt, "entries": [{**receipt["entries"][0], "translation": "excluded"}]})
