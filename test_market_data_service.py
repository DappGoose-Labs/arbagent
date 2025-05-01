import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from __init__ import MarketDataService

@pytest.mark.asyncio
async def test_start_and_stop_market_data_service():
    service = MarketDataService()
    service.collector.update_market_data = AsyncMock()
    service.analyzer.analyze_prices = AsyncMock()
    service.update_interval = 0.1  # speed up for test

    async def stop_service_later():
        await asyncio.sleep(0.3)
        await service.stop()

    stop_task = asyncio.create_task(stop_service_later())
    await service.start()
    await stop_task

    assert not service.running
    service.collector.update_market_data.assert_called()
    service.analyzer.analyze_prices.assert_called()

def test_get_token_price_returns_none_by_default():
    service = MarketDataService()
    price = service.get_token_price("nonexistent_token")
    assert price is None

@pytest.mark.asyncio
async def test_start_handles_exceptions_and_retries():
    service = MarketDataService()
    service.collector.update_market_data = AsyncMock(side_effect=Exception("fail"))
    service.analyzer.analyze_prices = AsyncMock()
    service.update_interval = 0.1

    async def stop_service_later():
        await asyncio.sleep(0.3)
        await service.stop()

    stop_task = asyncio.create_task(stop_service_later())
    await service.start()
    await stop_task

    assert not service.running