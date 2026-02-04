import hashlib
from solana.rpc.api import Client
from solders.pubkey import Pubkey

NAME_SERVICE_PROGRAM_ID = Pubkey.from_string("namesLPneUpt7WZvRBTBCqmb1pne1MkCcHmZ3vncKWH")
HASH_PREFIX = "Solana name service"
KNOWN_SOL_TLD = Pubkey.from_string("58P9EgQDuyfwP7F9fGf9L6asv9pABAnaa9AyFCfjkpf")

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
    # 'bonfida'
    h = get_name_hash("\x00bonfida")
    k = get_name_account_key(h, None, KNOWN_SOL_TLD)
    print(f"DEBUG: k={k}")
    
    # Try one more: 'toly'
    h2 = get_name_hash("\x00toly")
    k2 = get_name_account_key(h2, None, KNOWN_SOL_TLD)
    print(f"DEBUG: toly.sol key={k2}")
    res = client.get_account_info(k2)
    if res.value:
        print("✅ toly.sol found")

if __name__ == "__main__":
    main()
