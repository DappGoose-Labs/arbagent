import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from executor import FlashloanExecutor
from src.trade_simulation import TradeSimulationService

@pytest.fixture
def mock_simulation_service():
    return MagicMock(spec=TradeSimulationService)

@pytest.fixture
def flashloan_executor(mock_simulation_service):
    executor = FlashloanExecutor(mock_simulation_service)
    executor.web3_clients = {"1": MagicMock(), "2": MagicMock()}
    executor.wallet_address = "0xMockWalletAddress"
    return executor

def test_initialize_web3_clients(monkeypatch):
    with patch("executor.Web3") as mock_web3:
        mock_web3.HTTPProvider.return_value = "http://mock-rpc"
        executor = FlashloanExecutor(MagicMock())
        executor.initialize_web3_clients()
        assert len(executor.web3_clients) > 0

def test_initialize_wallet_no_key(monkeypatch):
    monkeypatch.setattr("executor.WALLET_CONFIG", {})
    executor = FlashloanExecutor(MagicMock())
    executor.wallet_address = None
    executor.initialize_wallet()
    assert executor.wallet_address is None

@pytest.mark.asyncio
async def test_execute_real_aave_flashloan(flashloan_executor):
    trade = {"simulated_profit_usd": 1000}
    execution_result = await flashloan_executor.execute_real_aave_flashloan(trade, {})
    assert execution_result["success"] is True
    assert "gas_used" in execution_result
    assert "profit_usd" in execution_result