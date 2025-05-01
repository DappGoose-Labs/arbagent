import pytest
from defi_agent import DeFiAgent

def test_settle_profit():
    agent = DeFiAgent("0xMockWallet")
    result = agent.settle_profit("ETH", 10)
    assert result["status"] == "success"
    assert "tx_hash" in result

def test_deploy_to_lending():
    agent = DeFiAgent("0xMockWallet")
    result = agent.deploy_to_lending("USDC", 1000)
    assert result["status"] == "success"
    assert "tx_hash" in result

def test_deploy_to_staking():
    agent = DeFiAgent("0xMockWallet")
    result = agent.deploy_to_staking("ETH", 5, "Lido")
    assert result["status"] == "success"
    assert "tx_hash" in result