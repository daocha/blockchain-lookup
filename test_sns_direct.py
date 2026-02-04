import hashlib
from solana.rpc.api import Client
from solders.pubkey import Pubkey

NAME_SERVICE_PROGRAM_ID = Pubkey.from_string("namesLPneUpt7WZvRBTBCqmb1pne1MkCcHmZ3vncKWH")
HASH_PREFIX = "Solana name service"
ROOT_TLD = Pubkey.from_string("58P9EgQDuyfwP7F9fGf9L6asv9pABAnaa9AyFCfjkpf")

def get_name_hash(name: str):
    return hashlib.sha256((HASH_PREFIX + name).encode('utf-8')).digest()

def get_name_account_key(name_hash: bytes, name_class: Pubkey = None, parent_name: Pubkey = None):
    seeds = [
        name_hash,
        bytes(name_class) if name_class else bytes(32),
        bytes(parent_name) if parent_name else bytes(32)
    ]
    key, _ = Pubkey.find_program_address(seeds, NAME_SERVICE_PROGRAM_ID)
    return key

def test_bonfida():
    client = Client("https://api.mainnet-beta.solana.com")
    # 'bonfida' is a domain under '.sol' TLD
    # '.sol' TLD is a known root
    domain_hash = get_name_hash("bonfida")
    domain_key = get_name_account_key(domain_hash, None, ROOT_TLD)
    print(f"DEBUG: bonfida.sol key: {domain_key}")
    res = client.get_account_info(domain_key)
    if res.value:
        print(f"✅ bonfida.sol found!")
        print(f"Owner: {Pubkey.from_bytes(res.value.data[32:64])}")
    else:
        print(f"❌ bonfida.sol not found")

if __name__ == "__main__":
    test_bonfida()
