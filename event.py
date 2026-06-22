#event.py manages json intake for recording interactions, these will be stored on the block as a record and hashed 
#into merkle leafs

from datetime import datetime, timezone
import hashlib
import json


#events, recordings being put to a block from a json for this simulation, are normalized, 
#passed to the block for merkle tree management
def create_event(recording_id, custody_id, action, device_id=None, source_type=None, recording_hash=None, details=None):
    return {
        "recording_id": recording_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "custody_id": custody_id,
        "action": action,
        "device_id": device_id,
        "source_type": source_type,
        "recording_hash": recording_hash,
        "details": details or {}
    }


def group_events_by_recording_id(events):
	grouped = {}

	for event in events:
		recording_id = event["recording_id"]

		if recording_id not in grouped:
			grouped[recording_id] = []

		grouped[recording_id].append(event)

	return grouped


