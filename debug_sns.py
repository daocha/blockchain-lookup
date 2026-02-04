import requests
import hashlib
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from construct import Struct, Int8byte, Int32ul, Bytes, Padding

# Constants for SNS
NAME_SERVICE_PROGRAM_ID = Pubkey.from_string("namesLPneUpt7WZvRBTBCqmb1pne1MkCcHmZ3vncKWH")
HASH_PREFIX = "Solana name service"

# Root domains (TLDs)
SOL_TLD = Pubkey.from_string("58P9EgQDuyfwP7F9fGf9L6asv9pABAnaa9AyFCfjkpf")
# We need to find the .skr root. Based on research, it's often a child of a specific root.
# Let's try to derive it or use a known one if found.
# Actually, the seeker ids might be subdomains of a specific root.

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

def resolve_sns(name: str, parent: Pubkey = None):
    client = Client("https://api.mainnet-beta.solana.com")
    name_hash = get_name_hash(name)
    name_account_key = get_name_account_key(name_hash, None, parent)
    print(f"DEBUG: Looking up {name} account: {name_account_key}")
    
    res = client.get_account_info(name_account_key)
    if res.value:
        # Simplified parsing of NameRegistry account
        # Header is 96 bytes: parent (32), owner (32), class (32)
        data = res.value.data
        owner = Pubkey.from_bytes(data[32:64])
        return owner
    return None

def main():
    # If msft.skr exists, 'skr' is the parent
    # Let's first try to find the 'skr' TLD account
    skr_tld_hash = get_name_hash("skr")
    skr_tld_key = get_name_account_key(skr_tld_hash, None, None)
    print(f"DEBUG: .skr TLD key candidate: {skr_tld_key}")
    
    # Try resolving msft with .skr parent
    # Note: the input name to hash is usually just the part before the dot for subdomains
    msft_hash = get_name_hash("msft")
    msft_skr_key = get_name_account_key(msft_hash, None, skr_tld_key)
    print(f"DEBUG: msft.skr account candidate: {msft_skr_key}")
    
    # Method 4: AllDomains TLD House lookup
    # AllDomains uses a different program but often integrates with SNS
    
    # Final check: Try a simple GET to a known explorer API that supports SNS
    try:
        url = f"https://api.solscan.io/tools/sns/resolve?name=msft.skr"
        # Solscan often blocks direct scripts, but let's see
        res = requests.get(url, timeout=10)
        print(f"Solscan Tool API: {res.status_code} - {res.text}")
    except:
        pass

if __name__ == "__main__":
    main()
