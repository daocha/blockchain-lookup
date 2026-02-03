# ============================================================
# 🌐 Wallet Dashboard v2.6
# Ethereum + Solana + Seeker + Hyperliquid + 名人下拉選單
# ============================================================

import requests
import streamlit as st
import pandas as pd
import base58
import ssl
import time
import os
from datetime import datetime
from web3 import Web3
from dotenv import load_dotenv
from known_wallets import KNOWN_WALLETS

# Optional: ENS support
try:
    from ens import ENS
    HAS_ENS = True
except ImportError:
    HAS_ENS = False

# ---------------- CONFIG ----------------
load_dotenv()
ETHERSCAN_API_KEY = os.getenv("ETH_API_KEY")
INFURA_API = os.getenv("INFURA_API_URL")

# Validate API keys
if not ETHERSCAN_API_KEY:
    st.error("❌ Missing ETH_API_KEY in .env file")
    st.stop()
if not INFURA_API:
    st.error("❌ Missing INFURA_API_URL in .env file")
    st.stop()

w3 = Web3(Web3.HTTPProvider(INFURA_API))

# Known wallets imported from known_wallets.py
known_wallets = KNOWN_WALLETS

# ============================================================
# Helper functions
# ============================================================
def detect_address_type(addr: str):
    addr = addr.strip()
    if addr.lower().startswith("0x") and len(addr) == 42:
        return "ethereum"
    try:
        base58.b58decode(addr)
        if 32 <= len(addr) <= 44:
            return "solana"
    except Exception:
        pass
    if addr.endswith(".skr"):
        return "seeker"
    return None


def resolve_ens(name_or_addr: str):
    """解析 ENS 名稱為以太坊地址"""
    if not name_or_addr.endswith(".eth"):
        return name_or_addr
    
    # Try using ENS library if available
    if HAS_ENS:
        try:
            ns = ENS.fromWeb3(w3)
            addr = ns.address(name_or_addr)
            if addr:
                return addr
        except Exception:
            pass
    
    # Fallback to API resolution
    try:
        res = requests.get(f"https://api.ensideas.com/ens/resolve/{name_or_addr}", timeout=10)
        data = res.json()
        if "address" in data and data["address"]:
            return data["address"]
    except Exception:
        pass
    
    return None


def resolve_seeker_id(name):
    """解析 Seeker SNS (.skr) 為 Solana address（含 fallback 與 SSL 問題修正）"""
    if not name.endswith(".skr"):
        return None

    headers = {"User-Agent": "Mozilla/5.0"}
    urls = [
        f"http://sns-api.seeker.tech/v1/resolve/{name}",
        f"http://api.seeker.id/v1/resolve/{name}",
    ]
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200 and res.text.strip():
                data = res.json()
                if "address" in data:
                    return data["address"]
                elif "result" in data and "address" in data["result"]:
                    return data["result"]["address"]
        except Exception as e:
            print(f"Seeker API error: {e}")
            continue
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
        "limit": 30,
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
        "limit": 30,
        "sort": "desc",
        "apikey": ETHERSCAN_API_KEY
    }
    res2 = requests.get(base, params=params_token, timeout=10)
    if res2.status_code == 200:
        tokens = res2.json().get("result", [])

    return txs, tokens


def interpret_eth_tx(tx, address, is_token=False):
    if not is_token:
        try:
            value = int(tx.get("value", 0)) / 1e18
        except (ValueError, TypeError):
            value = 0
        
        from_addr = tx.get("from", "").lower()
        to_addr = tx.get("to", "")
        
        # Fix: Check sender to determine direction
        if from_addr == address.lower():
            direction = "💸 轉出"
            return f"{direction} {value:.4f} ETH 給 {to_addr[:8]}..."
        else:
            direction = "📥 接收"
            return f"{direction} {value:.4f} ETH 來自 {from_addr[:8]}..."
    else:
        token = tx.get("tokenSymbol", "")
        try:
            value = int(tx.get("value", 0)) / (10 ** int(tx.get("tokenDecimal", 18)))
        except (ValueError, TypeError, ZeroDivisionError):
            value = 0
        
        from_addr = tx.get("from", "")
        to_addr = tx.get("to", "")
        if from_addr.lower() == address.lower():
            return f"💰 轉出 {value:.4f} {token} 給 {to_addr[:8]}..."
        else:
            return f"📥 接收 {value:.4f} {token} 來自 {from_addr[:8]}..."


# ============================================================
# Solana Transactions
# ============================================================
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_solana_transactions(address):
    url = "https://api.solscan.io/account/transactions"
    try:
        res = requests.get(url, params={"address": address, "limit": 30}, timeout=10)
        data = res.json()
        if isinstance(data, dict) and "data" in data:
            return data["data"]
        elif isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def interpret_solana_tx(tx):
    ttype = tx.get("type", "unknown").lower()
    try:
        lamports = int(tx.get("lamport", 0))
        sol_amount = lamports / 1e9
    except (ValueError, TypeError):
        sol_amount = 0
    
    status = "✅ 成功" if tx.get("status", "") == "Success" else "❌ 失敗"

    if "transfer" in ttype:
        return f"💸 轉帳 {sol_amount:.4f} SOL（{status}）"
    elif "swap" in ttype:
        return f"💱 代幣兌換（{status}）"
    elif "stake" in ttype:
        return f"🪙 質押操作（{status}）"
    elif "unstake" in ttype or "withdraw" in ttype:
        return f"💎 解質押操作（{status}）"
    elif "mint" in ttype:
        return f"🎨 NFT Mint（{status}）"
    else:
        return f"🧩 其他操作（{status}）"


# ============================================================
# Streamlit UI
# ============================================================
st.set_page_config(page_title="Multi-chain Wallet Dashboard v2.6", layout="wide")
st.title("🌐 多鏈錢包儀表板 v2.6 — 名人下拉選單 + 手動輸入")

options = list(known_wallets.keys())
sel = st.selectbox("選擇已知錢包（或選擇 '手動輸入地址'）", options)

if sel:
    meta = known_wallets[sel]
    if meta["status"] == "manual":
        st.info("請輸入或貼上你要查詢的錢包地址（支持 ENS / .skr / 0x / Solana）")
        addr_input = st.text_input("錢包地址 / ENS / Seeker ID", "")
    else:
        addr_input = st.text_input("錢包地址（可編輯）", meta["address"])
        st.markdown(f"**來源**：{meta['source']}（可信度：{meta['status']}）")

if st.button("開始分析"):
    actual_addr = addr_input.strip()
    if not actual_addr:
        st.error("請提供有效錢包地址。")
        st.stop()

    addr_type = detect_address_type(actual_addr)

    if not addr_type and actual_addr.endswith(".eth"):
        st.info("🔍 正在解析 ENS ...")
        resolved = resolve_ens(actual_addr)
        if resolved:
            actual_addr = resolved
            addr_type = "ethereum"
            st.success(f"✅ ENS 解析成功：{actual_addr}")
        else:
            st.error("❌ 無法解析 ENS 名稱。")
            st.stop()

    if actual_addr.endswith(".skr"):
        st.info("🔍 正在解析 Seeker ID (.skr)...")
        seeker_resolved = resolve_seeker_id(actual_addr)
        if seeker_resolved:
            addr_type = "solana"
            st.success(f"✅ Seeker ID 解析成功：{seeker_resolved}")
            actual_addr = seeker_resolved
        else:
            st.warning("⚠️ 無法解析此 Seeker ID。")

    if not addr_type:
        st.error("❌ 無法判斷地址類型。")
        st.stop()

    st.info(f"🔎 檢測到 {addr_type.upper()} 類型地址")

    tabs = st.tabs(["💼 Hyperliquid 倉位", "📜 交易紀錄"])

    # Hyperliquid 倉位
    with tabs[0]:
        pos = get_hyperliquid_positions(actual_addr)
        render_hyperliquid_positions(pos)

    # 交易紀錄
    with tabs[1]:
        readable = []

        if addr_type == "ethereum":
            eth_txs, token_txs = get_eth_transactions_detailed(actual_addr)
            for tx in eth_txs[:25]:
                try:
                    timestamp = int(tx["timeStamp"])
                    time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
                    desc = interpret_eth_tx(tx, actual_addr, is_token=False)
                    h = tx["hash"]
                    readable.append({
                        "時間": time_str, 
                        "摘要": desc, 
                        "Tx Hash": f"{h[:8]}...{h[-6:]}",
                        "_timestamp": timestamp  # Hidden field for sorting
                    })
                except (ValueError, KeyError):
                    continue
                    
            for tx in token_txs[:25]:
                try:
                    timestamp = int(tx["timeStamp"])
                    time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
                    desc = interpret_eth_tx(tx, actual_addr, is_token=True)
                    h = tx["hash"]
                    readable.append({
                        "時間": time_str, 
                        "摘要": desc, 
                        "Tx Hash": f"{h[:8]}...{h[-6:]}",
                        "_timestamp": timestamp  # Hidden field for sorting
                    })
                except (ValueError, KeyError):
                    continue

        elif addr_type == "solana":
            txs = get_solana_transactions(actual_addr)
            for tx in txs[:30]:
                try:
                    timestamp = tx.get("blockTime", 0)
                    time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
                    desc = interpret_solana_tx(tx)
                    h = tx.get("txHash", "")
                    readable.append({
                        "時間": time_str, 
                        "摘要": desc, 
                        "Tx Hash": f"{h[:8]}...{h[-6:]}",
                        "_timestamp": timestamp  # Hidden field for sorting
                    })
                except (ValueError, KeyError):
                    continue

        if readable:
            # Sort by timestamp in descending order (newest first)
            readable.sort(key=lambda x: x.get("_timestamp", 0), reverse=True)
            
            # Remove the hidden timestamp field before display
            df = pd.DataFrame(readable)
            if "_timestamp" in df.columns:
                df = df.drop(columns=["_timestamp"])
            
            st.dataframe(df)
        else:
            st.warning("未找到任何交易紀錄。")
