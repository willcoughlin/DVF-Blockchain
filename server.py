""" This module acts as a single node in the network. """

import sys

from uuid import uuid4
from flask import Flask, jsonify, request

from blockchain import Blockchain

app = Flask(__name__)  # Instantiate our node
node_identifier = str(uuid4()).replace("-", "")  # Generate a UUID for the node

blockchain = Blockchain()  # Instantiate the blockchain

@app.route("/mine", methods=["GET"])
def mine():
    """ Mines a block. """

    # We run the proof of work algorithm to get the next proof
    last_block = blockchain.last_block
    last_proof = last_block["proof"]
    proof = blockchain.proof_of_work(last_proof)

    # We must revieve an award for finding the proof.
    # The sender is "0" to signify this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1
    )

    # Forge new block and add to chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        "message": "New block forged",
        "index": block["index"],
        "transactions": block["transactions"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"]
    }
    return (jsonify(response), 200)  # Return new block info and 200 OK status

@app.route("/transactions/new", methods=["POST"])
def new_transaction():
    """ Posts a new transaction to the next block. """

    values = request.get_json()

    # Check that the required fields are in the POST data
    required = ["sender", "recipient", "amount"]
    if not all(k in values for k in required):
        # Return a 400 Bad Request error if not all required values found
        return ("Missing values", 400)

    # Create a new transaction
    index = blockchain.new_transaction(
        values["sender"],
        values["recipient"],
        values["amount"]
    )

    response = {"message": f"Transaction will be added to block #{index}"}
    return (jsonify(response), 201)  # Return response with 201 Created status

@app.route("/chain", methods=["GET"])
def full_chain():
    """ Gets the full blockchain. """

    response = {
        "chain": blockchain.chain,
        "length": len(blockchain.chain)
    }
    return (jsonify(response), 200)  # Return response with 200 OK status

@app.route("/nodes/register", methods=["POST"])
def register_nodes():
    """ Registers neighboring nodes to blockchain instance. """

    values = request.get_json()
    nodes = values.get("nodes")
    if nodes is None:
        # If no nodes supplied, return 400 Bad Request
        return ("Error: Please supply a valid list of nodes", 400)

    for node in nodes:
        blockchain.register_node(node)

    response = {
        "message": "New nodes have been added",
        "totalNodes": list(blockchain.nodes)
    }
    return (jsonify(response), 201)  # Response message and 201 Created status

@app.route("/nodes/resolve")
def consensus():
    """ Resolves conflicts between this and neighboring nodes. """

    was_blockchain_replaced = blockchain.resolve_conflicts()
    if was_blockchain_replaced:
        response = {
            "message": "Our chain was replaced",
            "newChain": blockchain.chain
        }
    else:
        response = {
            "message": "Our chain is authoritative",
            "chain": blockchain.chain
        }

    return (jsonify(response), 200)  # Response and 200 OK status

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=(5000 if len(sys.argv) < 2 else int(sys.argv[1])))
