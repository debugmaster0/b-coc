#merkle.py uses a merkle tree to catalog recording access and activity

import hashlib
import json

def hash_data(data):
	return hashlib.sha256(str(data).encode()).hexdigest()

#converts dictionary into string to enable encoding for hash
def hash_event(event):
    event_string = json.dumps(event, sort_keys=True)
    return hash_data(event_string)

def create_merkle_root(events):
	if not events:
		return None

	#combines hashes from tree
	combined_hashes = [hash_event(event) for event in events]


	while (len(combined_hashes) > 1):
		if len(combined_hashes) % 2 == 1:
			#checks if odd number of hashes, if odd, reuse last hash for hash combination
			combined_hashes.append(combined_hashes[-1])

		new_level = []

		#loop through leaf nodes 2 at a time, working up the tree
		for i in range(0,len(combined_hashes), 2):
			combine_leafs = combined_hashes[i] + combined_hashes[i+1]
			new_level.append(hash_data(combine_leafs))
		combined_hashes = new_level

	return combined_hashes[0]

def validate_merkle_root(events, merkle_root):
    return create_merkle_root(events) == merkle_root


