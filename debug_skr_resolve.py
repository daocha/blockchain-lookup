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

def resolve_domain(name: str):
    client = Client("https://api.mainnet-beta.solana.com")
    parts = name.split(".")
    if len(parts) != 2:
        return None
    
    domain, tld = parts[0], parts[1]
    
    # 1. Resolve TLD account key
    tld_hash = get_name_hash(tld)
    tld_key = get_name_account_key(tld_hash, None, None)
    print(f"DEBUG: TLD {tld} key: {tld_key}")

    # 2. Resolve Domain account key
    # SNS uses a \x00 prefix for the domain hash if it's a child of a TLD
    domain_hash = get_name_hash("\x00" + domain)
    domain_key = get_name_account_key(domain_hash, None, tld_key)
    print(f"DEBUG: Domain {domain} key: {domain_key}")
    
    res = client.get_account_info(domain_key)
    if res.value:
        # Header: parent(32), owner(32), class(32)
        # The owner starts at byte 32
        owner = Pubkey.from_bytes(res.value.data[32:64])
        return str(owner)
    
    # Fallback: try without \x00 prefix (some protocols differ)
    domain_hash_alt = get_name_hash(domain)
    domain_key_alt = get_name_account_key(domain_hash_alt, None, tld_key)
    res = client.get_account_info(domain_key_alt)
    if res.value:
        owner = Pubkey.from_bytes(res.value.data[32:64])
        return str(owner)
        
    return None

if __name__ == "__main__":
    sid = "msft.skr"
    addr = resolve_domain(sid)
    if addr:
        print(f"✅ {sid} -> {addr}")
    else:
        print(f"❌ {sid} failed to resolve")
