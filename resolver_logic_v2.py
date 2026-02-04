import requests
import hashlib
from solana.rpc.api import Client
from solders.pubkey import Pubkey

# SNS and Seeker Constants
NAME_SERVICE_PROGRAM_ID = Pubkey.from_string("namesLPneUpt7WZvRBTBCqmb1pne1MkCcHmZ3vncKWH")
# Known TLD for .sol
SOL_TLD = Pubkey.from_string("58P9EgQDuyfwP7F9fGf9L6asv9pABAnaa9AyFCfjkpf")
# Seeker IDs (.skr) are integrated into SNS. Let's try to derive/find the SKR TLD.
# Often AllDomains roots are handled via specific registries.
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

def resolve_sns_direct(name: str):
    """Resolves a domain via direct on-chain SNS lookup."""
    client = Client("https://api.mainnet-beta.solana.com")
    parts = name.split(".")
    if len(parts) != 2: return None
    
    domain, tld = parts[0], parts[1]
    
    # 1. Resolve TLD account key
    # For .sol we use the known ROOT_TLD. For others, we might need to derive it.
    parent_key = SOL_TLD if tld == "sol" else None
    if not parent_key:
        # Try to derive TLD account if not known
        tld_hash = get_name_hash(tld)
        parent_key = get_name_account_key(tld_hash, None, None)

    # 2. Resolve Domain account key
    # SNS direct names usually have a \x00 prefix in the hash
    domain_hash = get_name_hash("\x00" + domain)
    domain_key = get_name_account_key(domain_hash, None, parent_key)
    
    res = client.get_account_info(domain_key)
    if res.value:
        # Header: parent(32), owner(32), class(32)
        return str(Pubkey.from_bytes(res.value.data[32:64]))
    
    # Try without prefix
    domain_hash_alt = get_name_hash(domain)
    domain_key_alt = get_name_account_key(domain_hash_alt, None, parent_key)
    res = client.get_account_info(domain_key_alt)
    if res.value:
        return str(Pubkey.from_bytes(res.value.data[32:64]))
        
    return None

def resolve_seeker_id(name: str):
    """
    Unified resolver for Seeker IDs (.skr) and SNS (.sol).
    Uses multiple fallback methods for maximum reliability.
    """
    if not ("." in name): return None
    
    # 1. Try SNS Proxy (most reliable for registered names)
    try:
        # Note: Seeker IDs are sometimes subdomains or handles
        url = f"https://sdk-proxy.sns.id/resolve/{name}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data.get("s") == "ok" and data.get("result"):
                return data["result"]
    except: pass

    # 2. Try Community Seeker Tracker (specific for .skr)
    if name.endswith(".skr"):
        try:
            # Community API often provides the mapping directly
            url = f"https://seeker-production-46ae.up.railway.app/api/v1/resolve/{name}"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                addr = res.json().get("address")
                if addr: return addr
        except: pass

    # 3. Direct On-chain lookup
    try:
        addr = resolve_sns_direct(name)
        if addr: return addr
    except: pass

    return None

if __name__ == "__main__":
    # Test with a dummy Seeker ID if possible, but mainly ensure the logic is sound.
    # The user provided 'msft.skr' as an example.
    print(f"Resolving msft.skr: {resolve_seeker_id('msft.skr')}")
