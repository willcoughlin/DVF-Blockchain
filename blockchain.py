""" This module contains the core blockchain implementation. """

import hashlib
import json

import requests

from time import time
from urllib.parse import urlparse


class Blockchain(object):
    """ This class represents the blockchain itself. """

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a block.

        :param block: <dict> Block to hash

        :return: <str> Block hash
        """

        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
    def is_valid_proof(last_proof, proof):
        """
        Validates a proof. Checks that hash result contains 4 leading zeroes.

        :param last_proof: <int> Previous proof solution
        :param proof: <int> Current proof

        :return: <bool> True if valid, False otherwise
        """

        guess = f"{last_proof}{proof}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        return guess_hash[:4] == "0000"

    @property
    def last_block(self):
        """
        Gets the last block in the chain.

        :return: <dict> Last block
        """
        return self.chain[-1]

    def __init__(self):
        """ Constructor. """

        self.chain = []
        self.current_transactions = []

        self.nodes = set()

        self.new_block(proof=100, previous_hash=1)  # Create the genesis block

    def new_block(self, proof, previous_hash=None):
        """
        Creates a new block and adds it to the chain.

        :param proof: <int> The proof given by the proof of work algorithm
        :param previous_hash: (Optional) <str> Hash of the previous block

        :return: <dict> New
        """

        block = {
            "index": len(self.chain) + 1,
            "timestamp": time(),
            "transactions": self.current_transactions,
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.chain[-1])
        }

        self.current_transactions = []  # Reset current list of transactions

        self.chain.append(block)
        return block

    def proof_of_work(self, last_proof):
        """
        Simple proof of work algorithm. Find a number p' such that hash(pp')
        contains 4 leading zeroes, where p is the previous proof.

        :param last_proof: <int> Last proof solution

        :return: <int> Proof of work solution
        """

        proof = 0
        while not self.is_valid_proof(last_proof, proof):
            proof += 1

        return proof

    def new_transaction(self, sender, recipient, amount):
        """
        Adds a new transaction to go into the next mined block.

        :param sender: <str> Address of the sender
        :param recipient: <str> Address of the recipient
        :param amount: <int> Amount

        :return: <int> the index of the block that will hold this transaction
        """

        self.current_transactions.append({
            "sender": sender,
            "recipient": recipient,
            "amount": amount
        })

        return self.last_block["index"] + 1

    def register_node(self, address):
        """
        Adds a new node to the list of nodes.

        :param address: <str> Address of the new node.
            E.g., "http://192.168.0.5:5000"
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def is_valid_chain(self, chain):
        """
        Determines if a given blockchain is valid.

        :param chain: <list> A blockchain

        :return: <bool> True if valid, False otherwise
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            print(last_block)
            print(block)
            print("\n-----------\n")

            # Check that the hash of the block is correct
            if block["previous_hash"] != self.hash(last_block):
                return False

            # Check that proof of work is correct
            if not self.is_valid_proof(last_block["proof"], block["proof"]):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        Consensus algorithm. Resolves conflicts by replacing chain with the
        longest one on the network.

        :return: <bool> True if our chain was replaced, False otherwise
        """

        neighbors = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Verify chains from all nodes on network
        for node in neighbors:
            response = requests.get(f"http://{node}/chain")

            if response.status_code == 200:
                length = response.json()["length"]
                chain = response.json()["chain"]

                # Check if length is longer and chain is valid
                if length > max_length and self.is_valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False;