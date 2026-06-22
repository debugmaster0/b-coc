#block.py is the guts of the block chain. It holds meta data for chain of custody

import hashlib
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
import json
from datetime import datetime, timezone

class Block:
	#event is meta data to store on block, global_id keeps track of placement for global sequence in ledger, previous block 
	#allows for previous block.hash access
	def __init__(self, event, global_id, previous_block=None):
		self.global_id = global_id                               

		
		if previous_block:
			self.block_id = previous_block.block_id + 1				#local block ID based on previous block ID
			self.previous_hash = previous_block.block_hash      	#previous hash pulled fromm previous block hash
		else:				
			self.block_id = 1										#local genisis block gets ID 1
			self.previous_hash = "0"								#local genisis previous block hash is 0
		
		#evidence metadata, event is data from json to store on block for simulation purposes
		self.evidence_id = event["evidence_id"]					
		self.signer_id = event.get("signer_id") or event.get("device_id")		#non cryptographic unique identifier
		self.signature = event.get("signature")									#cryptographic private signature uses ec-secp256
		self.public_key = event.get("public_key")					#cryptographic public key 
		self.source_type = event.get("source_type")								#meta data for initial evidence uploads (bodycam, cctv, etc)
		self.evidence_hash = event.get("evidence_hash")							#cryptographic hash of evidencde
		self.events = event.get("action")										#evidence transactions and interaction types (accessed, copied, analyzed, transferred)
		self.timestamp = datetime.now(timezone.utc).isoformat()
		
		#block hash
		self.block_hash = self.calculate_hash()									#hash of block header

	   

	def calculate_hash(self):
		block_header = {
			"global_id": self.global_id,
			"block_id": self.block_id,
			"evidence_id": self.evidence_id,
			"signer_id": self.signer_id,
			"source_type": self.source_type,
			"evidence_hash": self.evidence_hash,
			#"timestamp": self.timestamp,
			"previous_hash": self.previous_hash,
			"events": self.events,
		}
		encoded_data = json.dumps(block_header, sort_keys=True).encode()
		return hashlib.sha256(encoded_data).hexdigest()

	#not used yet but will be for adding custom blocks in gui
	def sign_block(self, private_key):			

		signature = private_key.sign(
			self.block_hash.encode(),
			ec.ECDSA(hashes.SHA256())
		)

		self.signature = signature.hex()