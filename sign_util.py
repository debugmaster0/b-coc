#sign_util.py

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

#signs ledger produces root hash
def sign_hash(hash_value, private_key):
	signature = private_key.sign(
		hash_value.encode(),
		ec.ECDSA(hashes.SHA256())
	)
	return signature.hex()

#utilizes sender public key to verify signature attached to validation check
def verify_hash_signature(hash_value, signature_hex, public_key):
	try:
		public_key.verify(
			bytes.fromhex(signature_hex),
			hash_value.encode(),
			ec.ECDSA(hashes.SHA256())
		)
		return True
	except Exception:
		return False