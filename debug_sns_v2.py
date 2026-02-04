import requests
import hashlib
from solana.rpc.api import Client
from solders.pubkey import Pubkey

# Constants for SNS
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
    
    # msft.skr
    # Step 1: Find 'skr' account (TLD)
    skr_hash = get_name_hash("skr")
    skr_tld_key = get_name_account_key(skr_hash, None, None)
    print(f"DEBUG: .skr TLD key: {skr_tld_key}")
    
    # Step 2: Find 'msft' subdomain account under 'skr'
    msft_hash = get_name_hash("msft")
    msft_skr_key = get_name_account_key(msft_hash, None, skr_tld_key)
    print(f"DEBUG: msft.skr key: {msft_skr_key}")
    
    res = client.get_account_info(msft_skr_key)
    if res.value:
        data = res.value.data
        # Header: parent (32), owner (32), class (32)
        owner = Pubkey.from_bytes(data[32:64])
        print(f"✅ msft.skr resolved to owner: {owner}")
    else:
        print(f"❌ msft.skr account not found")

    # Try goog.skr
    goog_hash = get_name_hash("goog")
    goog_skr_key = get_name_account_key(goog_hash, None, skr_tld_key)
    res = client.get_account_info(goog_skr_key)
    if res.value:
        data = res.value.data
        owner = Pubkey.from_bytes(data[32:64])
        print(f"✅ goog.skr resolved to owner: {owner}")
    else:
        print(f"❌ goog.skr account not found")

if __name__ == "__main__":
    main()
