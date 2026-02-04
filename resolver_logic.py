import requests
import hashlib
from solana.rpc.api import Client
from solders.pubkey import Pubkey

# Constants
NAME_SERVICE_PROGRAM_ID = Pubkey.from_string("namesLPneUpt7WZvRBTBCqmb1pne1MkCcHmZ3vncKWH")
TLD_HOUSE_PROGRAM_ID = Pubkey.from_string("TLDHkysf5pCnKsVA4gXpNvmy7psXLPEu4LAdDJthT9S")
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

def resolve_sns(name: str):
    client = Client("https://api.mainnet-beta.solana.com")
    if "." not in name: return None
    
    parts = name.split(".")
    domain = parts[0]
    tld = parts[1]
    
    # Get TLD account
    tld_hash = get_name_hash(tld)
    tld_key = get_name_account_key(tld_hash, None, None)
    
    # Get domain account
    domain_hash = get_name_hash(domain)
    domain_key = get_name_account_key(domain_hash, None, tld_key)
    
    res = client.get_account_info(domain_key)
    if res.value:
        # Data structure: parent(32), owner(32), class(32)
        return str(Pubkey.from_bytes(res.value.data[32:64]))
    return None

def resolve_seeker_id(name: str):
    """
    Main resolution function for Seeker ID.
    Supports .skr domains via multiple fallback methods.
    """
    if not name.endswith(".skr"):
        return None
    
    # 1. Try SNS Proxy (Common for registered names)
    try:
        url = f"https://sdk-proxy.sns.id/resolve/{name}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get("s") == "ok" and data.get("result"):
                return data["result"]
    except: pass

    # 2. Try SNS Direct Resolution
    try:
        addr = resolve_sns(name)
        if addr: return addr
    except: pass

    # 3. Known Seeker Tracker (Publicly shared for .skr)
    try:
        url = f"https://seeker-production-46ae.up.railway.app/api/v1/resolve/{name}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return res.json().get("address")
    except: pass

    return None

def test():
    # Since I don't have a verified registered .skr ID, 
    # I will use a known .sol one to prove the logic works for SNS,
    # then include the .skr specific logic.
    test_names = ["bonfida.sol", "msft.skr"]
    for name in test_names:
        addr = resolve_seeker_id(name) if ".skr" in name else resolve_sns(name)
        print(f"{name} -> {addr}")

if __name__ == "__main__":
    test()
