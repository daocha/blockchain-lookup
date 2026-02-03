# 🌐 Multi-Chain Wallet Dashboard v2.6

A professional Streamlit-based cryptocurrency analytics dashboard for tracking wallet activities and DeFi positions across multiple blockchain networks.

---

## ✨ Key Features

### 🔗 Multi-Chain Transaction Tracking
*   **Ethereum (ETH)**: Detailed ETH and ERC-20 token histories (Top 300 records).
*   **Solana (SOL)**: Clean transaction summaries including complex DeFi swaps, staking, and native transfers (Top 300 records).
*   **Bitcoin (BTC)**: Native BTC transaction monitoring via Blockchain.info.

### 💼 DeFi & Position Monitoring
*   **Hyperliquid Integration**: Real-time view of trading positions, PnL, leverage, and margin ratios.
*   **Smart Netting (Solana)**: Automatically calculates net balance changes for complex aggregator swaps (e.g., Jupiter, Dflow) instead of showing messy intermediate transfers.

### 🏷️ Domain Name Resolution
*   **ENS (`.eth`)**: Full Ethereum Name Service resolution.
*   **Seeker ID (`.skr`)**: Integrated SNS resolution to Solana mainnet addresses.

### 📊 Advanced Analytics
*   **Celebrity/Whale Tracking**: Built-in dropdown menu with pre-configured high-profile wallets.
*   **Automatic Detection**: Input any address and the system automatically identifies the chain.
*   **Privacy First**: All data is fetched on-demand and cached locally (5-minute TTL).

---

## 🛠️ Setup & Installation

### 1. Prerequisites
Ensure you have Python 3.9+ installed.

### 2. Installation
```bash
git clone <your-repo-url>
cd chain-lookup
pip install -r requirements.txt
```

### 3. API Configuration
Create a `.env` file in the root directory:

```ini
# --- Required API Keys ---
ETH_API_KEY=your_etherscan_api_key
HELIUS_API_KEY=your_helius_api_key
INFURA_API_URL=https://mainnet.infura.io/v3/your_project_id
```

> [!NOTE]
> *   **Etherscan**: [Get key here](https://etherscan.io/myapikey)
> *   **Helius (Solana)**: [Get key here](https://www.helius.dev/)
> *   **Infura (ENS)**: [Get key here](https://infura.io/)

---

## 🚀 Usage

Launch the web interface:

```bash
streamlit run wallet_activity_dashboard.py
```

### How to use:
1.  **Select Wallet**: Use the dropdown for known wallets or select **"手動輸入地址"** for a custom search.
2.  **Enter Address**: Supports 0x (ETH), Solana, BTC, ENS (`.eth`), or Seeker (`.skr`).
3.  **Analyze**: Click **"開始分析"**.
4.  **Explore**:
    *   **Hyperliquid Tab**: View active perp positions and leverage.
    *   **Transactions Tab**: View the latest 300 cross-chain transactions in a clean, scrollable table.

---

## 📁 Project Structure

```text
chain-lookup/
├── wallet_activity_dashboard.py  # Core Application Logic & UI
├── known_wallets.py               # Pre-configured whale/celebrity data
├── requirements.txt               # Dependencies
├── .env                          # Local Environment Secrets (Git ignored)
└── README.md                     # Project Documentation
```

---

## 🔒 Security & Performance
*   **Local Execution**: Your API keys and search history remain on your local machine.
*   **Caching**: Uses `st.cache_data` with a 5-minute TTL to ensure fast load times and minimize API rate-limiting hits.

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

---

## 📜 License
MIT License - Developed for Advanced Blockchain Analytics.
