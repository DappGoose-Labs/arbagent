import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from detector import ArbitrageDetector

class DummyMarketDataService:
    def __init__(self):
        self.called = False
    def get_arbitrage_opportunities(self, min_profit):
        self.called = True
        return [{"id": 1, "profit": 0.05}]

@pytest.mark.asyncio
async def test_detect_opportunities_and_validation():
    market_data = DummyMarketDataService()
    detector = ArbitrageDetector(market_data)
    detector.validate_opportunities = AsyncMock()
    detector.last_detection = 0
    detector.detection_interval = 0.1

    await detector.detect_opportunities()
    assert market_data.called
    detector.validate_opportunities.assert_awaited()

@pytest.mark.asyncio
async def test_start_detection_runs_and_handles_exceptions():
    market_data = DummyMarketDataService()
    detector = ArbitrageDetector(market_data)
    detector.detect_opportunities = AsyncMock(side_effect=[None, Exception("fail"), None])
    detector.detection_interval = 0.1

    async def stop_after_delay():
        await asyncio.sleep(0.3)
        detector.detection_interval = 1000  # stop loop

    stop_task = asyncio.create_task(stop_after_delay())
    await detector.start_detection()
    await stop_task

@pytest.mark.asyncio
async def test_validate_opportunities_empty():
    detector = ArbitrageDetector(MagicMock())
    detector.opportunities = []
    await detector.validate_opportunities()
    assert detector.validated_opportunities == []