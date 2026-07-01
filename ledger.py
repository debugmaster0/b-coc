import hashlib
from block import Block
from blockchain import Blockchain
from sign_util import sign_hash, verify_hash_signature
from datetime import datetime, timezone
import json


class EvidenceLedger:
	def __init__(self):
		self.chains = {}
		self.ledger_state_root = "0" 
		self.global_block_count = 0  # Tracks absolute creation order

	def create_chain(self, evidence_id):
		self.chains[evidence_id] = Blockchain()

	def add_block(self, event, private_key=None):
		evidence_id = event["evidence_id"]

		#if evidence is now, create new chain
		if evidence_id not in self.chains:
			self.create_chain(evidence_id)

		#adding block so global counter is increased (always greater than 0 if ledger exists)
		self.global_block_count += 1
		
		#find the chain the record belongs to, returns none if no self chain. 
		target_blockchain = self.chains[evidence_id]
		latest_block = target_blockchain.get_latest_block()

		#create block, global_block_count is passed into block for its global ID, latest block used to get hash
		new_block = Block(event, self.global_block_count, previous_block=latest_block)

		####################################################
		#####need to rework signature workflow for gui#######
		#####################################################
		if private_key:
			new_block.signature = sign_hash(new_block.block_hash, private_key)
		
		#append block
		target_blockchain.chain.append(new_block)
		
		#This updates the state root hash for the ledger
		state_mix = f"{self.ledger_state_root}{new_block.block_hash}"
		self.ledger_state_root = hashlib.sha256(state_mix.encode()).hexdigest()

#Checks individual chain integrity with validate chain, then sorts blocks by global_id, if the id's arent sequenctual
#or calculated state root (root hash) doesnt match, its invalid. 
	def validate_ledger(self):
		calculated_state_root = "0"
		all_blocks = []
		
		if self.global_block_count == 0:
			print("Ledger is empty. Import events first.")
			return False
			
		# Step 1: Validate individual chains
		for evidence_id, blockchain in self.chains.items():

			if not blockchain.validate_chain():
				print(f"Invalid chain structural integrity: {evidence_id}")
				return False

			# create single list of ALL blocks, important to use global ID for sorting because validation was messy otherwise
			all_blocks.extend(blockchain.chain)
			
		#state root is estblished by hashing blocks FIFO, they are sorted by global_id to maintain that structure for hashing
		all_blocks.sort(key=lambda blk: blk.global_id)
		
		#Recalc state root in the exact order they were created
		for i, block in enumerate(all_blocks):
			expctd_glbl_id = i + 1 #global ID starts at 1, enumerate starts at 0
			if block.global_id != expctd_glbl_id:
				print(f"Validation failed: Missing/deleted block at sequence {expctd_glbl_id}")
				return False
				
			state_mix = f"{calculated_state_root}{block.block_hash}" #acts like a merkle root hash
			calculated_state_root = hashlib.sha256(state_mix.encode()).hexdigest()
			
		#compare stored state root vs recalc state root
		if calculated_state_root != self.ledger_state_root:
			print("Ledger verification failed: Chain or block is missing")
			return False

		print("Ledger verified! ")
		print("State Root:", self.ledger_state_root)
		return True

#this function creates a state snapshot to send to another ledger node for validation checks
	def create_validation_checkpoint(self, validator_id, private_key):
		if not self.validate_ledger():
			return None

		checkpoint = {
			"validator_id": validator_id,
			"ledger_state_root": self.ledger_state_root,
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"signature": sign_hash(self.ledger_state_root, private_key)
		}

		return checkpoint

#This function is used by a receiving node when it receives a validation check from another
#node, Node A sends hash of itselfs and signature to Node B, Node B verifies it with this
#function
	def verify_validation_checkpoint(self, checkpoint, validator_public_key):
		received_root = checkpoint["ledger_state_root"]

		#debugging
		print("received_root:", repr(received_root))
		print("self root:    ", repr(self.ledger_state_root))
		print("received type:", type(received_root))
		print("self type:    ", type(self.ledger_state_root))
		print("equal?:       ", received_root == self.ledger_state_root)

		if received_root != self.ledger_state_root:
			print("Ledger state root mismatch")
			return False

		if not verify_hash_signature(
			received_root,
			checkpoint["signature"],
			validator_public_key
		):
			print("Validator signature invalid")
			return False

		print("Validation checkpoint verified")
		return True

	#print chains from ledger for debugging
	def print_chains(self):
		for evidence_id, blockchain in self.chains.items():
			print(f"\nChain for {evidence_id}:")

			for i, block in enumerate(blockchain.chain):
				print(f"  Block {i}")
				print(f"    action: {block.events}")
				print(f"    source: {block.source_type}")
				print(f"    signer_id: {block.signer_id}")
				print(f"    public_key: {block.public_key}")
				print(f"    signature: {block.signature}")
				print(f"    evidence_hash: {block.evidence_hash}")
				print(f"    local_block_id: {block.block_id}")      
				print(f"    global_id: {block.global_id}")           
				print(f"    previous_hash: {block.previous_hash}")
				print(f"    block_hash: {block.block_hash}")

	#simulates database
	def export_json(self, out_file):
		data = {}

		for evidence_id, blockchain in self.chains.items():
			data[evidence_id] = []

			for block in blockchain.chain:

				block_data = block.__dict__.copy()
				block_data["signature"] = str(block_data["signature"])
				data[evidence_id].append(block_data)

		with open(out_file, "w") as file:
			json.dump(data, file, indent=2)

	#simulates chain of custody actions for ledger creation or functions as database
	def import_json(self, in_file):
		with open(in_file, "r") as file:
			data = json.load(file)