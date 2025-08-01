import vectorbt as vbt
import pandas as pd


class Runner:

    def __init__(self, strategy):
        self.strategy = strategy
        self.price = strategy.price

    def run_back_signal(self):
        entries, exits, direction = self.strategy.get_signals()
        return entries, exits, direction

    def run_live_signal(self, new_price: pd.Series):
        self.strategy.update_price(new_price)
        entries, exits, direction = self.strategy.get_signals()
        return entries, exits, direction

    def analyze_portfolio(self, entries, exits, direction, **kwargs):
        print('이후에 portfolio 옵션관련함수추가.')
        return vbt.Portfolio.from_signals(
            close=self.price,
            entries=entries,
            exits=exits,
            direction=direction,
            **kwargs,
            fees=kwargs.get('fees', 0.0),
            slippage=kwargs.get('slippage', 0.0),
        )




        # live_pf.append(
        #     new_close=new_price,
        #     new_entries=entries.iloc[-1:],
        #     new_exits=exits.iloc[-1:]
        # )