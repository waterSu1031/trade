# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based algorithmic trading engine that supports both backtesting and live trading through Interactive Brokers (IBKR). The system uses a modular architecture with separate components for data handling, strategy execution, order management, and broker integration.

## Key Commands

### Running the Application
- `python main.py` - Run the main trading application
- The application automatically selects environment files based on OS (.env_dev for Windows, .env_prod for Linux)

### Testing
- No specific test framework configuration found - check with the user for testing commands

### Environment Setup
- Uses Python virtual environment (`.venv/` directory present)
- Install dependencies: `pip install -r requirements.txt`
- Environment configuration via `.env_dev` (Windows) or `.env_prod` (Linux)

## Architecture Overview

### Core Components

1. **Trade Engine (`src/trade.py`)**: Main orchestration class that coordinates all components
   - Handles both backtesting (`trade_mode="back"`) and live trading (`trade_mode="live"`)
   - Manages IBKR connection and switches between paper/live trading
   - Entry point: `tradeApp = Trade()` instance

2. **Data Layer (`src/data/`)**:
   - `data_loader.py`: IBKRData class for historical data retrieval and real-time streaming
   - `connect_IBKR.py`: IBKR connection management
   - `resampler.py`: Data resampling utilities
   - Uses SQLite databases for local data storage

3. **Strategy Framework (`src/strategies/`)**:
   - `base_strategy.py`: Abstract base class for all trading strategies
   - `example1_strategy.py`, `example2_strategy.py`: Concrete strategy implementations
   - Supports long/short/both directional trading
   - Real-time signal generation with rolling price windows

4. **Order Management (`src/order/`)**:
   - `order_manager.py`: Handles signal-to-order conversion and position management
   - `broker_interface.py`: Abstract broker interface
   - `broker_IBKR.py`: IBKR-specific broker implementation
   - `runner.py`: Strategy execution and portfolio analysis using vectorbtpro

5. **Infrastructure (`src/infra/`)**:
   - SQLite database integration for trade data and market data storage
   - Database models and DDL definitions

### Key Dependencies

- **ib-insync**: Interactive Brokers API integration
- **vectorbtpro**: Backtesting and portfolio analytics
- **pandas**: Data manipulation and time series analysis
- **ta-lib**: Technical analysis indicators (custom wheel installation)

### Configuration

The system uses a dataclass-based configuration in `src/config.py`:
- Auto-detects OS and loads appropriate environment file
- Manages database paths, IBKR connection settings, and trading modes
- Central configuration: `config = Config()` instance

### Trading Modes

1. **Backtesting Mode**: 
   - Downloads historical data and runs strategy simulations
   - Returns vectorbt Portfolio objects with performance metrics

2. **Live Trading Mode**:
   - Streams real-time data from IBKR
   - Generates signals and executes trades automatically
   - Integrates with OrderManager for position management

### Data Flow

1. Main entry → `Trade.run()` → mode selection
2. Data retrieval → `IBKRData.database()` or `IBKRData.stream()`
3. Strategy execution → `BaseStrategy.run()` → signal generation
4. Order execution → `OrderManager.handle_signal()` → broker execution
5. Portfolio analysis → `Runner.analyze_portfolio()` using vectorbtpro

### Important Notes

- The system requires IBKR TWS or IB Gateway to be running
- Paper trading uses port 4002, live trading uses port 4001
- Database schema includes symbol contract definitions and historical price data
- Real-time data processing uses callback-based streaming architecture