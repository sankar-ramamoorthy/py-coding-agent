from pathlib import Path

from py_mono.skill import approval_ledger


def test_hash_file_ignores_crlf_vs_lf(tmp_path):
    """git's core.autocrlf rewrites a text file's on-disk line endings
    depending on the checking-out platform (CRLF on native Windows, LF in
    CI/Linux/Docker) even though the tracked content is identical. hash_file
    must treat both representations as the same content, or an approval
    recorded on one platform silently invalidates itself on another with no
    actual content change (see ISS-005)."""
    lf_file = tmp_path / "lf_skill.py"
    crlf_file = tmp_path / "crlf_skill.py"

    lf_file.write_bytes(b"def run():\n    return 1\n")
    crlf_file.write_bytes(b"def run():\r\n    return 1\r\n")

    assert approval_ledger.hash_file(lf_file) == approval_ledger.hash_file(crlf_file)


def test_is_approved_survives_line_ending_conversion(tmp_path):
    skill_py = tmp_path / "skill.py"
    skill_py.write_bytes(b"def run():\n    return 1\n")

    ledger = {}
    approval_ledger.record_approval(ledger, "sample", skill_py)
    assert approval_ledger.is_approved(ledger, "sample", skill_py)

    # Simulate a platform re-checkout converting LF -> CRLF with no content change.
    skill_py.write_bytes(b"def run():\r\n    return 1\r\n")
    assert approval_ledger.is_approved(ledger, "sample", skill_py)


def test_is_approved_still_rejects_real_content_changes(tmp_path):
    skill_py = tmp_path / "skill.py"
    skill_py.write_bytes(b"def run():\n    return 1\n")

    ledger = {}
    approval_ledger.record_approval(ledger, "sample", skill_py)

    skill_py.write_bytes(b"def run():\n    return 2\n")
    assert not approval_ledger.is_approved(ledger, "sample", skill_py)
