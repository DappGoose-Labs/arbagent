"""
Main entry point for the market data module.

This file initializes the market data collector and analyzer, and provides
a unified interface for accessing market data and arbitrage opportunities.
"""

import asyncio
import logging
from typing import Dict, List, Optional

from src.market_data.collector import MarketDataCollector
from src.market_data.analyzer import PriceAnalyzer
from src.config.config import MIN_PROFIT_THRESHOLD

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("market_data")

class MarketDataService:
    """
    Service that provides access to market data and arbitrage opportunities.
    """
    
    def __init__(self):
        """Initialize the market data service."""
        self.collector = MarketDataCollector()
        self.analyzer = PriceAnalyzer(self.collector)
        self.running = False
        self.update_interval = 60  # seconds
    
    async def start(self):
        """Start the market data service."""
        self.running = True
        logger.info("Starting market data service")
        
        while self.running:
            try:
                # Update market data
                await self.collector.update_market_data()
                
                # Analyze prices for arbitrage opportunities
                await self.analyzer.analyze_prices()
                
                # Wait for the next update
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in market data service: {e}")
                await asyncio.sleep(5)  # Wait a bit before retrying
    
    async def stop(self):
        """Stop the market data service."""
        self.running = False
        logger.info("Stopping market data service")
    
    def get_token_price(self, token_id: str) -> Optional[float]:
        """Get the current price of a token by its ID."""
        return self.collector.get_token_price(token_id)
    
    def get_token_prices(self, token_ids: List[str]) -> Dict[str, float]:
        """Get the current prices of multiple tokens by their IDs."""
        return self.collector.get_token_prices(token_ids)
    
    def get_liquidity_pools(self, dex_id: str, network_id: str) -> List[Dict]:
        """Get liquidity pools for a specific DEX on a specific network."""
        return self.collector.get_liquidity_pools(dex_id, network_id)
    
    def get_high_volume_pools(self, min_volume: float = 1000000.0) -> List[Dict]:
        """Get high-volume liquidity pools across all DEXs and networks."""
        return self.collector.get_high_volume_pools(min_volume)
    
    def get_arbitrage_opportunities(self, min_profit: float = MIN_PROFIT_THRESHOLD, limit: int = 10) -> List[Dict]:
        """Get the top arbitrage opportunities sorted by profit potential."""
        return self.analyzer.get_arbitrage_opportunities(min_profit, limit)
    
    def export_data(self, format: str = "json", directory: str = "data"):
        """Export market data for analysis."""
        if format.lower() == "csv":
            self.collector.export_data_to_csv(directory)
        else:
            self.collector.export_data_to_json(directory)


# Example usage
async def main():
    # Initialize the market data service
    service = MarketDataService()
    
    try:
        # Start the service in the background
        service_task = asyncio.create_task(service.start())
        
        # Wait for initial data to be collected and analyzed
        await asyncio.sleep(5)
        
        # Get arbitrage opportunities
        opportunities = service.get_arbitrage_opportunities()
        print(f"Found {len(opportunities)} profitable arbitrage opportunities")
        
        # Print details of top opportunities
        for i, opp in enumerate(opportunities[:3], 1):
            print(f"\nOpportunity {i}:")
            if opp["type"] == "cross_dex":
                print(f"  Type: Cross-DEX")
                print(f"  Token Pair: {opp['token0']}/{opp['token1']}")
                print(f"  Buy: {opp['buy_dex']} on {opp['buy_network']} at {opp['buy_price']}")
                print(f"  Sell: {opp['sell_dex']} on {opp['sell_network']} at {opp['sell_price']}")
            else:  # triangular
                print(f"  Type: Triangular")
                print(f"  DEX: {opp['dex_id']} on {opp['network_id']}")
                print(f"  Path: {opp['token_a']} -> {opp['token_b']} -> {opp['token_c']} -> {opp['token_a']}")
                print(f"  Round-trip rate: {opp['round_trip_rate']:.4f}")
            
            print(f"  Net Profit: {opp['net_profit_pct']:.2%}")
        
        # Export data for analysis
        service.export_data()
        
        # Run for a while to collect more data
        await asyncio.sleep(60)
    finally:
        # Stop the service
        await service.stop()
        service_task.cancel()
        try:
            await service_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(main())
