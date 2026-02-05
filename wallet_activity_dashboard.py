# Ethereum + Solana + Hyperliquid + 名人下拉選單

import requests
import streamlit as st
import pandas as pd
import base58
import ssl
import time
import os
import hashlib
from datetime import datetime
from web3 import Web3
from dotenv import load_dotenv
from solana.rpc.api import Client as SolanaClient
from solders.pubkey import Pubkey
from known_wallets import KNOWN_WALLETS

# ---------------- CONFIG ----------------
load_dotenv()
ETHERSCAN_API_KEY = os.getenv("ETH_API_KEY")
INFURA_API = os.getenv("INFURA_API_URL")
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")

# SNS/Seeker Constants
NAME_SERVICE_PROGRAM_ID = Pubkey.from_string("namesLPneUpt7WZvRBTBCqmb1pne1MkCcHmZ3vncKWH")
SOL_TLD = Pubkey.from_string("58P9EgQDuyfwP7F9fGf9L6asv9pABAnaa9AyFCfjkpf")
HASH_PREFIX = "Solana name service"

# AllDomains (Seeker .skr) Constants
ALL_DOMAINS_PROGRAM_ID = Pubkey.from_string("ALTNSZ46uaAUU7XUV6awvdorLGqAsPwa9shm7h4uP2FK")
SKR_PARENT = Pubkey.from_string("F3A8kuikEiu6k2399oSJ1PWfcJYDHqpwoQ2e8psSDNuF")
ALL_DOMAINS_HASH_PREFIX = "ALT Name Service"

# Validate API keys
if not ETHERSCAN_API_KEY:
    st.error("❌ Missing ETH_API_KEY in .env file")
    st.stop()
if not INFURA_API:
    st.error("❌ Missing INFURA_API_URL in .env file")
    st.stop()
if not HELIUS_API_KEY:
    st.warning("⚠️ Missing HELIUS_API_KEY in .env file - Solana transactions will not work")

w3 = Web3(Web3.HTTPProvider(INFURA_API))

# ---------------- ADDR & CONSTANTS ----------------
ETH_STAKING_CONTRACTS = {
    "0x00000000219ab540356cbb839cbe05303d7705fa": "ETH2 Deposit",
    "0xae7ab96520de3a18e5e111b5eaab095312d7fe84": "Lido stETH",
    "0x1643e812ae58766192cf7d2cf9567df2c37e9b7f": "Rocket Pool rETH",
    "0xdfe66b14d37c77f4e9b180ceb433d1b164f0281d": "Stakewise sETH2",
    "0xc874b064f465bdd6411d45734b56fac750cda29a": "Coinbase Wrapped Staked ETH",
}

SOL_WSOL_MINT = "So11111111111111111111111111111111111111112"

SOL_STAKING_ENTITIES = {
    "Stake11111111111111111111111111111111111111",  # Native Solana staking
    "SKRskrmtL83pcL4YqLWt6iPefDqwXQWHSw9S9vz94BZ",  # SKR Staking
    "SKRuTecmFDZHjs2DxRTJNEK7m7hunKGTWJiaZ3tMVVA",  # Solana Mobile validator
    "MarBmsSgKXdrN1egZf5sqe1TMai9K1rChYNDJgjq7aD",  # Marinade Finance
    "StkitLLhKKPjPzBJTCLSJYUDVxqDiPJUdCQPKJqvLKK",  # Lido on Solana
    "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn",  # Jito staking
    "CREAMpdW4kfKTfFMtTBLqb5tQG5mvXeGAibnqjVCT2Qv",  # Cream Finance
    "4HQy82s9CHTv1GsYKnANHMiHfhcqesYkK6sB3RDSYyqw",  # SKR staking pool
    SOL_WSOL_MINT, # WSOL is often involved in staking/unstaking
}




# Known wallets imported from known_wallets.py
known_wallets = KNOWN_WALLETS

# ============================================================
# Helper functions
# ============================================================
def detect_address_type(addr: str):
    addr = addr.strip()
    
    # Check Bitcoin addresses first (more specific patterns)
    # Legacy P2PKH (starts with 1)
    if addr.startswith('1') and 26 <= len(addr) <= 35:
        return "bitcoin"
    # P2SH (starts with 3)
    if addr.startswith('3') and 26 <= len(addr) <= 35:
        return "bitcoin"
    # Bech32 SegWit (starts with bc1)
    if addr.lower().startswith('bc1') and 42 <= len(addr) <= 62:
        return "bitcoin"
    
    # Check Ethereum (0x + 40 hex chars)
    if addr.lower().startswith("0x") and len(addr) == 42:
        return "ethereum"
    
    # Check Solana (base58, 32-44 chars)
    try:
        # Base58 check might fail if it's a domain name (contains dots or invalid chars)
        if "." not in addr:
            base58.b58decode(addr)
            if 32 <= len(addr) <= 44:
                return "solana"
    except Exception:
        pass
    
    # Check Seeker ID (.skr), SNS (.sol) or ENS (.eth)
    if addr.lower().endswith((".skr", ".sol")):
        return "seeker"
    
    if addr.lower().endswith(".eth"):
        return "ethereum_ens"
    
    return None


def resolve_ens(name_or_addr: str):
    """解析 ENS 名稱為以太坊地址"""
    if not name_or_addr.endswith(".eth"):
        return name_or_addr
    
    # Try fallback to API resolution
    try:
        res = requests.get(f"https://api.ensideas.com/ens/resolve/{name_or_addr}", timeout=10)
        data = res.json()
        if "address" in data and data["address"]:
            return data["address"]
    except Exception:
        pass
    
    return None


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
    """Resolves a domain via direct on-chain SNS lookup (Bonfida & AllDomains)."""
    client = SolanaClient("https://api.mainnet-beta.solana.com")
    parts = name.split(".")
    if len(parts) != 2: return None
    
    domain, tld = parts[0], parts[1]
    
    # 1. Handle AllDomains (.skr, etc.)
    if tld == "skr":
        try:
            hashed_name = hashlib.sha256((ALL_DOMAINS_HASH_PREFIX + domain).encode('utf-8')).digest()
            seeds = [hashed_name, bytes(32), bytes(SKR_PARENT)]
            domain_key, _ = Pubkey.find_program_address(seeds, ALL_DOMAINS_PROGRAM_ID)
            res = client.get_account_info(domain_key)
            if res.value:
                # Owner starts at offset 40 (disc 8 + parent 32)
                return str(Pubkey.from_bytes(res.value.data[40:72]))
        except: pass
    
    # 2. Handle Standard SNS (.sol)
    try:
        parent_key = SOL_TLD if tld == "sol" else get_name_account_key(get_name_hash(tld), None, None)

        # Try standard SNS prefix (\x00)
        domain_hash = get_name_hash("\x00" + domain)
        domain_key = get_name_account_key(domain_hash, None, parent_key)
        
        res = client.get_account_info(domain_key)
        if res.value:
            return str(Pubkey.from_bytes(res.value.data[32:64]))
        
        # Try no prefix
        domain_hash_alt = get_name_hash(domain)
        domain_key_alt = get_name_account_key(domain_hash_alt, None, parent_key)
        res = client.get_account_info(domain_key_alt)
        if res.value:
            return str(Pubkey.from_bytes(res.value.data[32:64]))
    except: pass
        
    return None


def resolve_seeker_id(name: str):
    """
    Unified resolver for Seeker IDs (.skr) and SNS (.sol).
    Uses AllDomains direct lookup for .skr and SNS Proxy/Direct for others.
    """
    if not ("." in name): return None
    
    # 1. Direct AllDomains Lookup for .skr (Most reliable)
    if name.endswith(".skr"):
        resolved = resolve_sns_direct(name)
        if resolved: return resolved

    # 2. Try SNS Proxies
    try:
        proxies = [
            f"https://sns-sdk-proxy.bonfida.workers.dev/resolve/{name}",
            f"https://sdk-proxy.sns.id/resolve/{name}"
        ]
        for url in proxies:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if data.get("s") == "ok" and data.get("result"):
                    return data["result"]
    except: pass

    # 3. Try Community Seeker Tracker
    if name.endswith(".skr"):
        try:
            url = f"https://seeker-production-46ae.up.railway.app/api/v1/resolve/{name}"
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                addr = res.json().get("address")
                if addr: return addr
        except: pass

    # 4. Fallback to direct resolution
    try:
        return resolve_sns_direct(name)
    except: pass

    return None

    return None




def safe_post_json(url, payload, retries=3):
    """安全呼叫 Hyperliquid API"""
    for _ in range(retries):
        try:
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200 and res.text.strip():
                return res.json()
        except Exception:
            pass
        time.sleep(1)
    return None


# ============================================================
# Hyperliquid
# ============================================================
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_hyperliquid_positions(addr_or_seeker):
    url = "https://api.hyperliquid.xyz/info"
    payload = (
        {"type": "clearinghouseStateSeeker", "seeker": addr_or_seeker}
        if addr_or_seeker.endswith(".skr") or addr_or_seeker.lower().startswith("seeker")
        else {"type": "clearinghouseState", "user": addr_or_seeker}
    )
    return safe_post_json(url, payload)


def render_hyperliquid_positions(data):
    if not data or "assetPositions" not in data or not data["assetPositions"]:
        st.info("📭 目前沒有倉位資料")
        return

    rows = []
    for p in data["assetPositions"]:
        pos = p["position"]
        symbol = pos.get("coin", "N/A")
        side = "多單 🟢" if float(pos.get("szi", 0)) > 0 else "空單 🔴"

        lev_info = pos.get("leverage", {})
        if isinstance(lev_info, dict):
            lev_val = lev_info.get("value", "—")
            lev_type = lev_info.get("type", "")
            leverage = f"{lev_val}x ({lev_type.capitalize()})"
        else:
            leverage = f"{lev_info}x" if lev_info != "—" else "—"

        entry = float(pos.get("entryPx", 0))
        mark = float(pos.get("markPx", entry))
        pnl = float(pos.get("unrealizedPnl", 0))
        pnl_pct = ((mark - entry) / entry * 100) if entry > 0 else 0
        liq = pos.get("liqPx", "—")

        rows.append({
            "幣種": symbol,
            "方向": side,
            "開倉均價": f"{entry:,.2f}",
            "現價": f"{mark:,.2f}",
            "盈虧率": f"{pnl_pct:+.2f}%",
            "未實現盈虧 (USD)": f"{pnl:,.2f}",
            "槓桿": leverage,
            "爆倉價": liq if liq != "—" else "—",
        })

    df = pd.DataFrame(rows)

    def color_pnl(val):
        try:
            num = float(val.replace("%", "").replace(",", ""))
            if num > 0:
                return "color: #00ff00; font-weight: bold"
            elif num < 0:
                return "color: #ff4d4d; font-weight: bold"
        except:
            pass
        return "color: #e0e0e0"

    st.markdown("### 📊 Hyperliquid 倉位概覽")
    st.dataframe(df.style.map(color_pnl, subset=["盈虧率", "未實現盈虧 (USD)"]))


# ============================================================
# Ethereum Transactions
# ============================================================
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_eth_transactions_detailed(address):
    base = "https://api.etherscan.io/v2/api"
    txs, tokens = [], []
    params_eth = {
        "chainid": 1,
        "module": "account",
        "action": "txlist",
        "address": address,
        "page": 1,
        "offset": 300,
        "sort": "desc",
        "apikey": ETHERSCAN_API_KEY
    }
    res = requests.get(base, params=params_eth, timeout=10)
    if res.status_code == 200:
        txs = res.json().get("result", [])

    params_token = {
        "chainid": 1,
        "module": "account",
        "action": "tokentx",
        "address": address,
        "page": 1,
        "offset": 300,
        "sort": "desc",
        "apikey": ETHERSCAN_API_KEY
    }
    res2 = requests.get(base, params=params_token, timeout=10)
    if res2.status_code == 200:
        tokens = res2.json().get("result", [])

    return txs, tokens


def format_address(addr):
    """Format address as {4 digits}...{3 digits}...{4 digits}"""
    if not addr or len(addr) < 11:
        return addr
    return f"{addr[:4]}...{addr[-7:-4]}...{addr[-4:]}"


def interpret_eth_tx(tx, address, is_token=False):
    # Use centralized ETH_STAKING_CONTRACTS
    
    if not is_token:
        try:
            value = int(tx.get("value", 0)) / 1e18
        except (ValueError, TypeError):
            value = 0
        
        from_addr = tx.get("from", "").lower()
        to_addr = tx.get("to", "").lower()
        
        # Check if it's a staking transaction
        if from_addr == address.lower():
            # Check if sending to a known staking contract
            if to_addr in ETH_STAKING_CONTRACTS:
                staking_protocol = ETH_STAKING_CONTRACTS[to_addr]
                return f"🪙 質押 {value:.4f} ETH 至 {staking_protocol}"
            direction = "💸 轉出"
            return f"{direction} {value:.4f} ETH 給 {format_address(to_addr)}"
        else:
            # Check if receiving from a staking contract (unstaking/rewards)
            if from_addr in ETH_STAKING_CONTRACTS:
                staking_protocol = ETH_STAKING_CONTRACTS[from_addr]
                return f"💎 解質押/獎勵 {value:.4f} ETH 來自 {staking_protocol}"
            direction = "📥 接收"
            return f"{direction} {value:.4f} ETH 來自 {format_address(from_addr)}"
    else:
        token = tx.get("tokenSymbol", "")
        try:
            value = int(tx.get("value", 0)) / (10 ** int(tx.get("tokenDecimal", 18)))
        except (ValueError, TypeError, ZeroDivisionError):
            value = 0
        
        from_addr = tx.get("from", "")
        to_addr = tx.get("to", "")
        if from_addr.lower() == address.lower():
            return f"💰 轉出 {value:.4f} {token} 給 {format_address(to_addr)}"
        else:
            return f"📥 接收 {value:.4f} {token} 來自 {format_address(from_addr)}"


# ============================================================
# Bitcoin Transactions
# ============================================================
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_bitcoin_transactions(address):
    """Fetch Bitcoin transactions using Blockchain.info API"""
    url = f"https://blockchain.info/rawaddr/{address}"
    try:
        res = requests.get(url, params={"limit": 300}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get("txs", [])
    except Exception:
        pass
    return []


def interpret_bitcoin_tx(tx, address):
    """Interpret Bitcoin transaction for display"""
    try:
        # Calculate total input and output for this address
        inputs_value = 0
        outputs_value = 0
        from_addr = None
        to_addr = None
        
        # Check inputs (spending)
        for inp in tx.get("inputs", []):
            prev_out = inp.get("prev_out", {})
            inp_addr = prev_out.get("addr", "")
            if inp_addr == address:
                inputs_value += prev_out.get("value", 0)
            elif not from_addr:
                from_addr = inp_addr
        
        # Check outputs (receiving)
        for out in tx.get("out", []):
            out_addr = out.get("addr", "")
            if out_addr == address:
                outputs_value += out.get("value", 0)
            elif not to_addr:
                to_addr = out_addr
        
        # Convert satoshis to BTC
        net_value = (outputs_value - inputs_value) / 1e8
        
        if net_value > 0:
            # Receiving
            direction = "📥 接收"
            from_display = format_address(from_addr) if from_addr else "Unknown"
            return f"{direction} {abs(net_value):.8f} BTC 來自 {from_display}"
        elif net_value < 0:
            # Sending
            direction = "💸 轉出"
            to_display = format_address(to_addr) if to_addr else "Unknown"
            return f"{direction} {abs(net_value):.8f} BTC 給 {to_display}"
        else:
            return f"🔄 內部轉帳 (0 BTC 淨變化)"
    except Exception:
        return "❓ 無法解析交易"


# ============================================================
# Solana Transactions
# ============================================================
@st.cache_data(ttl=300)
def get_solana_transactions(address):
    """Fetch Solana transactions using Helius Enhanced Transactions API (with pagination)"""
    if not HELIUS_API_KEY:
        return []
    
    all_txs = []
    last_signature = None
    
    # Fetch up to 3 pages (300 transactions)
    for _ in range(3):
        url = f"https://api.helius.xyz/v0/addresses/{address}/transactions"
        params = {
            "api-key": HELIUS_API_KEY,
            "limit": 100
        }
        if last_signature:
            params["before"] = last_signature
            
        try:
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if not data or not isinstance(data, list):
                    break
                all_txs.extend(data)
                if len(data) < 100:
                    break
                last_signature = data[-1].get("signature")
            else:
                break
        except Exception as e:
            print(f"Helius API error: {e}")
            break
            
    return all_txs


@st.cache_data(ttl=86400)
def get_solana_token_metadata(mint):
    """Fetch token symbol from Helius DAS API (getAsset)"""
    if not HELIUS_API_KEY or not mint:
        return {}
    
    url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
    payload = {
        "jsonrpc": "2.0",
        "id": "get-token-metadata",
        "method": "getAsset",
        "params": {"id": mint}
    }
    
    try:
        res = requests.post(url, json=payload, timeout=5)
        if res.status_code == 200:
            result = res.json().get("result", {})
            token_info = result.get("token_info", {})
            metadata = result.get("content", {}).get("metadata", {})
            return {
                "symbol": token_info.get("symbol") or metadata.get("symbol") or "",
                "name": metadata.get("name") or ""
            }
    except Exception:
        pass
    return {}


def interpret_solana_tx(tx, address):
    """Interpret Helius enhanced transaction for display"""
    try:
        # Check for staking indicators in instructions first
        instructions = tx.get("instructions", [])
        is_staking_program = False
        for instr in instructions:
            if instr.get("programId") in SOL_STAKING_ENTITIES:
                is_staking_program = True
                break

        # Net balance tracking: {mint_or_sol: net_amount}
        net_balances = {}


        # Analyze native transfers (SOL)
        native_transfers = tx.get("nativeTransfers", [])
        for transfer in native_transfers:
            from_addr = transfer.get("fromUserAccount", "")
            to_addr = transfer.get("toUserAccount", "")
            amount = transfer.get("amount", 0) / 1e9
            if amount <= 0: continue

            if from_addr == address:
                net_balances["SOL_NATIVE"] = net_balances.get("SOL_NATIVE", 0) - amount
            if to_addr == address:
                net_balances["SOL_NATIVE"] = net_balances.get("SOL_NATIVE", 0) + amount

        # Analyze token transfers
        token_transfers = tx.get("tokenTransfers", [])
        for transfer in token_transfers:
            from_addr = transfer.get("fromUserAccount", "")
            to_addr = transfer.get("toUserAccount", "")
            amount = transfer.get("tokenAmount", 0)
            if amount <= 0: continue

            mint = transfer.get("mint", "")
            # We treat them as separate keys in net_balances to avoid summing Native + Wrapped
            if from_addr == address:
                net_balances[mint] = net_balances.get(mint, 0) - amount
            if to_addr == address:
                net_balances[mint] = net_balances.get(mint, 0) + amount

        # Summarize net changes by symbol
        sent_dict = {}     # {symbol: amount}
        received_dict = {} # {symbol: amount}
        
        for mint, net_val in net_balances.items():
            if abs(net_val) < 0.000001: continue # Filter out dust

            if mint == "SOL_NATIVE":
                symbol = "SOL"
            elif mint == SOL_WSOL_MINT:
                symbol = "WSOL"  # Keep separate from native SOL
            else:
                meta = get_solana_token_metadata(mint)
                symbol = meta.get("symbol") or format_address(mint) or "Token"
            
            if net_val < 0:
                sent_dict[symbol] = sent_dict.get(symbol, 0) + abs(net_val)
            else:
                received_dict[symbol] = received_dict.get(symbol, 0) + abs(net_val)

        # Convert to display strings
        sent_assets = [f"{amt:.4f} {sym}" for sym, amt in sent_dict.items()]
        received_assets = [f"{amt:.4f} {sym}" for sym, amt in received_dict.items()]

        # --- Interpretation Logic Priority ---
        
        tx_type = tx.get("type", "UNKNOWN")
        description = tx.get("description", "").lower()

        # 1. Swap detection (Sent AND Received)
        if (sent_assets and received_assets) or tx_type == "SWAP":
            sent_str = ", ".join(sent_assets)
            recv_str = ", ".join(received_assets)
            
            if sent_str and recv_str:
                return f"💱 兌換 {sent_str} → {recv_str}"
            elif sent_str:
                return f"💸 賣出/轉出 {sent_str}"
            elif recv_str:
                return f"📥 買入/接收 {recv_str}"

        # 2. Staking Detection
        is_staking = (
            tx_type in ["STAKE", "UNSTAKE"] or
            "stake" in description or
            "deposit" in description or
            is_staking_program
        )

        if is_staking:
            # Check if it's primarily unstaking
            unstaking = tx_type == "UNSTAKE" or (received_dict and not sent_dict and any(key in SOL_STAKING_ENTITIES for key in net_balances))
            amount_str = (sent_assets[0] if sent_assets else received_assets[0]) if (sent_assets or received_assets) else ""
            
            if unstaking:
                return f"💎 解質押 {amount_str}" if amount_str else "💎 解質押"
            else:
                return f"🪙 質押 {amount_str}" if amount_str else "🪙 質押"

        # 3. Simple Transfer Fallback
        if sent_assets:
            return f"💸 轉出 {', '.join(sent_assets)}"
        elif received_assets:
            return f"📥 接收 {', '.join(received_assets)}"
        
        # 4. Final Fallback to Helius description or type
        if description:
            # Clean up the description by shortening any full addresses
            import re
            cleaned_desc = description
            # Match base58-like addresses (32-44 chars)
            addr_pattern = r'[1-9A-HJ-NP-Za-km-z]{32,44}'
            for match in re.findall(addr_pattern, description):
                cleaned_desc = cleaned_desc.replace(match, format_address(match))
            return f"🧩 {cleaned_desc.capitalize()}"
        return f"🧩 {tx_type}"
    except Exception as e:
        return f"❓ 解析錯誤: {str(e)}"


# ============================================================
# Transaction Processing Helpers
# ============================================================
def process_ethereum_transactions(address):
    """Process Ethereum transactions and return formatted list"""
    readable = []
    eth_txs, token_txs = get_eth_transactions_detailed(address)
    
    # Process ETH transfers
    for tx in eth_txs[:300]:
        try:
            timestamp = int(tx["timeStamp"])
            time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
            desc = interpret_eth_tx(tx, address, is_token=False)
            h = tx["hash"]
            readable.append({
                "時間": time_str, 
                "摘要": desc, 
                "Tx Hash": f"{h[:8]}...{h[-6:]}",
                "_timestamp": timestamp
            })
        except (ValueError, KeyError):
            continue
    
    # Detect swaps by grouping token transfers by transaction hash
    swap_txs = {}  # Group by tx hash
    for tx in token_txs[:300]:
        try:
            h = tx["hash"]
            if h not in swap_txs:
                swap_txs[h] = []
            swap_txs[h].append(tx)
        except (ValueError, KeyError):
            continue
    
    # Analyze each transaction for swap pattern
    for tx_hash, transfers in swap_txs.items():
        if len(transfers) >= 2:  # Potential swap
            sent_tokens = []
            received_tokens = []
            timestamp = 0
            
            for tx in transfers:
                try:
                    from_addr = tx.get("from", "").lower()
                    to_addr = tx.get("to", "").lower()
                    token = tx.get("tokenSymbol", "Token")
                    value = int(tx.get("value", 0)) / (10 ** int(tx.get("tokenDecimal", 18)))
                    timestamp = int(tx.get("timeStamp", 0))
                    
                    if from_addr == address.lower():
                        sent_tokens.append(f"{value:.4f} {token}")
                    elif to_addr == address.lower():
                        received_tokens.append(f"{value:.4f} {token}")
                except (ValueError, TypeError, ZeroDivisionError, KeyError):
                    continue
            
            # If we have both sent and received, it's a swap
            if sent_tokens and received_tokens:
                time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
                sent_str = ", ".join(sent_tokens)
                received_str = ", ".join(received_tokens)
                desc = f"💱 兌換 {sent_str} → {received_str}"
                
                readable.append({
                    "時間": time_str,
                    "摘要": desc,
                    "Tx Hash": f"{tx_hash[:8]}...{tx_hash[-6:]}",
                    "_timestamp": timestamp
                })
            else:
                # Not a swap, process normally
                for tx in transfers:
                    try:
                        timestamp = int(tx["timeStamp"])
                        time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
                        desc = interpret_eth_tx(tx, address, is_token=True)
                        h = tx["hash"]
                        readable.append({
                            "時間": time_str, 
                            "摘要": desc, 
                            "Tx Hash": f"{h[:8]}...{h[-6:]}",
                            "_timestamp": timestamp
                        })
                    except (ValueError, KeyError):
                        continue
        else:
            # Single transfer, not a swap
            for tx in transfers:
                try:
                    timestamp = int(tx["timeStamp"])
                    time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
                    desc = interpret_eth_tx(tx, address, is_token=True)
                    h = tx["hash"]
                    readable.append({
                        "時間": time_str, 
                        "摘要": desc, 
                        "Tx Hash": f"{h[:8]}...{h[-6:]}",
                        "_timestamp": timestamp
                    })
                except (ValueError, KeyError):
                    continue
    
    # Final sorting and hard limit of 300
    readable.sort(key=lambda x: x.get("_timestamp", 0), reverse=True)
    return readable[:300]


def process_solana_transactions(address):
    """Process Solana transactions and return formatted list"""
    readable = []
    txs = get_solana_transactions(address)
    
    for tx in txs: # Process all fetched transactions up to limit
        try:
            # Helius uses 'timestamp' field (Unix timestamp)
            timestamp = tx.get("timestamp", 0)
            time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
            desc = interpret_solana_tx(tx, address)
            # Helius uses 'signature' field
            h = tx.get("signature", "")
            readable.append({
                "時間": time_str, 
                "摘要": desc, 
                "Tx Hash": f"{h[:8]}...{h[-6:]}" if h else "N/A",
                "_timestamp": timestamp
            })
        except (ValueError, KeyError):
            continue
    
    return readable


def process_bitcoin_transactions(address):
    """Process Bitcoin transactions and return formatted list"""
    readable = []
    btc_txs = get_bitcoin_transactions(address)
    
    for tx in btc_txs: # Process all fetched transactions up to limit
        try:
            timestamp = tx.get("time", 0)
            time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
            desc = interpret_bitcoin_tx(tx, address)
            h = tx.get("hash", "")
            readable.append({
                "時間": time_str, 
                "摘要": desc, 
                "Tx Hash": f"{h[:8]}...{h[-6:]}",
                "_timestamp": timestamp
            })
        except (ValueError, KeyError):
            continue
    
    return readable


# ============================================================
# Streamlit UI
# ============================================================
def main():
    st.set_page_config(page_title="Multi-chain Wallet Dashboard v2.6", layout="wide")
    st.title("🌐 多鏈錢包儀表板 v2.6 — 名人下拉選單 + 手動輸入")

    options = list(known_wallets.keys())
    sel = st.selectbox("選擇已知錢包（或選擇 '手動輸入地址'）", options)

    if sel:
        meta = known_wallets[sel]
        if meta["status"] == "manual":
            st.info("請輸入或貼上你要查詢的錢包地址（支持 ENS / 0x / Solana）")
            addr_input = st.text_input("錢包地址 / ENS", "")
        else:
            addr_input = st.text_input("錢包地址（可編輯）", meta["address"])
            st.markdown(f"**來源**：{meta['source']}（可信度：{meta['status']}）")

    if st.button("開始分析"):
        actual_addr = addr_input.strip()
        if not actual_addr:
            st.error("請提供有效錢包地址。")
            st.stop()

        addr_type = detect_address_type(actual_addr)

        if addr_type == "ethereum_ens":
            st.info("🔍 正在解析 ENS ...")
            resolved = resolve_ens(actual_addr)
            if resolved:
                actual_addr = resolved
                addr_type = "ethereum"
                st.success(f"✅ ENS 解析成功：{actual_addr}")
            else:
                st.error("❌ 無法解析 ENS 名稱。")
                st.stop()
        elif addr_type == "seeker":
            st.info(f"🔍 正在解析 Seeker ID / SNS: {actual_addr} ...")
            resolved = resolve_seeker_id(actual_addr)
            if resolved:
                st.success(f"✅ 解析成功：{resolved}")
                actual_addr = resolved
                addr_type = "solana" # Switch to solana for transaction processing
            else:
                st.warning("⚠️ 無法解析此名稱到 Solana 地址。")
                st.stop()
        elif not addr_type:
            st.error("❌ 無法判斷地址類型。")
            st.stop()

        st.info(f"🔎 檢測到 {addr_type.upper()} 類型地址")

        # Check if Hyperliquid positions exist
        pos = get_hyperliquid_positions(actual_addr)
        has_hyperliquid = pos and "assetPositions" in pos and len(pos.get("assetPositions", [])) > 0
        
        # Reverting to original simple Tabs
        tabs = st.tabs(["💼 Hyperliquid 倉位", "📜 交易紀錄"])

        with tabs[0]:
            if has_hyperliquid:
                render_hyperliquid_positions(pos)
            else:
                st.info("💭 此地址目前沒有 Hyperliquid 倉位資料")

        with tabs[1]:
            # 📜 交易紀錄
            readable = []
            with st.spinner("⏳ 正在獲取交易紀錄 (最多 300 筆)..."):
                if addr_type == "ethereum":
                    readable = process_ethereum_transactions(actual_addr)
                elif addr_type == "solana":
                    readable = process_solana_transactions(actual_addr)
                elif addr_type == "bitcoin":
                    readable = process_bitcoin_transactions(actual_addr)
                
            if readable and len(readable) > 0:
                # Sort by timestamp in descending order (newest first)
                readable.sort(key=lambda x: x.get("_timestamp", 0), reverse=True)
                
                # Remove hidden fields and display ALL fetched records
                df = pd.DataFrame(readable)
                if "_timestamp" in df.columns:
                    df = df.drop(columns=["_timestamp"])
                
                st.success(f"✅ 成功讀取 {len(readable)} 筆交易")
                st.dataframe(df, use_container_width=True, height=800)
            else:
                st.warning("⚠️ 未找到任何符合條件的交易紀錄。")

if __name__ == "__main__":
    main()
