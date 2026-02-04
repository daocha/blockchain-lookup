import hashlib
from solana.rpc.api import Client
from solders.pubkey import Pubkey

NAME_SERVICE_PROGRAM_ID = Pubkey.from_string("namesLPneUpt7WZvRBTBCqmb1pne1MkCcHmZ3vncKWH")
HASH_PREFIX = "Solana name service"

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

def main():
    client = Client("https://api.mainnet-beta.solana.com")
    # 'sol' TLD
    sol_hash = get_name_hash("sol")
    sol_tld = get_name_account_key(sol_hash, None, None)
    print(f"DEBUG: derived .sol TLD: {sol_tld}")
    
    # known .sol TLD
    known_sol = Pubkey.from_string("58P9EgQDuyfwP7F9fGf9L6asv9pABAnaa9AyFCfjkpf")
    print(f"DEBUG: known .sol TLD: {known_sol}")

if __name__ == "__main__":
    main()
