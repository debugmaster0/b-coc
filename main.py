from block import Block
from blockchain import Blockchain
from ledger import EvidenceLedger 
from cryptography.hazmat.primitives.asymmetric import ec


def main():

	private_key = ec.generate_private_key(ec.SECP256R1())
	public_key = private_key.public_key()

	event1 = {
	"evidence_id": "evidence_001",
	"device_id": "dev_3Ab6",
	"source_type": "bodycam",
	"evidence_hash": "a4jf9",
	"action": "evidence stored",
	"public_key": "key-001",
	"signature": private_key
	}

	event2 = {
		"evidence_id": "evidence_001",
		"signer_id": "officer_1",
		"source_type": "bodycam",
		"evidence_hash": "a4jf9",
		"action": "accessed",
		"public_key_signer": "key-002",
		"signature": private_key
	}

	event3 = {
		"evidence_id": "evidence_001",
		"signer_id": "officer_1",
		"source_type": None,
		"evidence_hash": "a4jf9",
		"action": "exported",
		"public_key_signer": "key-002",
		"signature": private_key
	}

	event4 = {
		"evidence_id": "evidence_002",
		"signer_id": "dev_45fw",
		"source_type": None,
		"evidence_hash": None,
		"action": "evidence stored",
		"public_key_signer": "key-003",
		"signature": private_key
	}

	event5 = {
		"evidence_id": "evidence_002",
		"signer_id": "officer_2",
		"source_type": None,
		"evidence_hash": None,
		"action": "downloaded",
		"public_key_signer": "key-004",
		"signature": private_key
	}

	private_key = ec.generate_private_key(ec.SECP256R1())
	public_key = private_key.public_key()
	'''event6 = {
		"evidence_id": "evidence_003",
		"signer_id": "officer_2",
		"source_type": None,
		"evidence_hash": None,
		"action": [
			{"action": "downloaded"},
			{"action": "exported"},
			{"action": "analyzed"},
			{"action": "copied"},
			{"action": "downloaded"}
		]
	}'''

	ledger1 = EvidenceLedger()
	ledger2 = EvidenceLedger()

	ledger1.add_block(event1)
	print(ledger1.ledger_state_root)
	ledger1.add_block(event2)
	print(ledger1.ledger_state_root)
	ledger1.add_block(event3)
	print(ledger1.ledger_state_root)
	ledger1.add_block(event4)
	print(ledger1.ledger_state_root)
	ledger1.add_block(event5)
	print(ledger1.ledger_state_root)

	ledger2.add_block(event1)
	print(ledger2.ledger_state_root)
	ledger2.add_block(event2)
	print(ledger2.ledger_state_root)
	ledger2.add_block(event3)
	print(ledger2.ledger_state_root)
	ledger2.add_block(event4)
	print(ledger2.ledger_state_root)
	ledger2.add_block(event5)
	print(ledger2.ledger_state_root)
	

	while True:
		print("\nEvidence Ledger Menu")
		print("1. Add Block")
		print("2. Validate Ledger 1")
		print("3. Print Chains")
		print("4. Export JSON")
		print("5. validate other ledger")
		print("6. Exit")

		choice = input("Select an option: ")

		if choice == "1":
			print("Add block selected")

		elif choice == "2":
			ledger1.validate_ledger()

		elif choice == "3":
			ledger1.print_chains()

		elif choice == "4":
			print("Export JSON selected")

		elif choice == "5":
			if ledger1.validate_ledger():
			    checkpoint = ledger1.create_validation_checkpoint(
			        ledger1.ledger_state_root,
			        private_key
			    )

			    ledger2.verify_validation_checkpoint(
			        checkpoint,
			        public_key
			    )


			else:
			    print("Ledger 1 is invalid. Checkpoint not created.")

		elif choice == "6":
			print("Goodbye")
			break

		else:
			print("Invalid selection")

if __name__ == "__main__":
	main()