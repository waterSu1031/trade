# from abc import ABC, abstractmethod
import pandas as pd


class BaseStrategy:

    def __init__(self, price: pd.Series, direction: str = "both"):
        self.price = price
        self.direction = direction.lower()
        self.long_entry = pd.Series(False, index=price.index)
        self.long_exit = pd.Series(False, index=price.index)
        self.short_entry = pd.Series(False, index=price.index)
        self.short_exit = pd.Series(False, index=price.index)

    def generate_signals(self):
        pass

    def run(self):
        self.generate_signals()

    def get_signals(self) -> tuple:
        if self.direction == "long":
            entries = self.long_entry
            exits = self.long_exit
            direction = "long"
        elif self.direction == "short":
            entries = self.short_entry
            exits = self.short_exit
            direction = "short"
        elif self.direction == "both":
            entries = self.long_entry.combine_first(self.short_entry)
            exits = self.long_exit.combine_first(self.short_exit)
            direction = "both"
        else:
            raise ValueError("direction 은 'long', 'short', 'both' 중 하나 여야 합니다.")

        return entries, exits, direction

    def update_price(self, new_price: pd.Series):
        """실시간 가격 1봉 추가 및 유지"""
        self.price = pd.concat([self.price, new_price])
        self.price = self.price.last("2h")  # 롤링 유지 시간 조절 가능
