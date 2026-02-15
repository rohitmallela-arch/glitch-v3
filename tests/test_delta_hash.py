from ingest.delta_engine import snapshot_hash

def test_snapshot_hash_changes_on_status():
    r1 = {"status": "shortage", "last_updated": "2024-01-01"}
    r2 = {"status": "resolved", "last_updated": "2024-01-01"}
    assert snapshot_hash(r1) != snapshot_hash(r2)
