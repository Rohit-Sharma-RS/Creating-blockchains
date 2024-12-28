from flask import Flask, jsonify, request, render_template
import datetime
import hashlib
import json
from uuid import uuid4

class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof=1, previous_hash='0')

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash,
            'transactions': self.transactions
        }
        self.transactions = []
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while not check_proof:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:6] == '000000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    def add_transactions(self, sender, receiver, amount):
        self.transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        })
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    def get_chain(self):
        return self.chain

# Flask app initialization
app = Flask(__name__)

# Creating Blockchain instance
blockchain = Blockchain()

@app.route("/")
def index():
    """Serve the main frontend page."""
    return render_template("index_main.html")

@app.route("/mine_block", methods=["GET"])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transactions(sender="System", receiver=str(uuid4()), amount=1)
    block = blockchain.create_block(proof, previous_hash)
    response = {
        "message": "Congratulations, you just mined a block!",
        "block": block
    }
    return jsonify(response), 200   

@app.route("/get_chain", methods=["GET"])
def get_chain():
    response = {
        "chain": blockchain.get_chain(),
        "length": len(blockchain.get_chain())
    }
    return jsonify(response), 200

@app.route("/is_valid", methods=["GET"])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.get_chain())
    response = {"message": "The Blockchain is valid."} if is_valid else {"message": "The Blockchain is not valid."}
    return jsonify(response), 200

@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json for key in transaction_keys):
        return jsonify({"message": "Some elements are missing"}), 400
    index = blockchain.add_transactions(sender=json['sender'], receiver=json['receiver'], amount=json['amount'])
    response = {"message": f"This transaction will be added to block {index}"}
    return jsonify(response), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)
