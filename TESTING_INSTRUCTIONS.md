# Running Unit Tests for DeFi Arbitrage System

This document provides instructions to run the modular unit tests for the DeFi arbitrage system components.

## Prerequisites

- Python 3.8 or higher installed
- `pytest` installed (`pip install pytest`)
- `pytest-asyncio` installed for async test support (`pip install pytest-asyncio`)
- All project dependencies installed (see `requirements.txt`)

## Running Tests

1. Navigate to the project root directory:

```bash
cd /home/bruce/Documents/git/arbagent
```

2. Run all tests with pytest:

```bash
pytest
```

This will discover and run all test files matching `test_*.py`.

## Notes

- The tests use mocks and stubs for external dependencies such as Web3 and blockchain networks to avoid real mainnet transactions.
- Tests involving async functions require `pytest-asyncio`.
- To run tests against a testnet environment, ensure your environment variables or config files point to testnet RPC URLs and wallets with testnet funds.
- You can run individual test files, for example:

```bash
pytest test_flashloan_executor.py
```

- For detailed output, add the `-v` flag:

```bash
pytest -v
```

## Troubleshooting

- If tests fail due to missing dependencies, install them via pip.
- Ensure your Python environment is activated if using virtual environments.
- Check your config files for correct testnet RPC URLs and wallet keys.

## Summary of Test Files

- `test_market_data_service.py` - Tests MarketDataService functionality
- `test_arbitrage_detector.py` - Tests ArbitrageDetector detection and validation
- `test_trade_simulator.py` - Tests TradeSimulator trade simulation logic
- `test_flashloan_executor.py` - Tests FlashloanExecutor including Aave flashloan integration
- `test_defi_agent.py` - Tests DeFiAgent profit settlement and deployment methods