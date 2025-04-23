"""
Price analyzer for the DeFi Arbitrage Trading System.

This module analyzes price data across different DEXs and networks to identify
potential arbitrage opportunities.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import asyncio
import time

from src.config.config import MIN_PROFIT_THRESHOLD
from src.market_data.collector import MarketDataCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("market_data.analyzer")

class PriceAnalyzer:
    """
    Analyzes price data to identify arbitrage opportunities across DEXs and networks.
    """
    
    def __init__(self, data_collector: MarketDataCollector):
        """Initialize the price analyzer with a market data collector."""
        self.data_collector = data_collector
        self.price_discrepancies = []
        self.last_analysis = 0
        self.analysis_interval = 30  # seconds
    
    async def analyze_prices(self):
        """Analyze prices across DEXs and networks to identify arbitrage opportunities."""
        current_time = time.time()
        if current_time - self.last_analysis < self.analysis_interval:
            logger.debug("Skipping analysis, not enough time has passed since last analysis")
            return
        
        # Ensure market data is up to date
        await self.data_collector.update_market_data()
        
        try:
            # Clear previous discrepancies
            self.price_discrepancies = []
            
            # Get all liquidity pools
            all_pools = self.data_collector.get_all_liquidity_pools()
            
            # Analyze price discrepancies across DEXs and networks
            await self.analyze_cross_dex_opportunities(all_pools)
            
            # Analyze triangular arbitrage opportunities
            await self.analyze_triangular_opportunities(all_pools)
            
            self.last_analysis = current_time
            logger.info(f"Price analysis completed, found {len(self.price_discrepancies)} potential opportunities")
        except Exception as e:
            logger.error(f"Error analyzing prices: {e}")
    
    async def analyze_cross_dex_opportunities(self, all_pools: Dict[str, List[Dict]]):
        """Analyze price discrepancies for the same token pair across different DEXs."""
        # Create a mapping of token pairs to their prices across different DEXs
        pair_prices = {}
        
        # Iterate through all pools and extract price information
        for key, pools in all_pools.items():
            dex_id, network_id = key.split("_")
            
            for pool in pools:
                # For Uniswap-like pools
                if "token0" in pool and "token1" in pool and "reserve0" in pool and "reserve1" in pool:
                    token0 = pool["token0"]["symbol"]
                    token1 = pool["token1"]["symbol"]
                    
                    # Calculate price (token1 per token0)
                    price = pool["reserve1"] / pool["reserve0"] if pool["reserve0"] > 0 else 0
                    
                    # Create a unique key for this token pair
                    pair_key = f"{token0}_{token1}"
                    
                    # Store price information
                    if pair_key not in pair_prices:
                        pair_prices[pair_key] = []
                    
                    pair_prices[pair_key].append({
                        "dex_id": dex_id,
                        "network_id": network_id,
                        "pool_id": pool["id"],
                        "price": price,
                        "reserve0": pool["reserve0"],
                        "reserve1": pool["reserve1"],
                        "reserveUSD": pool.get("reserveUSD", 0),
                        "fee": pool.get("feeTier", 0.003)  # Default to 0.3% if not specified
                    })
                
                # For Curve-like pools (multi-token)
                elif "coins" in pool and "balances" in pool:
                    # Curve pools are more complex, but we can still extract some price information
                    # For simplicity, we'll just look at pairs of tokens within the pool
                    coins = pool["coins"]
                    balances = pool["balances"]
                    
                    for i in range(len(coins) - 1):
                        for j in range(i + 1, len(coins)):
                            token_i = coins[i]["symbol"]
                            token_j = coins[j]["symbol"]
                            
                            # Calculate price (token_j per token_i)
                            price = balances[j] / balances[i] if balances[i] > 0 else 0
                            
                            # Create a unique key for this token pair
                            pair_key = f"{token_i}_{token_j}"
                            
                            # Store price information
                            if pair_key not in pair_prices:
                                pair_prices[pair_key] = []
                            
                            pair_prices[pair_key].append({
                                "dex_id": dex_id,
                                "network_id": network_id,
                                "pool_id": pool["id"],
                                "price": price,
                                "reserve_i": balances[i],
                                "reserve_j": balances[j],
                                "fee": pool.get("fee", 0.0004)  # Default to 0.04% if not specified
                            })
        
        # Analyze price discrepancies for each token pair
        for pair_key, prices in pair_prices.items():
            if len(prices) < 2:
                continue  # Need at least two prices to compare
            
            # Find the lowest and highest prices
            lowest_price = min(prices, key=lambda x: x["price"])
            highest_price = max(prices, key=lambda x: x["price"])
            
            # Calculate the price difference percentage
            price_diff_pct = (highest_price["price"] - lowest_price["price"]) / lowest_price["price"]
            
            # Calculate estimated fees
            buy_fee = lowest_price["fee"]
            sell_fee = highest_price["fee"]
            
            # Estimate gas costs (this would be more accurate in a real implementation)
            estimated_gas_cost_pct = 0.001  # 0.1% as a placeholder
            
            # Calculate net profit after fees and gas costs
            net_profit_pct = price_diff_pct - buy_fee - sell_fee - estimated_gas_cost_pct
            
            # If the net profit exceeds our threshold, record this opportunity
            if net_profit_pct >= MIN_PROFIT_THRESHOLD:
                token0, token1 = pair_key.split("_")
                
                opportunity = {
                    "type": "cross_dex",
                    "token_pair": pair_key,
                    "token0": token0,
                    "token1": token1,
                    "buy_dex": lowest_price["dex_id"],
                    "buy_network": lowest_price["network_id"],
                    "buy_pool": lowest_price["pool_id"],
                    "buy_price": lowest_price["price"],
                    "sell_dex": highest_price["dex_id"],
                    "sell_network": highest_price["network_id"],
                    "sell_pool": highest_price["pool_id"],
                    "sell_price": highest_price["price"],
                    "price_diff_pct": price_diff_pct,
                    "buy_fee": buy_fee,
                    "sell_fee": sell_fee,
                    "estimated_gas_cost_pct": estimated_gas_cost_pct,
                    "net_profit_pct": net_profit_pct,
                    "timestamp": time.time()
                }
                
                self.price_discrepancies.append(opportunity)
                logger.info(f"Found cross-DEX opportunity: {token0}/{token1} - Buy on {lowest_price['dex_id']} ({lowest_price['network_id']}), "
                           f"Sell on {highest_price['dex_id']} ({highest_price['network_id']}), Net profit: {net_profit_pct:.2%}")
    
    async def analyze_triangular_opportunities(self, all_pools: Dict[str, List[Dict]]):
        """Analyze triangular arbitrage opportunities within a single DEX."""
        # For each DEX and network combination
        for key, pools in all_pools.items():
            dex_id, network_id = key.split("_")
            
            # Skip if there are not enough pools for triangular arbitrage
            if len(pools) < 3:
                continue
            
            # Create a mapping of tokens to their connected tokens and prices
            token_graph = {}
            
            # Build the token graph
            for pool in pools:
                # For Uniswap-like pools
                if "token0" in pool and "token1" in pool and "reserve0" in pool and "reserve1" in pool:
                    token0 = pool["token0"]["symbol"]
                    token1 = pool["token1"]["symbol"]
                    
                    # Calculate prices in both directions
                    price_0_to_1 = pool["reserve1"] / pool["reserve0"] if pool["reserve0"] > 0 else 0
                    price_1_to_0 = pool["reserve0"] / pool["reserve1"] if pool["reserve1"] > 0 else 0
                    
                    # Add to token graph
                    if token0 not in token_graph:
                        token_graph[token0] = {}
                    if token1 not in token_graph:
                        token_graph[token1] = {}
                    
                    token_graph[token0][token1] = {
                        "price": price_0_to_1,
                        "pool_id": pool["id"],
                        "fee": pool.get("feeTier", 0.003)
                    }
                    
                    token_graph[token1][token0] = {
                        "price": price_1_to_0,
                        "pool_id": pool["id"],
                        "fee": pool.get("feeTier", 0.003)
                    }
            
            # Look for triangular arbitrage opportunities
            for token_a in token_graph:
                for token_b in token_graph.get(token_a, {}):
                    for token_c in token_graph.get(token_b, {}):
                        # Check if we can complete the triangle
                        if token_c in token_graph and token_a in token_graph.get(token_c, {}):
                            # Calculate the product of prices
                            price_a_to_b = token_graph[token_a][token_b]["price"]
                            price_b_to_c = token_graph[token_b][token_c]["price"]
                            price_c_to_a = token_graph[token_c][token_a]["price"]
                            
                            # Calculate the round-trip rate
                            round_trip_rate = price_a_to_b * price_b_to_c * price_c_to_a
                            
                            # Calculate fees
                            fee_a_to_b = token_graph[token_a][token_b]["fee"]
                            fee_b_to_c = token_graph[token_b][token_c]["fee"]
                            fee_c_to_a = token_graph[token_c][token_a]["fee"]
                            total_fee = fee_a_to_b + fee_b_to_c + fee_c_to_a
                            
                            # Estimate gas costs
                            estimated_gas_cost_pct = 0.002  # 0.2% as a placeholder for 3 transactions
                            
                            # Calculate net profit
                            net_profit_pct = round_trip_rate - 1 - total_fee - estimated_gas_cost_pct
                            
                            # If the net profit exceeds our threshold, record this opportunity
                            if net_profit_pct >= MIN_PROFIT_THRESHOLD:
                                opportunity = {
                                    "type": "triangular",
                                    "dex_id": dex_id,
                                    "network_id": network_id,
                                    "token_a": token_a,
                                    "token_b": token_b,
                                    "token_c": token_c,
                                    "price_a_to_b": price_a_to_b,
                                    "price_b_to_c": price_b_to_c,
                                    "price_c_to_a": price_c_to_a,
                                    "round_trip_rate": round_trip_rate,
                                    "pool_a_to_b": token_graph[token_a][token_b]["pool_id"],
                                    "pool_b_to_c": token_graph[token_b][token_c]["pool_id"],
                                    "pool_c_to_a": token_graph[token_c][token_a]["pool_id"],
                                    "total_fee": total_fee,
                                    "estimated_gas_cost_pct": estimated_gas_cost_pct,
                                    "net_profit_pct": net_profit_pct,
                                    "timestamp": time.time()
                                }
                                
                                self.price_discrepancies.append(opportunity)
                                logger.info(f"Found triangular opportunity on {dex_id} ({network_id}): "
                                           f"{token_a} -> {token_b} -> {token_c} -> {token_a}, "
                                           f"Net profit: {net_profit_pct:.2%}")
    
    def get_arbitrage_opportunities(self, min_profit: float = MIN_PROFIT_THRESHOLD, limit: int = 10):
        """Get the top arbitrage opportunities sorted by profit potential."""
        # Filter opportunities by minimum profit
        filtered_opportunities = [
            opp for opp in self.price_discrepancies
            if opp["net_profit_pct"] >= min_profit
        ]
        
        # Sort by net profit (descending)
        sorted_opportunities = sorted(
            filtered_opportunities,
            key=lambda x: x["net_profit_pct"],
            reverse=True
        )
        
        # Return the top opportunities
        return sorted_opportunities[:limit]


# Example usage
async def main():
    data_collector = MarketDataCollector()
    analyzer = PriceAnalyzer(data_collector)
    
    # Analyze prices
    await analyzer.analyze_prices()
    
    # Get top arbitrage opportunities
    opportunities = analyzer.get_arbitrage_opportunities()
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

if __name__ == "__main__":
    asyncio.run(main())
