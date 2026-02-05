import os
import sys
import pytest
import hashlib
from unittest.mock import patch, MagicMock

# Identity decorator for cache_data
def identity_decorator(*args, **kwargs):
    def wrapper(f):
        return f
    return wrapper

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock streamlit before importing the dashboard
mock_st = MagicMock()
mock_st.cache_data = identity_decorator
sys.modules['streamlit'] = mock_st

from wallet_activity_dashboard import (
    detect_address_type, 
    resolve_ens,
    SkrResolver,
    ALL_DOMAINS_HASH_PREFIX,
    SKR_PARENT,
    ALL_DOMAINS_PROGRAM_ID,
    interpret_eth_tx,
    interpret_bitcoin_tx,
    interpret_solana_tx,
    format_address,
    safe_post_json,
    process_ethereum_transactions,
    process_solana_transactions,
    process_bitcoin_transactions
)
from solders.pubkey import Pubkey

def test_format_address():
    addr = "0x1234567890abcdef1234567890abcdef12345678"
    res = format_address(addr)
    assert res == f"{addr[:4]}...{addr[-7:-4]}...{addr[-4:]}"
    assert format_address("short") == "short"

def test_detect_address_type():
    assert detect_address_type("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa") == "bitcoin"
    assert detect_address_type("0x742d35Cc6634C0532925a3b844Bc454e4438f44e") == "ethereum"
    assert detect_address_type("msft.skr") == "seeker"
    assert detect_address_type("msft") == "seeker_potential"

@patch('requests.get')
def test_resolve_ens(mock_get):
    mock_get.return_value.json.return_value = {"address": "0x123"}
    assert resolve_ens("test.eth") == "0x123"

def test_skr_resolver():
    resolver = SkrResolver()
    assert resolver.get_name_hash("test")
    
    with patch.object(resolver.client, 'get_account_info') as mock_get:
        mock_get.return_value = MagicMock(value=None)
        assert resolver.resolve_sns_direct("msft.skr") is None

@patch.object(SkrResolver, 'resolve_sns_direct')
@patch('requests.get')
def test_skr_resolver_unified(mock_get, mock_direct):
    resolver = SkrResolver()
    mock_direct.return_value = "ADDR1"
    assert resolver.resolve("msft") == "ADDR1" # Tests auto-completion

def test_interpret_txs():
    # ETH
    tx = {"value": "1000000000000000000", "from": "0x1", "to": "0x2", "timeStamp": "1"}
    assert "轉出" in interpret_eth_tx(tx, "0x1")
    
    # BTC
    btc_tx = {"inputs": [{"prev_out": {"addr": "A1", "value": 10**8}}], "out": [{"addr": "A2", "value": 10**8}]}
    assert "轉出" in interpret_bitcoin_tx(btc_tx, "A1")
    
    # SOL
    sol_tx = {"type": "TRANSFER", "nativeTransfers": [{"fromUserAccount": "S1", "toUserAccount": "S2", "amount": 10**9}]}
    assert "轉出" in interpret_solana_tx(sol_tx, "S1", "KEY")

def test_safe_post_json():
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = '{"a":1}'
        mock_post.return_value.json.return_value = {"a":1}
        assert safe_post_json("url", {}) == {"a":1}

@patch('wallet_activity_dashboard.get_eth_transactions_detailed')
def test_process_ethereum_transactions(mock_get):
    mock_get.return_value = ([], [])
    assert process_ethereum_transactions("0x1", "KEY") == []

@patch('wallet_activity_dashboard.get_solana_transactions')
def test_process_solana_transactions(mock_get):
    mock_get.return_value = []
    assert process_solana_transactions("ADDR", "KEY") == []

def test_interpret_solana_tx_edge_cases():
    # Swap
    tx_swap = {
        "type": "SWAP",
        "nativeTransfers": [
            {"fromUserAccount": "ME", "toUserAccount": "YOU", "amount": 10**9}
        ],
        "tokenTransfers": [
            {"fromUserAccount": "OTHER", "toUserAccount": "ME", "tokenAmount": 100, "mint": "M1"}
        ]
    }
    with patch('wallet_activity_dashboard.get_solana_token_metadata') as mock_meta:
        mock_meta.return_value = {"symbol": "T1"}
        res = interpret_solana_tx(tx_swap, "ME", "KEY")
        assert "兌換" in res

    # Staking program
    tx_stake = {
        "type": "UNKNOWN",
        "instructions": [{"programId": "Stake11111111111111111111111111111111111111"}]
    }
    res_stake = interpret_solana_tx(tx_stake, "ME", "KEY")
    assert "質押" in res_stake

def test_process_ethereum_swaps():
    with patch('wallet_activity_dashboard.get_eth_transactions_detailed') as mock_get:
        mock_get.return_value = ([], [
            {"hash": "H1", "from": "ME", "to": "POOL", "value": "100", "tokenSymbol": "A", "tokenDecimal": "0", "timeStamp": "1"},
            {"hash": "H1", "from": "POOL", "to": "ME", "value": "200", "tokenSymbol": "B", "tokenDecimal": "0", "timeStamp": "1"}
        ])
        res = process_ethereum_transactions("ME", "KEY")
        assert len(res) == 1
        assert "兌換" in res[0]["摘要"]

@patch('wallet_activity_dashboard.st')
@patch('wallet_activity_dashboard.detect_address_type')
@patch('wallet_activity_dashboard.SkrResolver')
def test_main_flow(mock_resolver_class, mock_detect, mock_st):
    from wallet_activity_dashboard import main
    import os
    with patch.dict(os.environ, {"ETH_API_KEY": "K1", "INFURA_API_URL": "U1"}):
        mock_st.selectbox.return_value = "手動輸入地址 (Manual)"
        mock_st.text_input.return_value = "msft"
        mock_st.button.return_value = True
        mock_detect.return_value = "seeker_potential"
        mock_resolver_class.return_value.resolve.return_value = "SOL_ADDR"
        
        with patch('wallet_activity_dashboard.get_hyperliquid_positions') as mock_hl:
            mock_hl.return_value = {}
            with patch('wallet_activity_dashboard.process_solana_transactions') as mock_proc:
                mock_proc.return_value = []
                main()
    assert mock_st.success.called
