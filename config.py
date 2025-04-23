"""
Configuration settings for the DeFi Arbitrage Trading System.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# General settings
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MIN_PROFIT_THRESHOLD = float(os.getenv("MIN_PROFIT_THRESHOLD", "0.005"))  # 0.5%
MIN_LIQUIDITY_THRESHOLD = float(os.getenv("MIN_LIQUIDITY_THRESHOLD", "100000"))  # $100k

# Blockchain networks
NETWORKS = {
    "polygon": {
        "name": "Polygon",
        "chain_id": 137,
        "rpc_url": os.getenv("POLYGON_RPC_URL", ""),
        "explorer_url": "https://polygonscan.com",
        "enabled": os.getenv("ENABLE_POLYGON", "true").lower() == "true",
    },
    "base": {
        "name": "Base",
        "chain_id": 8453,
        "rpc_url": os.getenv("BASE_RPC_URL", ""),
        "explorer_url": "https://basescan.org",
        "enabled": os.getenv("ENABLE_BASE", "true").lower() == "true",
    },
    "optimism": {
        "name": "Optimism",
        "chain_id": 10,
        "rpc_url": os.getenv("OPTIMISM_RPC_URL", ""),
        "explorer_url": "https://optimistic.etherscan.io",
        "enabled": os.getenv("ENABLE_OPTIMISM", "true").lower() == "true",
    },
    "bsc": {
        "name": "Binance Smart Chain",
        "chain_id": 56,
        "rpc_url": os.getenv("BSC_RPC_URL", ""),
        "explorer_url": "https://bscscan.com",
        "enabled": os.getenv("ENABLE_BSC", "true").lower() == "true",
    },
    "arbitrum": {
        "name": "Arbitrum",
        "chain_id": 42161,
        "rpc_url": os.getenv("ARBITRUM_RPC_URL", ""),
        "explorer_url": "https://arbiscan.io",
        "enabled": os.getenv("ENABLE_ARBITRUM", "true").lower() == "true",
    },
    "sonic": {
        "name": "Sonic",
        "chain_id": 64165,
        "rpc_url": os.getenv("SONIC_RPC_URL", ""),
        "explorer_url": "https://explorer.sonic.org",
        "enabled": os.getenv("ENABLE_SONIC", "true").lower() == "true",
    },
}

# DEX configurations
DEXES = {
    "uniswap": {
        "name": "Uniswap",
        "versions": ["v2", "v3"],
        "enabled": os.getenv("ENABLE_UNISWAP", "true").lower() == "true",
        "networks": ["polygon", "base", "optimism", "arbitrum"],
        "fee_tiers": [0.0005, 0.003, 0.01, 0.03],  # 0.05%, 0.3%, 1%, 3%
    },
    "curve": {
        "name": "Curve",
        "enabled": os.getenv("ENABLE_CURVE", "true").lower() == "true",
        "networks": ["polygon", "optimism", "arbitrum"],
        "fee_tiers": [0.0004, 0.0001],  # 0.04%, 0.01%
    },
    "quickswap": {
        "name": "QuickSwap",
        "enabled": os.getenv("ENABLE_QUICKSWAP", "true").lower() == "true",
        "networks": ["polygon"],
        "fee_tiers": [0.003],  # 0.3%
    },
    "paraswap": {
        "name": "ParaSwap",
        "enabled": os.getenv("ENABLE_PARASWAP", "true").lower() == "true",
        "networks": ["polygon", "bsc", "optimism", "arbitrum"],
    },
    "kyberswap": {
        "name": "KyberSwap",
        "enabled": os.getenv("ENABLE_KYBERSWAP", "true").lower() == "true",
        "networks": ["polygon", "bsc", "optimism", "arbitrum"],
        "fee_tiers": [0.001, 0.003, 0.005],  # 0.1%, 0.3%, 0.5%
    },
    "velodrome": {
        "name": "Velodrome",
        "enabled": os.getenv("ENABLE_VELODROME", "true").lower() == "true",
        "networks": ["optimism"],
        "fee_tiers": [0.002],  # 0.2%
    },
    "aerodrome": {
        "name": "Aerodrome",
        "enabled": os.getenv("ENABLE_AERODROME", "true").lower() == "true",
        "networks": ["base"],
        "fee_tiers": [0.002],  # 0.2%
    },
}

# API keys and endpoints
API_KEYS = {
    "coingecko": os.getenv("COINGECKO_API_KEY", ""),
    "coinmarketcap": os.getenv("COINMARKETCAP_API_KEY", ""),
    "the_graph": os.getenv("THE_GRAPH_API_KEY", ""),
}

# Flash loan providers
FLASH_LOAN_PROVIDERS = {
    "aave": {
        "name": "Aave",
        "enabled": os.getenv("ENABLE_AAVE", "true").lower() == "true",
        "networks": ["polygon", "optimism", "arbitrum"],
        "fee": 0.0009,  # 0.09%
    },
    "dydx": {
        "name": "dYdX",
        "enabled": os.getenv("ENABLE_DYDX", "true").lower() == "true",
        "networks": ["arbitrum"],
        "fee": 0,  # No fee
    },
    "balancer": {
        "name": "Balancer",
        "enabled": os.getenv("ENABLE_BALANCER", "true").lower() == "true",
        "networks": ["polygon", "arbitrum", "base", "optimism"],
        "fee": 0.0006,  # 0.06%
    },
}

# Machine learning settings
ML_CONFIG = {
    "model_path": os.path.join(PROJECT_ROOT, "models"),
    "distilbert_model": "distilbert-base-uncased",
    "rl_algorithm": "PPO",
    "training_frequency": int(os.getenv("TRAINING_FREQUENCY", "1000")),  # Train every 1000 trades
    "batch_size": int(os.getenv("BATCH_SIZE", "64")),
    "learning_rate": float(os.getenv("LEARNING_RATE", "0.0003")),
}

# Wallet and transaction settings
WALLET_CONFIG = {
    "private_key": os.getenv("WALLET_PRIVATE_KEY", ""),
    "max_gas_price": {
        "polygon": int(os.getenv("POLYGON_MAX_GAS_PRICE", "100")),  # gwei
        "base": int(os.getenv("BASE_MAX_GAS_PRICE", "5")),  # gwei
        "optimism": int(os.getenv("OPTIMISM_MAX_GAS_PRICE", "5")),  # gwei
        "bsc": int(os.getenv("BSC_MAX_GAS_PRICE", "5")),  # gwei
        "arbitrum": int(os.getenv("ARBITRUM_MAX_GAS_PRICE", "1")),  # gwei
        "sonic": int(os.getenv("SONIC_MAX_GAS_PRICE", "5")),  # gwei
    },
    "max_trade_size": float(os.getenv("MAX_TRADE_SIZE", "100000")),  # $100k
}

# Coinbase onchain agent SDK settings
COINBASE_AGENT_CONFIG = {
    "api_key": os.getenv("COINBASE_AGENT_API_KEY", ""),
    "api_secret": os.getenv("COINBASE_AGENT_API_SECRET", ""),
    "endpoint": os.getenv("COINBASE_AGENT_ENDPOINT", ""),
}

# UI settings
UI_CONFIG = {
    "port": int(os.getenv("UI_PORT", "8080")),
    "host": os.getenv("UI_HOST", "0.0.0.0"),
    "debug": os.getenv("UI_DEBUG", "false").lower() == "true",
}
