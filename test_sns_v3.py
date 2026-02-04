import hashlib
from solana.rpc.api import Client
from solders.pubkey import Pubkey

NAME_SERVICE_PROGRAM_ID = Pubkey.from_string("namesLPneUpt7WZvRBTBCqmb1pne1MkCcHmZ3vncKWH")
HASH_PREFIX = "Solana name service"
KNOWN_SOL_TLD = Pubkey.from_string("58P9EgQDuyfwP7F9fGf9L6asv9pABAnaa9AyFCfjkpf")

def get_name_hash(name: str):
    # SNS uses SHA256 of (HASH_PREFIX + name)
    return hashlib.sha256((HASH_PREFIX + name).encode('utf-8')).digest()

def get_name_account_key(name_hash: bytes, name_class: Pubkey = None, parent_name: Pubkey = None):
    # For subdomains, name_class is usually zero, parent is the TLD or parent domain
    seeds = [
        name_hash,
        bytes(name_class) if name_class else bytes(32),
        bytes(parent_name) if parent_name else bytes(32)
    ]
    key, _ = Pubkey.find_program_address(seeds, NAME_SERVICE_PROGRAM_ID)
    return key

def test_bonfida():
    client = Client("https://api.mainnet-beta.solana.com")
    # bonfida.sol
    # name_hash is SHA256("Solana name service" + "\x00" + "bonfida")
    # Actually, the hashing logic for subdomains can be tricky. 
    # For a direct domain under TLD, it is:
    # seeds = [sha256(prefix + name), zero_class, tld_key]
    
    name = "bonfida"
    name_hash = get_name_hash("\x00" + name) # Common pattern for SNS handles/domains
    key = get_name_account_key(name_hash, None, KNOWN_SOL_TLD)
    print(f"DEBUG: bonfida.sol key (hashed with \\x00): {key}")
    
    res = client.get_account_info(key)
    if res.value:
        print(f"✅ bonfida.sol found with \\x00 prefix!")
        return

    name_hash_no_prefix = get_name_hash(name)
    key_no_prefix = get_name_account_key(name_hash_no_prefix, None, KNOWN_SOL_TLD)
    print(f"DEBUG: bonfida.sol key (no prefix): {key_no_prefix}")
    res = client.get_account_info(key_no_prefix)
    if res.value:
        print(f"✅ bonfida.sol found with no prefix!")

if __name__ == "__main__":
    test_bonfida()
