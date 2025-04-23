"""
Market data module for the DeFi Arbitrage Trading System.

This module is responsible for collecting and processing market data from various sources,
including DEXs, price oracles, and API providers.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
import asyncio
import json

import requests
from pycoingecko import CoinGeckoAPI
import pandas as pd
from web3 import Web3

from src.config.config import (
    NETWORKS, 
    DEXES, 
    API_KEYS, 
    MIN_LIQUIDITY_THRESHOLD
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("market_data")

class MarketDataCollector:
    """
    Collects market data from various sources and provides a unified interface
    for accessing this data.
    """
    
    def __init__(self):
        """Initialize the market data collector with necessary API clients."""
        self.coingecko = CoinGeckoAPI(api_key=API_KEYS["coingecko"])
        self.web3_clients = {}
        self.initialize_web3_clients()
        self.token_prices = {}
        self.liquidity_pools = {}
        self.last_update = 0
        self.update_interval = 60  # seconds
        
    def initialize_web3_clients(self):
        """Initialize Web3 clients for each enabled network."""
        for network_id, network_config in NETWORKS.items():
            if network_config["enabled"] and network_config["rpc_url"]:
                try:
                    self.web3_clients[network_id] = Web3(Web3.HTTPProvider(network_config["rpc_url"]))
                    logger.info(f"Initialized Web3 client for {network_config['name']}")
                except Exception as e:
                    logger.error(f"Failed to initialize Web3 client for {network_config['name']}: {e}")
    
    async def update_market_data(self):
        """Update all market data sources."""
        current_time = time.time()
        if current_time - self.last_update < self.update_interval:
            logger.debug("Skipping update, not enough time has passed since last update")
            return
        
        try:
            # Update token prices
            await self.update_token_prices()
            
            # Update liquidity pool data
            await self.update_liquidity_pools()
            
            self.last_update = current_time
            logger.info("Market data updated successfully")
        except Exception as e:
            logger.error(f"Error updating market data: {e}")
    
    async def update_token_prices(self):
        """Update token prices from CoinGecko."""
        try:
            # Get top tokens by market cap
            markets = self.coingecko.get_coins_markets(
                vs_currency='usd',
                order='market_cap_desc',
                per_page=250,
                page=1
            )
            
            # Update token prices dictionary
            for token in markets:
                self.token_prices[token['id']] = {
                    'symbol': token['symbol'].upper(),
                    'name': token['name'],
                    'price': token['current_price'],
                    'market_cap': token['market_cap'],
                    'volume_24h': token['total_volume'],
                    'price_change_24h': token['price_change_percentage_24h']
                }
            
            logger.info(f"Updated prices for {len(self.token_prices)} tokens")
        except Exception as e:
            logger.error(f"Error updating token prices: {e}")
    
    async def update_liquidity_pools(self):
        """Update liquidity pool data from DEXs."""
        tasks = []
        
        # Create tasks for each DEX on each network
        for dex_id, dex_config in DEXES.items():
            if dex_config["enabled"]:
                for network_id in dex_config["networks"]:
                    if network_id in self.web3_clients:
                        task = self.fetch_dex_pools(dex_id, network_id)
                        tasks.append(task)
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
    
    async def fetch_dex_pools(self, dex_id: str, network_id: str):
        """Fetch liquidity pools for a specific DEX on a specific network."""
        try:
            # This would normally use DEX-specific API calls or subgraph queries
            # For demonstration, we'll use a placeholder implementation
            
            if dex_id == "uniswap":
                await self.fetch_uniswap_pools(network_id)
            elif dex_id == "curve":
                await self.fetch_curve_pools(network_id)
            elif dex_id == "quickswap":
                await self.fetch_quickswap_pools(network_id)
            # Add more DEX-specific implementations as needed
            
            logger.info(f"Updated liquidity pools for {dex_id} on {network_id}")
        except Exception as e:
            logger.error(f"Error fetching pools for {dex_id} on {network_id}: {e}")
    
    async def fetch_uniswap_pools(self, network_id: str):
        """Fetch Uniswap liquidity pools for a specific network."""
        # In a real implementation, this would query the Uniswap subgraph or contract
        # For demonstration, we'll use a placeholder implementation
        
        # Example structure for storing pool data
        key = f"uniswap_{network_id}"
        if key not in self.liquidity_pools:
            self.liquidity_pools[key] = []
        
        # Placeholder for demonstration
        # In a real implementation, this would be populated with actual pool data
        sample_pools = [
            {
                "id": "0x1234567890abcdef1234567890abcdef12345678",
                "token0": {
                    "id": "0xabcdef1234567890abcdef1234567890abcdef12",
                    "symbol": "WETH",
                    "name": "Wrapped Ether"
                },
                "token1": {
                    "id": "0x1234567890abcdef1234567890abcdef12345678",
                    "symbol": "USDC",
                    "name": "USD Coin"
                },
                "reserve0": 100.5,
                "reserve1": 200000.0,
                "totalSupply": 4500.0,
                "reserveUSD": 300000.0,
                "volumeUSD24h": 1500000.0,
                "feeTier": 0.003
            }
        ]
        
        # Filter pools by minimum liquidity threshold
        filtered_pools = [
            pool for pool in sample_pools 
            if pool["reserveUSD"] >= MIN_LIQUIDITY_THRESHOLD
        ]
        
        self.liquidity_pools[key] = filtered_pools
    
    async def fetch_curve_pools(self, network_id: str):
        """Fetch Curve liquidity pools for a specific network."""
        # Similar placeholder implementation as for Uniswap
        key = f"curve_{network_id}"
        if key not in self.liquidity_pools:
            self.liquidity_pools[key] = []
        
        # Placeholder data
        sample_pools = [
            {
                "id": "0x2345678901abcdef2345678901abcdef23456789",
                "name": "3pool",
                "coins": [
                    {"symbol": "DAI", "address": "0x..."},
                    {"symbol": "USDC", "address": "0x..."},
                    {"symbol": "USDT", "address": "0x..."}
                ],
                "balances": [10000000, 15000000, 12000000],
                "totalSupply": 37000000,
                "virtualPrice": 1.002,
                "volumeUSD24h": 5000000.0,
                "fee": 0.0004
            }
        ]
        
        self.liquidity_pools[key] = sample_pools
    
    async def fetch_quickswap_pools(self, network_id: str):
        """Fetch QuickSwap liquidity pools for a specific network."""
        # Similar placeholder implementation as for Uniswap
        key = f"quickswap_{network_id}"
        if key not in self.liquidity_pools:
            self.liquidity_pools[key] = []
        
        # Placeholder data
        sample_pools = [
            {
                "id": "0x3456789012abcdef3456789012abcdef34567890",
                "token0": {
                    "id": "0xcdef1234567890abcdef1234567890abcdef1234",
                    "symbol": "MATIC",
                    "name": "Polygon"
                },
                "token1": {
                    "id": "0x2345678901abcdef2345678901abcdef23456789",
                    "symbol": "USDC",
                    "name": "USD Coin"
                },
                "reserve0": 500000.0,
                "reserve1": 750000.0,
                "totalSupply": 612000.0,
                "reserveUSD": 1250000.0,
                "volumeUSD24h": 3000000.0,
                "fee": 0.003
            }
        ]
        
        # Filter pools by minimum liquidity threshold
        filtered_pools = [
            pool for pool in sample_pools 
            if pool["reserveUSD"] >= MIN_LIQUIDITY_THRESHOLD
        ]
        
        self.liquidity_pools[key] = filtered_pools
    
    def get_token_price(self, token_id: str) -> Optional[float]:
        """Get the current price of a token by its ID."""
        if token_id in self.token_prices:
            return self.token_prices[token_id]["price"]
        return None
    
    def get_token_prices(self, token_ids: List[str]) -> Dict[str, float]:
        """Get the current prices of multiple tokens by their IDs."""
        return {
            token_id: self.token_prices[token_id]["price"]
            for token_id in token_ids
            if token_id in self.token_prices
        }
    
    def get_liquidity_pools(self, dex_id: str, network_id: str) -> List[Dict]:
        """Get liquidity pools for a specific DEX on a specific network."""
        key = f"{dex_id}_{network_id}"
        return self.liquidity_pools.get(key, [])
    
    def get_all_liquidity_pools(self) -> Dict[str, List[Dict]]:
        """Get all liquidity pools across all DEXs and networks."""
        return self.liquidity_pools
    
    def get_high_volume_pools(self, min_volume: float = 1000000.0) -> List[Dict]:
        """Get high-volume liquidity pools across all DEXs and networks."""
        high_volume_pools = []
        
        for key, pools in self.liquidity_pools.items():
            for pool in pools:
                if "volumeUSD24h" in pool and pool["volumeUSD24h"] >= min_volume:
                    # Add DEX and network information to the pool data
                    dex_id, network_id = key.split("_")
                    pool_with_meta = pool.copy()
                    pool_with_meta["dex_id"] = dex_id
                    pool_with_meta["network_id"] = network_id
                    high_volume_pools.append(pool_with_meta)
        
        # Sort by volume (descending)
        high_volume_pools.sort(key=lambda x: x.get("volumeUSD24h", 0), reverse=True)
        
        return high_volume_pools
    
    def export_data_to_csv(self, directory: str = "data"):
        """Export market data to CSV files for analysis."""
        os.makedirs(directory, exist_ok=True)
        
        # Export token prices
        df_prices = pd.DataFrame.from_dict(self.token_prices, orient="index")
        df_prices.to_csv(os.path.join(directory, "token_prices.csv"))
        
        # Export liquidity pools
        for key, pools in self.liquidity_pools.items():
            if pools:
                df_pools = pd.DataFrame(pools)
                df_pools.to_csv(os.path.join(directory, f"{key}_pools.csv"))
        
        logger.info(f"Exported market data to {directory}")
    
    def export_data_to_json(self, directory: str = "data"):
        """Export market data to JSON files for analysis."""
        os.makedirs(directory, exist_ok=True)
        
        # Export token prices
        with open(os.path.join(directory, "token_prices.json"), "w") as f:
            json.dump(self.token_prices, f, indent=2)
        
        # Export liquidity pools
        with open(os.path.join(directory, "liquidity_pools.json"), "w") as f:
            json.dump(self.liquidity_pools, f, indent=2)
        
        logger.info(f"Exported market data to {directory}")


# Example usage
async def main():
    collector = MarketDataCollector()
    await collector.update_market_data()
    
    # Get high-volume pools
    high_volume_pools = collector.get_high_volume_pools()
    print(f"Found {len(high_volume_pools)} high-volume pools")
    
    # Export data
    collector.export_data_to_json()

if __name__ == "__main__":
    asyncio.run(main())
