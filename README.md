# Multi-Agent DeFi Arbitrage Trading System

A comprehensive system for identifying and executing profitable arbitrage trades across decentralized exchanges using flash loans, reinforcement learning, and on-chain execution.

## System Overview

This system utilizes a multi-agent architecture to:
1. Monitor market data across multiple DEXs and blockchain networks
2. Identify profitable arbitrage opportunities
3. Simulate trades to validate profitability
4. Execute trades using flash loans
5. Settle profits and optimize capital deployment

## Key Features

- **Multi-DEX Support**: Monitors Uniswap, Curve, QuickSwap, ParaSwap, KyberSwap, Velodrome, Aerodrome, and other high-volume DEXs
- **Multi-Chain Support**: Operates across Polygon, Base, Optimism, BSC, Arbitrum, and Sonic networks
- **Comprehensive Data Sources**: Integrates with CoinGecko, CoinMarketCap, The Graph, and Chainlink oracles
- **Advanced ML Models**: Uses DistilBERT for Admin and DeFi Agents with Stable Baselines3 for reinforcement learning
- **Dynamic Opportunity Detection**: Identifies opportunities across all token pairs with at least 100k liquidity
- **Risk Management**: Ensures minimum 0.5% profit after all fees (DEX fees, transaction fees, flashloan fees)
- **Autonomous Operation**: Runs independently to identify, simulate, and execute profitable trades
- **Self-Improvement**: Logs execution data for reinforcement learning to optimize trade size, routing, and profitability
- **Profit Redeployment**: Settles profits to stablecoins and deploys them to lending/staking opportunities

## System Architecture

The system consists of the following components:

### 1. Market Data Module
- Collects and processes real-time price and liquidity data from multiple sources
- Monitors DEX liquidity pools and token pairs
- Normalizes data for consistent analysis

### 2. Arbitrage Detection Module
- Analyzes market data to identify price discrepancies
- Calculates potential profit after all fees
- Prioritizes opportunities based on profitability and risk

### 3. Trade Simulation Module
- Simulates potential trades to validate profitability
- Accounts for price impact, slippage, and gas costs
- Determines optimal trade parameters

### 4. Flashloan Execution Module
- Dynamically selects optimal flashloan providers
- Manages the borrowing, trading, and repayment process
- Ensures transaction security and efficiency

### 5. Reinforcement Learning Component
- Learns from historical trade data to improve decision-making
- Optimizes trade size, timing, and routing
- Adapts to changing market conditions

### 6. DeFi Agent
- Manages profit settlement to stablecoins
- Deploys capital to lending and staking opportunities
- Rebalances positions for optimal returns

### 7. Admin Agent
- Monitors system performance and health
- Manages risk parameters and thresholds
- Provides reporting and analytics

## Implementation Approach

Due to the complexity and resource requirements of the system, implementation follows a modular approach:

1. Each component is developed and tested independently
2. Dependencies are installed as needed for each module
3. Components are integrated incrementally
4. The system is tested end-to-end before deployment

## Requirements

- Python 3.10+
- Web3 connectivity to supported blockchain networks
- API keys for market data sources
- Coinbase onchain agent SDK credentials
- Sufficient capital for testing and execution

## Development Status

The system is currently under development. See the [todo.md](todo.md) file for current progress and next steps.
