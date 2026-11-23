from strategies.day_trading import DayTradingStrategy
from strategies.scalping import ScalpingStrategy
from strategies.swing_trading import SwingTradingStrategy

REGISTRY = {"Scalping": ScalpingStrategy, "Day Trading": DayTradingStrategy, "Swing Trading": SwingTradingStrategy}
