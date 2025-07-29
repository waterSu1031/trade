# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a SvelteKit-based frontend application for an automated trading system. The application provides interfaces for monitoring trading status, running batch jobs, backtesting strategies, and viewing statistics.

## Development Commands

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run check` - Run svelte-check for TypeScript validation
- `npm run check:watch` - Run svelte-check in watch mode

## Project Structure

```
src/
├── lib/
│   ├── components/       # Reusable Svelte components
│   ├── stores/          # Svelte stores for state management
│   ├── api/             # API communication utilities
│   ├── utils/           # Utility functions
│   └── types/           # TypeScript type definitions
├── routes/              # SvelteKit routes (pages)
│   ├── trading/         # Trading status page
│   ├── batch/           # Batch execution page
│   ├── backtest/        # Backtesting page
│   └── statistics/      # Statistics page
└── app.css             # Global styles with Tailwind
```

## Architecture

- **Framework**: SvelteKit with TypeScript
- **Styling**: Tailwind CSS with DaisyUI components
- **State Management**: Svelte stores
- **Type Safety**: TypeScript interfaces for trading data
- **Future Integrations**: Chart.js for visualizations, Socket.io for real-time data

## Key Types

The application uses TypeScript interfaces defined in `src/lib/types/index.ts`:
- `Trade` - Individual trading transactions
- `TradingStatus` - Overall trading system status
- `BacktestResult` - Backtesting analysis results
- `BatchJob` - Background job execution status
- `Statistics` - Trading performance statistics

## Pages

1. **Dashboard (/)** - Overview with key metrics and quick access
2. **Trading (/trading)** - Real-time trading status and recent trades
3. **Batch (/batch)** - Background job management and monitoring
4. **Backtest (/backtest)** - Strategy testing and performance analysis
5. **Statistics (/statistics)** - Detailed trading statistics and reports

## Styling Conventions

- Uses DaisyUI component classes for consistency
- Custom trading-specific CSS classes defined in app.css:
  - `.trading-card` - Standard card styling
  - `.profit/.loss` - Color coding for financial data
  - `.status-*` - Status badge styling

## Future Development

- Implement real-time WebSocket connections for live data
- Add Chart.js integration for data visualization
- Connect to backend APIs for actual trading data
- Add authentication and user management
- Implement data export functionality