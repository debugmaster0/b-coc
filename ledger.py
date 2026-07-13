import hashlib 
from block import Block 
from blockchain import Blockchain 
from sign_util import sign_hash, verify_hash_signature 
from datetime import datetime, timezone
import json

# The EvidenceLedger is a dictionary of evidence blockchains
# Each evidence ID is associated with a separate chain of custody, while
# global block IDs preserve block creation order in ledger
# Individual chains provide block integrity through hash links
# The ledger also maintains a SHA-256 state root hash calculated from
# every block hash in global creation order
class EvidenceLedger:
	def __init__(self):
		self.chains = {}
		self.ledger_state_root = "0" 
		self.global_block_count = 0  # Tracks absolute creation order

	def create_chain(self, evidence_id):
		#sub chains are tracked using evidence Id
		self.chains[evidence_id] = Blockchain()

# Adds a signed block to the appropriate evidence chain.
#
# 1. Reads the imported event data and obtains evidence ID.
# 2. Creates a new evidence chain if the evidence ID does not exist.
# 3. Calculates the next global block ID.
# 4. Retrieves the latest block from the target (target_block) evidence chain.
# 5. Creates a new block using the event, global ID, and previous block.
# 6. Signs the block hash and attaches the corresponding public key.
# 7. Appends the signed block to the target evidence chain.
# 8. Commits the new global block count.
# 9. Updates the ledger state hash.
	def add_block(self, event, private_key=None, public_key=None):
		evidence_id = event["evidence_id"]

		#if evidence is new, create new chain
		if evidence_id not in self.chains:
			self.create_chain(evidence_id)

		#adding block so global counter is increased (always greater than 0 if ledger exists)
		next_global_id = self.global_block_count + 1
		
		#find the chain the record belongs to and pull the last added block
		target_blockchain = self.chains[evidence_id]
		latest_block = target_blockchain.get_latest_block()

		#New Block creation
		#create block, global_block_count is passed into block for its global ID
		#latest block used to get hash
		new_block = Block(event, next_global_id, previous_block=latest_block)

		#adds signatures to block, see sign_util.py for sign_hash
		if private_key and public_key:
			new_block.signature = sign_hash(new_block.block_hash, private_key)
			new_block.public_key = public_key
		
		#append block
		target_blockchain.chain.append(new_block)

		self.global_block_count = next_global_id
		
		#This updates the state root hash for the ledger by adding new block hash to state root
		#and hashing it using sha256
		state_mix = f"{self.ledger_state_root}{new_block.block_hash}"
		self.ledger_state_root = hashlib.sha256(state_mix.encode()).hexdigest()

# Validates evidence ledger.
#
# 1. Rejects validation if the ledger contains no blocks
# 2. Calls validate_chain() for each blockchain to verify:
	# See blockchain.py for validate_chain()
# 3. Combine all blocks from every evidence chain into one list
# 4. Sort the combined list by global_id to reconstruct build order
# 5. Verifies that global IDs begin at 1 and remain sequential
# 6. Verifies each block's digital signature using its stored public key
# 7. Recalculates the ledger state root hash in global id order
# 8. Compares the recalculated state root hash with the stored ledger state root
# 9. Returns True only if every chain, block sequence, signature, and
#    ledger state value passes validation
	def validate_ledger(self):
		calculated_state_root = "0"
		all_blocks = []
		
		if self.global_block_count == 0:
			print("Ledger is empty. Import first.")
			return False
			
		#Validate individual chains accessed by evidence_id
		for evidence_id, blockchain in self.chains.items():

			if not blockchain.validate_chain():
				print(f"Invalid chain structural integrity: {evidence_id}")
				return False

			# create single list of ALL blocks, important to use global ID for sorting 
			all_blocks.extend(blockchain.chain)
			
		#sorts the extended list by global id
		#state root is estblished by hashing blocks FIFO, 
		#they are sorted by global_id to maintain that structure for hashing
		all_blocks.sort(key=lambda blk: blk.global_id)
		
		#Recalc state root in the exact order they were created
		for i, block in enumerate(all_blocks):
			expctd_glbl_id = i + 1 #global ID starts at 1, enumerate starts at 0

			if block.global_id != expctd_glbl_id:
				print(f"Validation failed: Missing/deleted block at sequence {expctd_glbl_id}")
				return False

			#for gui validation output
			signature_valid = verify_hash_signature(
				block.block_hash,
				block.signature,
				block.public_key
			)
			
			if not signature_valid:
				print(
					f"Validation failed: Invalid signature on "
					f"block {block.global_id}"
				)
				return False

			print(
				f"Block {block.global_id} | "
				f"Signer: {block.signer_id} | "
				f"Signature Verified "
			)
			print(f"-------VALID-------")

			#state mix is current state_root hash + block hash 
			state_mix = f"{calculated_state_root}{block.block_hash}" 
			calculated_state_root = hashlib.sha256(state_mix.encode()).hexdigest()
			
		#compare state root vs recalc final state root
		if calculated_state_root != self.ledger_state_root:
			print("Ledger verification failed: Chain or block is missing")
			return False

		print("Ledger verified! ")
		print("State Root:", self.ledger_state_root)
		return True

#this function creates a state snapshot to send to another ledger node for validation checks
#I did not utilize this feature in the gui
	def create_validation_checkpoint(self, validator_id, private_key):

		#no self ledger to verify
		if not self.validate_ledger():
			return None

		#checkpoint contains id of validator user
		#ledger state root
		#timestamp
		#and signed hash using validator user private key
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

		#if state roots don't match
		if received_root != self.ledger_state_root:
			print("Ledger state root mismatch")
			return False

		#if signature is not valid
		if not verify_hash_signature(
			received_root,
			checkpoint["signature"],
			validator_public_key
		):
			print("Validator signature invalid")
			return False

		#else all good
		print("Validation checkpoint verified")
		return True

	#print chains from ledger for debugging
	def print_chains(self):
		for evidence_id, blockchain in self.chains.items():
			print(f"\nChain for {evidence_id}:")

			for i, block in enumerate(blockchain.chain):
				print(f"  Block {i}")
				print(f"    action: {block.actions}")
				print(f"    source: {block.source_type}")
				print(f"    signer_id: {block.signer_id}")
				print(f"    public_key: {block.public_key}")
				print(f"    signature: {block.signature}")
				print(f"    evidence_hash: {block.evidence_hash}")
				print(f"    local_block_id: {block.block_id}")      
				print(f"    global_id: {block.global_id}")           
				print(f"    previous_hash: {block.previous_hash}")
				print(f"    block_hash: {block.block_hash}")

	#returns item chain from ledger
	def get_chain(self, evidence_id):
		return self.chains.get(evidence_id)

	#ledger export
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

	#simulates chain of custody actions for ledger creation
	def import_json(self, in_file):
		with open(in_file, "r") as file:
			data = json.load(file)


