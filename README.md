# 🌐 Multi-Chain Wallet Dashboard

A Streamlit-based cryptocurrency wallet analytics dashboard for tracking wallet activities across multiple blockchain networks.

## Features

### 🔗 Multi-Chain Support
- **Bitcoin**: Track BTC transactions via Blockchain.info API
- **Ethereum**: Track ETH and ERC-20 token transactions via Etherscan
- **Solana**: Monitor SOL transactions and activities via Helius API
- **Hyperliquid**: View trading positions, PnL, and leverage data

### 🏷️ Domain Name Resolution
- **ENS** (`.eth`) - Ethereum Name Service resolution
- **Seeker** (`.skr`) - Seeker SNS resolution to Solana addresses

### 📊 Analytics Features
- Pre-configured celebrity/whale wallet dropdown
- Real-time transaction history (last 30 transactions)
- Hyperliquid position tracking with profit/loss visualization
- Automatic address type detection
- Color-coded P&L display
- 5-minute API response caching for performance

## Installation

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd chain-lookup
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
Create a `.env` file in the project root:

```bash
ETH_API_KEY=your_etherscan_api_key
INFURA_API_URL=https://mainnet.infura.io/v3/your_infura_project_id
HELIUS_API_KEY=your_helius_api_key
```

**Get your API keys:**
- Etherscan API: https://etherscan.io/myapikey
- Infura: https://infura.io/
- Helius (for Solana): https://www.helius.dev/

### 4. Configure known wallets (optional)
Edit `known_wallets.py` to add or modify celebrity/whale wallets:

```python
KNOWN_WALLETS = {
    "Wallet Name": {
        "address": "0x... or name.eth",
        "status": "reported",
        "source": "Source description",
    },
}
```

## Usage

### Run the dashboard
```bash
streamlit run wallet_activity_dashboard.py
```

The app will open in your browser at `http://localhost:8501`

### Using the Dashboard

1. **Select a wallet** from the dropdown menu or choose "手動輸入地址 (Manual)" to enter a custom address
2. **Enter wallet address** - Supports:
   - Bitcoin addresses (Legacy, P2SH, Bech32)
   - Ethereum addresses (`0x...`)
   - ENS names (`vitalik.eth`)
   - Solana addresses
   - Seeker IDs (`.skr`)
3. **Click "開始分析"** to fetch data
4. **View results** in two tabs:
   - 💼 **Hyperliquid 倉位**: Trading positions with P&L (if available)
   - 📜 **交易紀錄**: Transaction history

## Project Structure

```
chain-lookup/
├── wallet_activity_dashboard.py  # Main application
├── known_wallets.py               # Celebrity/whale wallet configurations
├── requirements.txt               # Python dependencies
├── .env                          # API keys (not in git)
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## API Rate Limits

The dashboard uses caching (5-minute TTL) to minimize API calls:
- **Blockchain.info**: Free public API for Bitcoin
- **Etherscan**: Free tier allows 5 calls/second
- **Helius**: Free tier for Solana transactions (requires API key)
- **Hyperliquid**: Public API

## Security Notes

⚠️ **Important:**
- Never commit your `.env` file to version control
- Keep your API keys private
- The `.gitignore` file is configured to exclude `.env`

## Dependencies

- `streamlit` - Web interface
- `web3` - Ethereum interaction
- `ens` - ENS name resolution
- `pandas` - Data manipulation
- `requests` - API calls
- `python-dotenv` - Environment variable management
- `base58` - Solana address decoding

## Troubleshooting

### "Missing ETH_API_KEY in .env file"
Make sure your `.env` file exists and contains valid API keys.

### ENS resolution fails
Ensure the `ens` package is installed: `pip install ens`

### Transaction direction shows incorrectly
This was fixed in v2.6. Make sure you're using the latest version.

## Contributing

Feel free to submit issues or pull requests to improve the dashboard.

## License

MIT License
