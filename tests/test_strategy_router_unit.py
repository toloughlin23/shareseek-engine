# /tests/test_strategy_router_unit.py

import unittest
from datetime import datetime
from engine.strategy_router import generate_trade_signal

class TestStrategyRouter(unittest.TestCase):

    def setUp(self):
        self.symbol = "AAPL"
        self.now = datetime(2025, 6, 25, 9, 30)
        self.valid_volume = 1_500_000
        self.default_win_rate = 0.65

        self.data_long = {
            'sma_20': [390, 392, 395, 397],
            'sma_50': [388, 389, 390, 391]
        }

    def test_accepts_valid_signal(self):
        data_short = {
            'sma_20': [98, 99, 100, 101],
            'sma_50': [95, 96, 97, 98],
            'close': [102],
            'high': [100, 101, 102, 102],
            'low': [99, 98, 97, 97],
            'open': [100],
            'VWAP': [101],
            'volatility': [0.025]
        }

        signal = generate_trade_signal(data_short, self.data_long, self.symbol, self.now, self.valid_volume, self.default_win_rate)
        self.assertIsNotNone(signal)
        self.assertEqual(signal['direction'], 'long')
        self.assertIn('risk_pct', signal)

    def test_rejects_due_to_no_crossover(self):
        data_short = {
            'sma_20': [100, 100, 100, 100],
            'sma_50': [100, 100, 100, 100],
            'close': [100],
            'high': [100]*4,
            'low': [99]*4,
            'open': [100],
            'VWAP': [100],
            'volatility': [0.025]
        }

        signal = generate_trade_signal(data_short, self.data_long, self.symbol, self.now, self.valid_volume, self.default_win_rate)
        self.assertIsNone(signal)

    def test_rejects_due_to_low_volume(self):
        data_short = {
            'sma_20': [98, 99, 100, 101],
            'sma_50': [95, 96, 97, 98],
            'close': [102],
            'high': [100, 101, 102, 102],
            'low': [99, 98, 97, 97],
            'open': [100],
            'VWAP': [101],
            'volatility': [0.025]
        }

        low_volume = 100_000
        signal = generate_trade_signal(data_short, self.data_long, self.symbol, self.now, low_volume, self.default_win_rate)
        self.assertIsNone(signal)

if __name__ == '__main__':
    unittest.main()
