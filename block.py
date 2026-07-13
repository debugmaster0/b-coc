# block.py
#
# Defines the Block object used by each evidence blockchain
# A block stores chain of custody event metadata, maintains a link to the
# previous block, and calculates a SHA-256 hash from its block header

import hashlib
import json
from datetime import datetime, timezone


class Block:
    # Creates a block from structured event data
    # event:
    #     Dictionary containing evidence and chain of custody metadata
    # global_id:
    #     Ledger sequence number representing the block's creation order in ledger
    # previous_block:
    #     Previous block in the evidence chain. Its local block ID
    #     and block hash are used to construct the new block's chain link
    def __init__(self, event, global_id, previous_block=None):
        self.global_id = global_id

        if previous_block is not None:
            # Local sequence number in evidence chain
            self.block_id = previous_block.block_id + 1

            # Cryptographic link to the previous block
            self.previous_hash = previous_block.block_hash
        else:
            # The first block in an evidence chain is the genesis block
            self.block_id = 1
            self.previous_hash = "0"

        # Evidence ID for chain tracking in ledger
        self.evidence_id = event["evidence_id"]

        # Human users provide signer_id, while automated sources provide
        # device_id. This identifies the source of the event
        self.signer_id = (
            event.get("signer_id")
            or event.get("device_id")
        )

        # Signature and public key are assigned by EvidenceLedger add_block()
        # after the block hash has been calculated
        self.signature = None
        self.public_key = None

        # Evidence source, such as body camera or CCTV
        self.source_type = event.get("source_type")

        # Hash of digital evidence represented by this block
        self.evidence_hash = event.get("evidence_hash")

        # Chain of custody custody action, such as collected, accessed, analyzed,
        # copied, stored, or transferred
        self.action = event.get("action")

        # Record the block creation time
        self.timestamp = datetime.now(timezone.utc).isoformat()

        # Calculate and store the SHA-256 hash of the block header
        self.block_hash = self.calculate_hash()

    # Creates a SHA-256 hash of the block header
    def calculate_hash(self):
        block_header = {
            "global_id": self.global_id,
            "block_id": self.block_id,
            "evidence_id": self.evidence_id,
            "signer_id": self.signer_id,
            "source_type": self.source_type,
            "evidence_hash": self.evidence_hash,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "action": self.action,
        }

        encoded_data = json.dumps(
            block_header,
            sort_keys=True
        ).encode()

        return hashlib.sha256(encoded_data).hexdigest()