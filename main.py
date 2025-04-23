"""
Main entry point for the DeFi Arbitrage Trading System.

This file integrates all components of the system and provides a unified interface
for running the complete arbitrage trading system.
"""

import asyncio
import logging
import os
import json
import time
from typing import Dict, List, Optional

from src.market_data import MarketDataService
from src.arbitrage_detection import ArbitrageService
from src.trade_simulation import TradeSimulationService
from src.flashloan_execution import FlashloanExecutionService
from src.config.config import MIN_PROFIT_THRESHOLD

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("arbitrage_system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("arbitrage_system")

class ArbitrageSystem:
    """
    Main class that integrates all components of the DeFi Arbitrage Trading System.
    """
    
    def __init__(self):
        """Initialize the arbitrage system."""
        logger.info("Initializing DeFi Arbitrage Trading System")
        
        # Initialize all services
        self.market_data = MarketDataService()
        self.arbitrage_service = ArbitrageService(self.market_data)
        self.simulation_service = TradeSimulationService(self.arbitrage_service)
        self.execution_service = FlashloanExecutionService(self.simulation_service)
        
        # System state
        self.running = False
        self.auto_execute = False
        self.min_profit_threshold = MIN_PROFIT_THRESHOLD
        self.system_start_time = 0
        self.stats = {
            "opportunities_detected": 0,
            "trades_simulated": 0,
            "trades_executed": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_profit_usd": 0,
            "total_fees_usd": 0,
            "total_gas_cost_usd": 0
        }
    
    async def start(self, auto_execute: bool = False):
        """
        Start the arbitrage system.
        
        Args:
            auto_execute: Whether to automatically execute profitable trades.
        """
        if self.running:
            logger.warning("System is already running")
            return
        
        self.running = True
        self.auto_execute = auto_execute
        self.system_start_time = time.time()
        
        logger.info(f"Starting DeFi Arbitrage Trading System (auto_execute={auto_execute})")
        
        # Start all services
        market_data_task = asyncio.create_task(self.market_data.start())
        arbitrage_task = asyncio.create_task(self.arbitrage_service.start())
        simulation_task = asyncio.create_task(self.simulation_service.start())
        
        # Only start execution service if auto_execute is enabled
        execution_task = None
        if auto_execute:
            execution_task = asyncio.create_task(self.execution_service.start())
            logger.info("Auto-execution enabled, execution service started")
        else:
            logger.info("Auto-execution disabled, trades will be simulated but not executed")
        
        # Start the monitoring loop
        monitor_task = asyncio.create_task(self._monitor_system())
        
        try:
            # Keep the system running until stopped
            while self.running:
                await asyncio.sleep(1)
        finally:
            # Stop all services
            logger.info("Stopping all services")
            
            if execution_task:
                await self.execution_service.stop()
                execution_task.cancel()
            
            await self.simulation_service.stop()
            await self.arbitrage_service.stop()
            await self.market_data.stop()
            
            monitor_task.cancel()
            
            try:
                if execution_task:
                    await execution_task
                await simulation_task
                await arbitrage_task
                await market_data_task
                await monitor_task
            except asyncio.CancelledError:
                pass
            
            self.running = False
            logger.info("DeFi Arbitrage Trading System stopped")
    
    async def stop(self):
        """Stop the arbitrage system."""
        if not self.running:
            logger.warning("System is not running")
            return
        
        logger.info("Stopping DeFi Arbitrage Trading System")
        self.running = False
    
    async def _monitor_system(self):
        """Monitor the system and update statistics."""
        logger.info("Starting system monitoring")
        
        while self.running:
            try:
                # Update statistics
                await self._update_stats()
                
                # Log current system status
                await self._log_system_status()
                
                # Export data for analysis
                self._export_data()
                
                # Wait before next update
                await asyncio.sleep(60)  # Update every minute
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _update_stats(self):
        """Update system statistics."""
        try:
            # Get current data
            opportunities = self.arbitrage_service.get_all_opportunities()
            simulations = self.simulation_service.get_all_simulations()
            executions = self.execution_service.get_execution_results()
            successful = self.execution_service.get_successful_executions()
            
            # Update statistics
            self.stats["opportunities_detected"] = len(opportunities)
            self.stats["trades_simulated"] = len(simulations)
            self.stats["trades_executed"] = len(executions)
            self.stats["successful_trades"] = len(successful)
            self.stats["failed_trades"] = len(executions) - len(successful)
            
            # Calculate financial metrics
            total_profit = sum(trade.get("profit_usd", 0) for trade in successful)
            total_fees = sum(trade.get("flashloan_fee", 0) for trade in successful)
            total_gas = sum(trade.get("gas_cost_usd", 0) for trade in successful)
            
            self.stats["total_profit_usd"] = total_profit
            self.stats["total_fees_usd"] = total_fees
            self.stats["total_gas_cost_usd"] = total_gas
            
            # Calculate runtime
            runtime = time.time() - self.system_start_time
            self.stats["runtime_seconds"] = runtime
            
            # Calculate performance metrics
            if runtime > 0:
                self.stats["opportunities_per_hour"] = opportunities / (runtime / 3600)
                self.stats["profit_per_hour"] = total_profit / (runtime / 3600)
            
            if len(successful) > 0:
                self.stats["avg_profit_per_trade"] = total_profit / len(successful)
                self.stats["avg_gas_cost_per_trade"] = total_gas / len(successful)
            
            if len(executions) > 0:
                self.stats["success_rate"] = len(successful) / len(executions)
        except Exception as e:
            logger.error(f"Error updating stats: {e}")
    
    async def _log_system_status(self):
        """Log current system status."""
        runtime_hours = self.stats.get("runtime_seconds", 0) / 3600
        
        logger.info(f"System Status (Runtime: {runtime_hours:.2f} hours):")
        logger.info(f"  Opportunities Detected: {self.stats['opportunities_detected']}")
        logger.info(f"  Trades Simulated: {self.stats['trades_simulated']}")
        logger.info(f"  Trades Executed: {self.stats['trades_executed']}")
        logger.info(f"  Successful Trades: {self.stats['successful_trades']}")
        logger.info(f"  Failed Trades: {self.stats['failed_trades']}")
        logger.info(f"  Total Profit: ${self.stats['total_profit_usd']:.2f}")
        logger.info(f"  Total Fees: ${self.stats['total_fees_usd']:.2f}")
        logger.info(f"  Total Gas Cost: ${self.stats['total_gas_cost_usd']:.2f}")
        
        if "avg_profit_per_trade" in self.stats:
            logger.info(f"  Avg Profit per Trade: ${self.stats['avg_profit_per_trade']:.2f}")
        
        if "success_rate" in self.stats:
            logger.info(f"  Success Rate: {self.stats['success_rate']:.2%}")
    
    def _export_data(self):
        """Export system data for analysis."""
        os.makedirs("data", exist_ok=True)
        
        # Export system statistics
        with open(os.path.join("data", "system_stats.json"), "w") as f:
            json.dump(self.stats, f, indent=2)
        
        # Export data from each service
        self.market_data.export_data()
        self.arbitrage_service.export_opportunities()
        self.simulation_service.export_simulations()
        self.execution_service.export_execution_results()
        
        logger.info("Exported system data for analysis")
    
    def get_system_stats(self) -> Dict:
        """Get current system statistics."""
        return self.stats
    
    def get_best_opportunities(self, limit: int = 5) -> List[Dict]:
        """Get the best arbitrage opportunities."""
        return self.arbitrage_service.get_best_opportunities(limit=limit)
    
    def get_profitable_simulations(self, limit: int = 5) -> List[Dict]:
        """Get the most profitable simulated trades."""
        return self.simulation_service.get_profitable_simulations(limit=limit)
    
    def get_successful_executions(self, limit: int = 5) -> List[Dict]:
        """Get successful trade executions."""
        return self.execution_service.get_successful_executions(limit=limit)
    
    async def execute_trade(self, trade: Dict) -> Dict:
        """
        Manually execute a specific trade.
        
        Args:
            trade: The trade to execute.
            
        Returns:
            Dict: The execution result.
        """
        if not self.running:
            logger.warning("System is not running, cannot execute trade")
            return {"status": "failed", "message": "System is not running"}
        
        logger.info(f"Manually executing trade: {trade.get('id', 'unknown')}")
        return await self.execution_service.execute_single_trade(trade)
    
    def set_auto_execute(self, enabled: bool):
        """
        Enable or disable automatic trade execution.
        
        Args:
            enabled: Whether to enable automatic execution.
        """
        self.auto_execute = enabled
        logger.info(f"Auto-execution {'enabled' if enabled else 'disabled'}")
    
    def set_min_profit_threshold(self, threshold: float):
        """
        Set the minimum profit threshold for opportunity detection.
        
        Args:
            threshold: The minimum profit threshold as a decimal (e.g., 0.005 for 0.5%).
        """
        self.min_profit_threshold = threshold
        self.arbitrage_service.set_min_profit_threshold(threshold)
        logger.info(f"Minimum profit threshold set to {threshold:.2%}")


# Example usage
async def main():
    # Initialize the arbitrage system
    system = ArbitrageSystem()
    
    try:
        # Start the system (without auto-execution)
        system_task = asyncio.create_task(system.start(auto_execute=False))
        
        # Wait for the system to initialize and collect some data
        await asyncio.sleep(30)
        
        # Get the best opportunities
        opportunities = system.get_best_opportunities()
        print(f"Found {len(opportunities)} best arbitrage opportunities")
        
        # Get profitable simulations
        simulations = system.get_profitable_simulations()
        print(f"Found {len(simulations)} profitable simulated trades")
        
        # Manually execute the most profitable simulated trade
        if simulations:
            best_sim = simulations[0]
            print(f"Manually executing the most profitable trade: {best_sim.get('id', 'unknown')}")
            result = await system.execute_trade(best_sim)
            print(f"Execution result: {result['status']}")
            if result['status'] == 'success':
                print(f"Profit: ${result.get('profit_usd', 0):.2f}")
        
        # Get system statistics
        stats = system.get_system_stats()
        print("\nSystem Statistics:")
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        
        # Run for a while to collect more data
        await asyncio.sleep(60)
        
        # Enable auto-execution
        system.set_auto_execute(True)
        print("Enabled auto-execution")
        
        # Run with auto-execution for a while
        await asyncio.sleep(120)
        
        # Get successful executions
        executions = system.get_successful_executions()
        print(f"Successfully executed {len(executions)} trades")
        
        # Print details of successful executions
        for i, result in enumerate(executions[:3], 1):
            print(f"\nExecution {i}:")
            if result["type"] == "cross_dex":
                print(f"  Type: Cross-DEX")
                print(f"  Token Pair: {result['token0']}/{result['token1']}")
                print(f"  Buy: {result['buy_dex']} on {result['buy_network']}")
                print(f"  Sell: {result['sell_dex']} on {result['sell_network']}")
            else:  # triangular
                print(f"  Type: Triangular")
                print(f"  DEX: {result['dex_id']} on {result['network_id']}")
                print(f"  Path: {result['token_a']} -> {result['token_b']} -> {result['token_c']} -> {result['token_a']}")
            
            print(f"  Trade Size: ${result['trade_size_usd']:.2f}")
            print(f"  Net Profit: ${result['profit_usd']:.2f}")
    finally:
        # Stop the system
        await system.stop()
        system_task.cancel()
        try:
            await system_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(main())
