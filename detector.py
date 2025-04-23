"""
Arbitrage detection module for the DeFi Arbitrage Trading System.

This module builds on the market data module to identify, validate, and prioritize
arbitrage opportunities across DEXs and blockchain networks.
"""

import logging
import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
import json
import os

from src.market_data import MarketDataService
from src.config.config import MIN_PROFIT_THRESHOLD, MIN_LIQUIDITY_THRESHOLD

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("arbitrage_detection")

class ArbitrageDetector:
    """
    Detects and validates arbitrage opportunities across DEXs and networks.
    """
    
    def __init__(self, market_data_service: MarketDataService):
        """Initialize the arbitrage detector with a market data service."""
        self.market_data = market_data_service
        self.opportunities = []
        self.validated_opportunities = []
        self.last_detection = 0
        self.detection_interval = 30  # seconds
        self.min_profit_threshold = MIN_PROFIT_THRESHOLD
        self.min_liquidity = MIN_LIQUIDITY_THRESHOLD
    
    async def start_detection(self):
        """Start continuous arbitrage detection."""
        logger.info("Starting arbitrage detection")
        
        while True:
            try:
                await self.detect_opportunities()
                await asyncio.sleep(self.detection_interval)
            except Exception as e:
                logger.error(f"Error in arbitrage detection: {e}")
                await asyncio.sleep(5)  # Wait a bit before retrying
    
    async def detect_opportunities(self):
        """Detect arbitrage opportunities using market data."""
        current_time = time.time()
        if current_time - self.last_detection < self.detection_interval:
            logger.debug("Skipping detection, not enough time has passed since last detection")
            return
        
        try:
            # Get arbitrage opportunities from market data service
            raw_opportunities = self.market_data.get_arbitrage_opportunities(
                min_profit=self.min_profit_threshold
            )
            
            # Store raw opportunities
            self.opportunities = raw_opportunities
            
            # Validate and prioritize opportunities
            await self.validate_opportunities()
            
            self.last_detection = current_time
            logger.info(f"Detected {len(self.opportunities)} opportunities, "
                       f"{len(self.validated_opportunities)} validated")
        except Exception as e:
            logger.error(f"Error detecting arbitrage opportunities: {e}")
    
    async def validate_opportunities(self):
        """Validate arbitrage opportunities by checking additional constraints."""
        validated = []
        
        for opp in self.opportunities:
            try:
                # Apply additional validation logic
                is_valid, validation_details = await self.validate_opportunity(opp)
                
                if is_valid:
                    # Add validation details to the opportunity
                    validated_opp = {**opp, **validation_details}
                    validated.append(validated_opp)
            except Exception as e:
                logger.error(f"Error validating opportunity: {e}")
        
        # Sort validated opportunities by expected profit
        validated.sort(key=lambda x: x.get("expected_profit_usd", 0), reverse=True)
        
        self.validated_opportunities = validated
    
    async def validate_opportunity(self, opportunity: Dict) -> Tuple[bool, Dict]:
        """
        Validate a single arbitrage opportunity.
        
        Returns:
            Tuple[bool, Dict]: A tuple containing a boolean indicating if the opportunity
                is valid, and a dictionary with additional validation details.
        """
        validation_details = {
            "validation_timestamp": time.time(),
            "is_valid": False,
            "validation_message": "",
            "expected_profit_usd": 0,
            "max_trade_size_usd": 0,
            "optimal_trade_size_usd": 0,
            "estimated_execution_time_ms": 0,
            "risk_score": 0  # 0-100, higher is riskier
        }
        
        try:
            # Different validation logic based on opportunity type
            if opportunity["type"] == "cross_dex":
                return await self.validate_cross_dex_opportunity(opportunity, validation_details)
            elif opportunity["type"] == "triangular":
                return await self.validate_triangular_opportunity(opportunity, validation_details)
            else:
                validation_details["validation_message"] = f"Unknown opportunity type: {opportunity['type']}"
                return False, validation_details
        except Exception as e:
            validation_details["validation_message"] = f"Validation error: {str(e)}"
            return False, validation_details
    
    async def validate_cross_dex_opportunity(self, opportunity: Dict, validation_details: Dict) -> Tuple[bool, Dict]:
        """Validate a cross-DEX arbitrage opportunity."""
        # Check if the tokens are supported
        token0, token1 = opportunity["token0"], opportunity["token1"]
        
        # Get current token prices (in a real implementation, this would use actual token IDs)
        token0_price = self.market_data.get_token_price(token0.lower()) or 1.0
        token1_price = self.market_data.get_token_price(token1.lower()) or 1.0
        
        # Check liquidity on both DEXs
        buy_pool = self.get_pool_details(
            opportunity["buy_dex"], 
            opportunity["buy_network"], 
            opportunity["buy_pool"]
        )
        
        sell_pool = self.get_pool_details(
            opportunity["sell_dex"], 
            opportunity["sell_network"], 
            opportunity["sell_pool"]
        )
        
        if not buy_pool or not sell_pool:
            validation_details["validation_message"] = "Could not retrieve pool details"
            return False, validation_details
        
        # Check minimum liquidity
        buy_liquidity_usd = buy_pool.get("reserveUSD", 0)
        sell_liquidity_usd = sell_pool.get("reserveUSD", 0)
        
        if buy_liquidity_usd < self.min_liquidity or sell_liquidity_usd < self.min_liquidity:
            validation_details["validation_message"] = "Insufficient liquidity"
            return False, validation_details
        
        # Calculate maximum trade size (limited by the smaller pool)
        max_trade_size_usd = min(buy_liquidity_usd, sell_liquidity_usd) * 0.05  # Limit to 5% of pool size
        
        # Calculate optimal trade size based on price impact
        optimal_trade_size_usd = self.calculate_optimal_trade_size(
            buy_liquidity_usd, 
            sell_liquidity_usd,
            opportunity["net_profit_pct"]
        )
        
        # Calculate expected profit
        expected_profit_usd = optimal_trade_size_usd * opportunity["net_profit_pct"]
        
        # Calculate risk score
        risk_score = self.calculate_risk_score(
            opportunity["net_profit_pct"],
            buy_liquidity_usd,
            sell_liquidity_usd,
            opportunity["buy_network"] != opportunity["sell_network"]
        )
        
        # Estimate execution time
        estimated_execution_time_ms = self.estimate_execution_time(
            opportunity["buy_network"],
            opportunity["sell_network"]
        )
        
        # Update validation details
        validation_details.update({
            "is_valid": True,
            "validation_message": "Opportunity validated successfully",
            "expected_profit_usd": expected_profit_usd,
            "max_trade_size_usd": max_trade_size_usd,
            "optimal_trade_size_usd": optimal_trade_size_usd,
            "estimated_execution_time_ms": estimated_execution_time_ms,
            "risk_score": risk_score,
            "token0_price_usd": token0_price,
            "token1_price_usd": token1_price,
            "buy_liquidity_usd": buy_liquidity_usd,
            "sell_liquidity_usd": sell_liquidity_usd
        })
        
        return True, validation_details
    
    async def validate_triangular_opportunity(self, opportunity: Dict, validation_details: Dict) -> Tuple[bool, Dict]:
        """Validate a triangular arbitrage opportunity."""
        # Get pool details for each leg of the triangle
        pool_a_to_b = self.get_pool_details(
            opportunity["dex_id"], 
            opportunity["network_id"], 
            opportunity["pool_a_to_b"]
        )
        
        pool_b_to_c = self.get_pool_details(
            opportunity["dex_id"], 
            opportunity["network_id"], 
            opportunity["pool_b_to_c"]
        )
        
        pool_c_to_a = self.get_pool_details(
            opportunity["dex_id"], 
            opportunity["network_id"], 
            opportunity["pool_c_to_a"]
        )
        
        if not pool_a_to_b or not pool_b_to_c or not pool_c_to_a:
            validation_details["validation_message"] = "Could not retrieve pool details"
            return False, validation_details
        
        # Check minimum liquidity for each pool
        liquidity_a_to_b = pool_a_to_b.get("reserveUSD", 0)
        liquidity_b_to_c = pool_b_to_c.get("reserveUSD", 0)
        liquidity_c_to_a = pool_c_to_a.get("reserveUSD", 0)
        
        min_liquidity = min(liquidity_a_to_b, liquidity_b_to_c, liquidity_c_to_a)
        
        if min_liquidity < self.min_liquidity:
            validation_details["validation_message"] = "Insufficient liquidity"
            return False, validation_details
        
        # Calculate maximum trade size (limited by the smallest pool)
        max_trade_size_usd = min_liquidity * 0.03  # Limit to 3% of smallest pool size
        
        # Calculate optimal trade size based on price impact
        optimal_trade_size_usd = self.calculate_optimal_trade_size_triangular(
            liquidity_a_to_b,
            liquidity_b_to_c,
            liquidity_c_to_a,
            opportunity["round_trip_rate"] - 1  # Convert to percentage gain
        )
        
        # Calculate expected profit
        expected_profit_usd = optimal_trade_size_usd * (opportunity["round_trip_rate"] - 1 - opportunity["total_fee"])
        
        # Calculate risk score
        risk_score = self.calculate_risk_score_triangular(
            opportunity["round_trip_rate"] - 1,
            liquidity_a_to_b,
            liquidity_b_to_c,
            liquidity_c_to_a
        )
        
        # Estimate execution time
        estimated_execution_time_ms = self.estimate_execution_time_triangular(
            opportunity["network_id"]
        )
        
        # Update validation details
        validation_details.update({
            "is_valid": True,
            "validation_message": "Opportunity validated successfully",
            "expected_profit_usd": expected_profit_usd,
            "max_trade_size_usd": max_trade_size_usd,
            "optimal_trade_size_usd": optimal_trade_size_usd,
            "estimated_execution_time_ms": estimated_execution_time_ms,
            "risk_score": risk_score,
            "liquidity_a_to_b": liquidity_a_to_b,
            "liquidity_b_to_c": liquidity_b_to_c,
            "liquidity_c_to_a": liquidity_c_to_a
        })
        
        return True, validation_details
    
    def get_pool_details(self, dex_id: str, network_id: str, pool_id: str) -> Optional[Dict]:
        """Get details for a specific liquidity pool."""
        # In a real implementation, this would query the market data service
        # For demonstration, we'll return placeholder data
        
        # Get pools for the specified DEX and network
        pools = self.market_data.get_liquidity_pools(dex_id, network_id)
        
        # Find the pool with the matching ID
        for pool in pools:
            if pool.get("id") == pool_id:
                return pool
        
        # If pool not found, return placeholder data
        return {
            "id": pool_id,
            "reserveUSD": 500000,  # $500k liquidity
            "volumeUSD24h": 1000000  # $1M daily volume
        }
    
    def calculate_optimal_trade_size(self, buy_liquidity: float, sell_liquidity: float, profit_pct: float) -> float:
        """Calculate the optimal trade size based on liquidity and expected profit."""
        # A simple model: optimal size increases with liquidity and profit percentage
        # In a real implementation, this would use a more sophisticated model
        
        # Base size: 0.5% of the smaller liquidity pool
        base_size = min(buy_liquidity, sell_liquidity) * 0.005
        
        # Adjust based on profit percentage (higher profit allows larger trades)
        profit_multiplier = 1 + (profit_pct * 10)  # e.g., 1% profit gives 1.1x multiplier
        
        # Cap at 5% of the smaller pool
        max_size = min(buy_liquidity, sell_liquidity) * 0.05
        
        optimal_size = min(base_size * profit_multiplier, max_size)
        
        return optimal_size
    
    def calculate_optimal_trade_size_triangular(self, liquidity_a_to_b: float, liquidity_b_to_c: float, 
                                              liquidity_c_to_a: float, profit_pct: float) -> float:
        """Calculate the optimal trade size for triangular arbitrage."""
        # Base size: 0.3% of the smallest liquidity pool
        base_size = min(liquidity_a_to_b, liquidity_b_to_c, liquidity_c_to_a) * 0.003
        
        # Adjust based on profit percentage
        profit_multiplier = 1 + (profit_pct * 8)  # e.g., 1% profit gives 1.08x multiplier
        
        # Cap at 3% of the smallest pool
        max_size = min(liquidity_a_to_b, liquidity_b_to_c, liquidity_c_to_a) * 0.03
        
        optimal_size = min(base_size * profit_multiplier, max_size)
        
        return optimal_size
    
    def calculate_risk_score(self, profit_pct: float, buy_liquidity: float, sell_liquidity: float, 
                           cross_network: bool) -> float:
        """Calculate a risk score for a cross-DEX opportunity."""
        # Base risk score: 50
        risk_score = 50
        
        # Adjust based on profit percentage (higher profit often means higher risk)
        risk_score += profit_pct * 1000  # e.g., 1% profit adds 10 to risk score
        
        # Adjust based on liquidity (lower liquidity means higher risk)
        min_liquidity = min(buy_liquidity, sell_liquidity)
        if min_liquidity < 100000:  # Less than $100k
            risk_score += 20
        elif min_liquidity < 500000:  # Less than $500k
            risk_score += 10
        elif min_liquidity < 1000000:  # Less than $1M
            risk_score += 5
        
        # Adjust for cross-network trades (adds complexity and risk)
        if cross_network:
            risk_score += 15
        
        # Cap at 0-100
        return max(0, min(100, risk_score))
    
    def calculate_risk_score_triangular(self, profit_pct: float, liquidity_a_to_b: float, 
                                      liquidity_b_to_c: float, liquidity_c_to_a: float) -> float:
        """Calculate a risk score for a triangular arbitrage opportunity."""
        # Base risk score: 40 (generally lower than cross-DEX due to single network)
        risk_score = 40
        
        # Adjust based on profit percentage
        risk_score += profit_pct * 1200  # e.g., 1% profit adds 12 to risk score
        
        # Adjust based on liquidity
        min_liquidity = min(liquidity_a_to_b, liquidity_b_to_c, liquidity_c_to_a)
        if min_liquidity < 100000:  # Less than $100k
            risk_score += 25
        elif min_liquidi
(Content truncated due to size limit. Use line ranges to read in chunks)