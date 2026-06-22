from block import Block

class Blockchain: 
    def __init__(self):
        self.chain = []

    #returns last block in local chain
    def get_latest_block(self):
        if not self.chain:
            return None
        return self.chain[-1]


    #validates chain by recalc and compare hash, 
    #as well as current blocks previous hash with previous block hash
    def validate_chain(self):
        if len(self.chain) == 0:
            return True 

        for i in range(len(self.chain)):
            current_block = self.chain[i]

            #verify current hash
            if current_block.block_hash != current_block.calculate_hash():
                print(f"Tampered data found at Local Block ID: {current_block.block_id}")
                return False

            #if actual chain, not genisis node, check hash link and block_id sequence
            if i > 0:
                previous_block = self.chain[i - 1]

                #verify previous hash with stored previous hash
                if current_block.previous_hash != previous_block.block_hash:
                    print(f"Broken link at Local Block ID: {current_block.block_id}")
                    return False
 
                #verify sequence of block_id (no missing IDs or alterations)
                if current_block.block_id != previous_block.block_id + 1:
                    print(f"Index sequence broken at Local Block ID: {current_block.block_id}")
                    return False
            else:
                #genisis block should be 0 prev hash or 1 block ID
                if current_block.previous_hash != "0" or current_block.block_id != 1:
                    print("Genesis block structure corrupted")
                    return False

        return True
