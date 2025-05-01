import pytest
import asyncio
from src.market_data.collector import TradeSimulator

@pytest.mark.asyncio
async def test_simulate_trade_cross_dex():
    simulator = TradeSimulator()
    trade_data = {
        "type": "cross_dex",
        "token0": "ETH",
        "token1": "USDC",
        "buy_dex": "Uniswap",
        "buy_network": "1",
        "buy_pool": "pool1",
        "buy_price": 2000,
        "sell_dex": "Sushiswap",
        "sell_network": "1",
        "sell_pool": "pool2",
        "sell_price": 2100,
        "price_diff_pct": 5,
        "buy_fee": 0.003,
        "sell_fee": 0.003,
    }
    profitable, details = await simulator.simulate_trade(trade_data)
    assert isinstance(profitable, bool)
    assert isinstance(details, dict)

@pytest.mark.asyncio
async def test_simulate_trade_triangular():
    simulator = TradeSimulator()
    trade_data = {
        "type": "triangular",
        "dex_id": "Uniswap",
        "network_id": "1",
        "token_a": "ETH",
        "token_b": "USDC",
        "token_c": "DAI",
        "price_a_to_b": 2000,
        "price_b_to_c": 1,
        "price_c_to_a": 0.0005,
        "round_trip_rate": 1.01,
        "total_fee": 0.003,
    }
    profitable, details = await simulator.simulate_trade(trade_data)
    assert isinstance(profitable, bool)
    assert isinstance(details, dict)

@pytest.mark.asyncio
async def test_simulate_trade_unknown_type():
    simulator = TradeSimulator()
    trade_data = {"type": "unknown"}
    profitable, details = await simulator.simulate_trade(trade_data)
    assert profitable is False
    assert "reason" in details