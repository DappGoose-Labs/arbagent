#!/usr/bin/env python3
"""
DeFi Arbitrage Trading System - Main Entry Point

This script serves as the main entry point for the DeFi Arbitrage Trading System.
It initializes and starts all components of the system.
"""

import os
import sys
import asyncio
import argparse
import logging
import threading
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import ArbitrageSystem
from src.ui.server import run_ui_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("arbitrage_system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("run")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='DeFi Arbitrage Trading System')
    
    parser.add_argument('--auto-execute', action='store_true',
                        help='Enable automatic trade execution')
    
    parser.add_argument('--min-profit', type=float, default=0.5,
                        help='Minimum profit threshold in percentage (default: 0.5)')
    
    parser.add_argument('--ui-port', type=int, default=8080,
                        help='Port for the web UI (default: 8080)')
    
    parser.add_argument('--no-ui', action='store_true',
                        help='Disable the web UI')
    
    parser.add_argument('--train-rl', action='store_true',
                        help='Train the reinforcement learning model')
    
    parser.add_argument('--rl-steps', type=int, default=10000,
                        help='Number of steps for RL training (default: 10000)')
    
    return parser.parse_args()

async def run_system(args):
    """Run the arbitrage system."""
    # Initialize the system
    system = ArbitrageSystem()
    
    # Set minimum profit threshold
    min_profit = args.min_profit / 100.0  # Convert from percentage to decimal
    system.set_min_profit_threshold(min_profit)
    
    # Start the UI in a separate thread if enabled
    if not args.no_ui:
        ui_thread = threading.Thread(
            target=run_ui_server,
            args=(system,),
            daemon=True
        )
        ui_thread.start()
        logger.info(f"Web UI started on port {args.ui_port}")
    
    # Train the RL model if requested
    if args.train_rl:
        from src.models.reinforcement_learning import RLModel
        logger.info(f"Training RL model for {args.rl_steps} steps")
        model = RLModel()
        model.train(total_timesteps=args.rl_steps)
    
    try:
        # Start the system
        logger.info(f"Starting arbitrage system (auto_execute={args.auto_execute})")
        await system.start(auto_execute=args.auto_execute)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping system")
    finally:
        # Stop the system
        await system.stop()
        logger.info("System stopped")

def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Print startup banner
    print("\n" + "=" * 80)
    print(f"DeFi Arbitrage Trading System - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print(f"Auto-Execute: {'Enabled' if args.auto_execute else 'Disabled'}")
    print(f"Min Profit Threshold: {args.min_profit}%")
    print(f"Web UI: {'Disabled' if args.no_ui else f'Enabled on port {args.ui_port}'}")
    print(f"RL Training: {'Enabled' if args.train_rl else 'Disabled'}")
    if args.train_rl:
        print(f"RL Training Steps: {args.rl_steps}")
    print("=" * 80 + "\n")
    
    # Run the system
    asyncio.run(run_system(args))

if __name__ == "__main__":
    main()
