import asyncio
import threading
from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware
from web3.gas_strategies.rpc import rpc_gas_price_strategy
from web3.datastructures import AttributeDict
from siwe import SiweMessage, generate_nonce
from django.conf import settings

import pprint

import os, json
from pathlib import Path


w3 = None
contract = None
acc = None


def setup_web3():
    global w3, contract, acc
    
    if not w3 or not contract:
        private_key = os.environ.get("PRIVATE_KEY")
        provider_url = "https://sepolia.infura.io/v3/4645cea3156340028cc4f51b73bbef5a" # os.environ.get("PROVIDER_URL")
        contract_address = "0x9fB42230C66C04e1E468b728e8177D4C97965392"
        w3 = Web3(Web3.HTTPProvider(provider_url))
        acc = w3.eth.account.from_key(private_key)
        w3.middleware_onion.add(construct_sign_and_send_raw_middleware(acc))
        w3.eth.default_account = acc.address
        # w3.eth.set_gas_price_strategy(rpc_gas_price_strategy)

        abi_path = f"{Path(__file__).resolve().parent}/abi.json"
        with open(abi_path, "r") as abi_file:
            abi = json.load(abi_file)
            contract = w3.eth.contract(address=contract_address, abi=abi)
        print("set up web3 successfully!")

        # event_loop_thread = threading.Thread(target=listen_to_event)
        # event_loop_thread.start()

        # print("-default address:", acc.address)
        # print("-contract address:", contract_address)

    return (w3, contract)


def read_test(address):
    return contract.functions.NFTList(address).call()  # block_identifier='latest'


def get_tokenId():
    return contract.functions.getTokenId().call()  # block_identifier='latest'


def mint_test(to, logs):
    nonce = w3.eth.get_transaction_count(acc.address)
    token_id = get_tokenId()
    # gp = w3.eth.generate_gas_price()
    # print( contract.functions.mint(acc.address).estimate_gas(...))

    tx_hash = contract.functions.mint(to, logs).transact(
        {
            "nonce": nonce,
        }
    )

    hash = tx_hash.hex()
    print(f"hash: {hash}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    def toHex(value):
        if isinstance(value, bytes):
            return value.hex()
        elif isinstance(value, AttributeDict):
            return {k: toHex(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [toHex(v) for v in value]
        else:
            return value

    _receipt = {}
    for key, value in receipt.items():
        _receipt[key] = toHex(value)

    pprint.pprint(_receipt)

    return {
        "status": receipt.status,
        "hash": hash,
        "link": f"https://sepolia.etherscan.io/tx/{hash}",
        "token_id": token_id,
    }


def generate_random_ethereum_address():
    w3 = Web3()
    private_key = w3.eth.account.create()._private_key.hex()
    account = w3.eth.account.from_key(private_key)
    address = account.address
    return address

    # nonce = request.session['nonce']
    # siweMessage.verify(signature, nonce=user.nonce)
    # del request.session['nonce'] or generate_nonce()
