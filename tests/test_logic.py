import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock streamlit before importing the dashboard
sys.modules['streamlit'] = MagicMock()

from wallet_activity_dashboard import (
    detect_address_type, 
    resolve_seeker_id, 
    resolve_ens,
    resolve_sns_direct
)

def test_detect_address_type():
    # Bitcoin
    assert detect_address_type("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa") == "bitcoin"
    assert detect_address_type("3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy") == "bitcoin"
    assert detect_address_type("bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq") == "bitcoin"
    
    # Ethereum
    assert detect_address_type("0x742d35Cc6634C0532925a3b844Bc454e4438f44e") == "ethereum"
    assert detect_address_type("test.eth") == "ethereum_ens"
    
    # Solana / Seeker
    assert detect_address_type("HN7cABqLq46Es1W92BQQB8mUshU88P5gN58A6K1Tzp") == "solana"
    assert detect_address_type("msft.skr") == "seeker"
    assert detect_address_type("test.sol") == "seeker"
    
    # Invalid
    assert detect_address_type("invalid") is None
    assert detect_address_type("short") is None

@patch('requests.get')
def test_resolve_ens(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"address": "0x123"}
    mock_get.return_value = mock_response
    
    assert resolve_ens("test.eth") == "0x123"
    assert resolve_ens("0x123") == "0x123" # No .eth

@patch('requests.get')
def test_resolve_ens_failure(mock_get):
    # Test API failure
    mock_get.side_effect = Exception("API Down")
    assert resolve_ens("test.eth") is None

@patch('wallet_activity_dashboard.SolanaClient')
def test_resolve_sns_direct_skr(mock_client_class):
    mock_client = mock_client_class.return_value
    mock_res = MagicMock()
    # Mock data for .skr: owner at offset 40
    data = bytearray(72)
    from solders.pubkey import Pubkey
    mock_addr = Pubkey.new_unique()
    data[40:72] = bytes(mock_addr)
    mock_res.value.data = bytes(data)
    mock_client.get_account_info.return_value = mock_res
    
    assert resolve_sns_direct("test.skr") == str(mock_addr)

@patch('wallet_activity_dashboard.SolanaClient')
def test_resolve_sns_direct_sol(mock_client_class):
    mock_client = mock_client_class.return_value
    mock_res = MagicMock()
    # Mock data for .sol: owner at offset 32
    data = bytearray(64)
    from solders.pubkey import Pubkey
    mock_addr = Pubkey.new_unique()
    data[32:64] = bytes(mock_addr)
    mock_res.value.data = bytes(data)
    mock_client.get_account_info.return_value = mock_res
    
    assert resolve_sns_direct("test.sol") == str(mock_addr)

@patch('wallet_activity_dashboard.SolanaClient')
def test_resolve_sns_direct_exceptions(mock_client_class):
    mock_client = mock_client_class.return_value
    mock_client.get_account_info.side_effect = Exception("Solana Error")
    
    # Trigger except block in .skr
    assert resolve_sns_direct("test.skr") is None
    # Trigger except block in .sol
    assert resolve_sns_direct("test.sol") is None

@patch('wallet_activity_dashboard.resolve_sns_direct')
@patch('requests.get')
def test_resolve_seeker_id_unified(mock_get, mock_sns_direct):
    # 1. Test .skr direct success
    mock_sns_direct.return_value = "ADDR1"
    assert resolve_seeker_id("test.skr") == "ADDR1"
    
    # 2. Test .sol via proxy success
    mock_sns_direct.return_value = None
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"s": "ok", "result": "ADDR2"}
    mock_get.return_value = mock_response
    assert resolve_seeker_id("test.sol") == "ADDR2"
    
    # 3. Test .skr via community fallback
    mock_sns_direct.return_value = None
    def side_effect(url, **kwargs):
        m = MagicMock()
        m.status_code = 200
        if "seeker-production" in url:
            m.json.return_value = {"address": "ADDR3"}
        else:
            m.json.return_value = {"s": "error"}
        return m
    mock_get.side_effect = side_effect
    assert resolve_seeker_id("test.skr") == "ADDR3"

@patch('wallet_activity_dashboard.resolve_sns_direct')
@patch('requests.get')
def test_resolve_seeker_id_failures(mock_get, mock_sns_direct):
    mock_sns_direct.return_value = None
    mock_get.side_effect = Exception("All Down")
    
    assert resolve_seeker_id("test.skr") is None
    assert resolve_seeker_id("test.sol") is None
    assert resolve_seeker_id("no_dot") is None
