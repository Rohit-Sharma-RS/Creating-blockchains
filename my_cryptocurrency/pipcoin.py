import datetime
import hashlib
import json
from flask import jsonify, Flask
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Building the blockchain using a class
class Blockchain:
    def __init__(self) -> None:
        self.chain = []
        self.transactions = []
        self.create_block(proof=1, previous_hash='0')

    def create_block(self, proof, previous_hash):
        block = {
                'index': len(self.chain)+1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'transactions': self.transactions
                }
        self.transactions = [] # only once does transactions get added then gets empty
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    # Let's create the proof of work
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False

        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == "0000":
                check_proof = True
            else:
                new_proof += 1 # so he checks new proof and tries to mine using this new_proof
        return new_proof
    
    def hash_it(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    # is this a valid proof of work
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            # for each block next hash  = previous hash
            # proof of work is valid
            block = chain[block_index]
            if block["previous_hash"] != self.hash_it(previous_block):
                return False
            previous_proof = previous_block["proof"]
            proof = block["proof"]
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index+=1
        return True
    
    def add_transactions(self, sender, receiver, amount):
        self.transactions.append({'sender': sender,
                                  'receiver': receiver,
                                  'amount': amount})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f"http://{node}/get_chain")
            if response == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length>max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain   
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

    
# Mining our blockchain

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

node_address = str(uuid4()).replace("-", "")
blockchain = Blockchain()

@app.route("/mine_block", methods=["GET"])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash_it(previous_block)
    blockchain.add_transactions(sender=node_address, receiver='Rohit', amount=1)
    block = blockchain.create_block(proof, previous_hash=previous_hash) # ab new block banana
    response = {'Message': 'Congratulations you mined a block it is your now!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200

@app.route("/get_chain", methods = ["GET"])
def get_chain():
    response = {'Chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

@app.route('/is_valid', methods = ['GET'])
def valid_chain():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid==True:
        response={'message': 'Alright the blockchain is valid'}
    else:
        response={"message": 'Oh no Blockchain is invalid!'}
    return jsonify(response), 200

# Add a new transaction to the blockchain
@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    json = requests.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all (key in json for key in transaction_keys):
        return "Some elements are missing",400
    index = blockchain.add_transactions(sender = json['sender'], 
                                        receiver=json['receiver'],
                                        amount=json['amount']) 
    response = {"message": f"This transaction will be added to block {index}"}
    return response, 201

# decentralizing the blockchain
@app.route('connet_node', methods=["POST"])
# json = {"nodes": ["http://127.5000". "http://127.5001" etc]
def connect_node():
    json = requests.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(address=node)
    response = {'message': "All nodes are connected. The Pipcoin contains following nodes",
                'total_nodes': list(blockchain.nodes)}
    return response, 200

@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced==True:
        response={'message': 'The chain is replaced by longest one.',
                  'new_chain': blockchain.chain}
    else:
        response={"message": 'All good the chain is the largest one!',
                  'actual_chain':blockchain.chain}
    return jsonify(response), 200

if __name__ == "__main__":
    app.run(port=8000, debug=True)