# ============================================================
# Known Wallets Configuration
# 已知或被媒體報導的錢包清單
# 
# NOTE: Hyperliquid addresses are on Hyperliquid L1 blockchain, 
# not Ethereum mainnet. They will show:
#   ✅ Hyperliquid positions (via Hyperliquid API)
#   ❌ Ethereum transactions (no activity on Ethereum mainnet)
# ============================================================

KNOWN_WALLETS = {
    "手動輸入地址 (Manual)": {
        "address": "",
        "status": "manual",
        "source": "—",
    },
    
    # ========== Top Hyperliquid L1 Traders ==========
    # These addresses are on Hyperliquid L1, not Ethereum
    # Use them to view Hyperliquid positions only
    "The White Whale (@TheWhiteWhaleHL)": {
        "address": "0xd5ff5491f6f3c80438e02c281726757baf4d1070",
        "status": "verified",
        "source": "Binance Research / OKX / Bitget (Made $50M+ in 30 days, July-Aug 2025) [Hyperliquid L1]",
    },
    "The White Whale - Wallet 2": {
        "address": "0xb8b9e3097c8b1dddf9c5ea9d48a7ebeaf09d67d2",
        "status": "verified",
        "source": "Binance Research (Associated wallet of The White Whale) [Hyperliquid L1]",
    },
    "BitcoinOG / 1011short (Trump Whale)": {
        "address": "0xb317d2bc2d3d2df5fa441b5bae0ab9d8b07283ae",
        "status": "verified",
        "source": "CoinSpeaker / KuCoin / Blockchain.news (Peak profit $142M, liquidated -$128.7M) [Hyperliquid L1]",
    },
    
    # ========== Celebrity Traders & Influencers ==========
    "麻吉大哥 (Machi Big Brother)": {
        "address": "0x020ca66c30bec2c4fe3861a94e4db4a498a35872",
        "status": "verified",
        "source": "Etherscan / Arbiscan / Blockchain.news (machibigbrother.eth) [Ethereum Mainnet]",
    },
    "James Wynn (合約戰神)": {
        "address": "0x5078C2fBeA2b2aD61bc840Bc023E35Fce56BeDb6",
        "status": "verified",
        "source": "Cryptopolitan / TheBlock (Lost $110M from BTC liquidation, 9 liquidations in July 2025) [Hyperliquid L1]",
    }
}
