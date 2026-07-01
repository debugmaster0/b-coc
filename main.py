from block import Block
from blockchain import Blockchain
from ledger import EvidenceLedger 
from sign_util import sign_hash, verify_hash_signature
from cryptography.hazmat.primitives.asymmetric import ec
import json


def main():

	private_key = ec.generate_private_key(ec.SECP256R1())
	public_key = private_key.public_key()

	ledger = EvidenceLedger()

	def import_events(in_file, ledger):
		with open(in_file, "r") as file:
			events = json.load(file)

		for event in events:
			ledger.add_block(event, private_key)

	#ledger2 = EvidenceLedger()

	'''ledger1.add_block(event1)
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
	print(ledger2.ledger_state_root)'''
	

	while True:
		print("\nEvidence Ledger Menu")
		print("1. Import ledger")
		print("2. Validate Ledger")
		print("3. Print Chains")
		print("4. Export JSON")
		print("5. Not in Use")
		print("6. Exit")

		choice = input("Select an option: ")

		if choice == "1":
			filename = input("Enter JSON filename: ")
			import_events(filename, ledger)

		elif choice == "2":
			ledger.validate_ledger()

		elif choice == "3":
			ledger.print_chains()

		elif choice == "4":
			print("Export JSON selected")
			filename = input("Export filename: ")
			ledger.export_json(filename)

		elif choice == "5":
			'''if ledger1.validate_ledger():
				checkpoint = ledger1.create_validation_checkpoint(
					ledger1.ledger_state_root,
					private_key
				)

				ledger2.verify_validation_checkpoint(
					checkpoint,
					public_key
				)'''
			print("Goodbye")
			break

			#else:
				#print("Ledger 1 is invalid. Checkpoint not created.")

		elif choice == "6":
			print("Goodbye")
			break

		else:
			print("Invalid selection")

if __name__ == "__main__":
	main()