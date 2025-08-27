"""
Random Martingale Trading Bot - 优化版本
基于随机数生成和马丁格尔策略的自动交易机器人
"""

import MetaTrader5 as mt5
import time
import random
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class OrderType(Enum):
    """订单类型枚举"""
    BUY = mt5.ORDER_TYPE_BUY
    SELL = mt5.ORDER_TYPE_SELL


class TradeResult(Enum):
    """交易结果枚举"""
    PROFIT = "profit"
    LOSS = "loss"
    BREAK_EVEN = "break_even"


@dataclass
class TradingConfig:
    """交易配置"""
    symbol: str = "XAUUSDm"
    base_lot_size: float = 0.01
    max_martingale_multiplier: int = 8
    cooling_time: int = 64
    check_interval: int = 5
    seed_config_file: str = "种子配置.txt"
    magic_number: int = 234000
    deviation: int = 20
    default_seed: int = 1006111951111


@dataclass
class TradeStrategy:
    """交易策略"""
    tp_points: int
    sl_points: int


@dataclass
class PositionInfo:
    """持仓信息"""
    open_price: float
    order_type: OrderType
    lot_size: float
    ticket: int


@dataclass
class MT5Config:
    """MT5连接配置"""
    login: int
    server: str
    password: str


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            "mt5": {
                "login": 0,
                "server": "",
                "password": ""
            },
            "trading": {
                "symbol": "XAUUSDm",
                "base_lot_size": 0.01,
                "max_martingale_multiplier": 8,
                "cooling_time": 64,
                "magic_number": 234000
            }
        }
        
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            logger.info(f"创建默认配置文件: {self.config_file}")
            return default_config
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return default_config
    
    def get_mt5_config(self) -> MT5Config:
        """获取MT5配置"""
        mt5_config = self.config.get("mt5", {})
        return MT5Config(
            login=mt5_config.get("login", 0),
            server=mt5_config.get("server", ""),
            password=mt5_config.get("password", "")
        )
    
    def get_trading_config(self) -> TradingConfig:
        """获取交易配置"""
        trading_config = self.config.get("trading", {})
        return TradingConfig(
            symbol=trading_config.get("symbol", "XAUUSDm"),
            base_lot_size=trading_config.get("base_lot_size", 0.01),
            max_martingale_multiplier=trading_config.get("max_martingale_multiplier", 8),
            cooling_time=trading_config.get("cooling_time", 64),
            magic_number=trading_config.get("magic_number", 234000)
        )


class SeedManager:
    """种子管理器"""
    
    def __init__(self, seed_file: str = "种子配置.txt", default_seed: int = 1006111951111):
        self.seed_file = seed_file
        self.default_seed = default_seed
        self.last_modified = 0
        self.current_seed = self._load_seed()
    
    def _load_seed(self) -> int:
        """从配置文件加载种子"""
        if not os.path.exists(self.seed_file):
            return self.default_seed
        
        try:
            encodings = ['utf-8', 'gbk', 'utf-16', 'ascii']
            for encoding in encodings:
                try:
                    with open(self.seed_file, 'r', encoding=encoding) as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                seed_value = int(line)
                                if seed_value > 0:
                                    return seed_value
                    break
                except UnicodeDecodeError:
                    continue
            return self.default_seed
        except Exception as e:
            logger.error(f"读取种子配置文件失败: {e}")
            return self.default_seed
    
    def get_seed(self) -> int:
        """获取当前种子，如果文件有更新则重新加载"""
        if os.path.exists(self.seed_file):
            current_modified = os.path.getmtime(self.seed_file)
            if current_modified > self.last_modified:
                new_seed = self._load_seed()
                if new_seed != self.current_seed:
                    self.current_seed = new_seed
                    logger.info(f"种子配置已更新: {self.current_seed}")
                self.last_modified = current_modified
        
        return self.current_seed


class StrategyCalculator:
    """策略计算器"""
    
    # 策略映射表：(K线形态, 随机数1, 随机数2, 随机数3) -> (TP点数, SL点数)
    STRATEGY_MAP = {
        (1, 1, 1, 1): TradeStrategy(4, 1),  # 阳阳阳阳
        (1, 1, 1, 0): TradeStrategy(3, 2),  # 阳阳阳阴
        (1, 1, 0, 1): TradeStrategy(2, 3),  # 阳阳阴阳
        (1, 1, 0, 0): TradeStrategy(3, 2),  # 阳阳阴阴
        (1, 0, 1, 1): TradeStrategy(2, 3),  # 阳阴阳阳
        (1, 0, 1, 0): TradeStrategy(1, 4),  # 阳阴阳阴
        (1, 0, 0, 1): TradeStrategy(2, 3),  # 阳阴阴阳
        (1, 0, 0, 0): TradeStrategy(3, 2),  # 阳阴阴阴
        (0, 1, 1, 1): TradeStrategy(3, 2),  # 阴阳阳阳
        (0, 1, 1, 0): TradeStrategy(2, 3),  # 阴阳阳阴
        (0, 1, 0, 1): TradeStrategy(1, 4),  # 阴阳阴阳
        (0, 1, 0, 0): TradeStrategy(2, 3),  # 阴阳阴阴
        (0, 0, 1, 1): TradeStrategy(3, 2),  # 阴阴阳阳
        (0, 0, 1, 0): TradeStrategy(2, 3),  # 阴阴阳阴
        (0, 0, 0, 1): TradeStrategy(3, 2),  # 阴阴阴阳
        (0, 0, 0, 0): TradeStrategy(4, 1),  # 阴阴阴阴
    }
    
    @staticmethod
    def get_candle_pattern(symbol: str) -> Optional[int]:
        """获取当前K线的阴阳形态"""
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 1)
        if rates is None or len(rates) == 0:
            return None
        
        latest_candle = rates[0]
        open_price = latest_candle['open']
        close_price = latest_candle['close']
        
        return 1 if close_price > open_price else 0
    
    @staticmethod
    def generate_random_sequence(seed: int) -> Tuple[int, int, int]:
        """基于种子和当前时间戳生成3个随机数"""
        current_timestamp = int(time.time())
        combined_seed = seed + current_timestamp
        random.seed(combined_seed)
        
        return (
            random.randint(0, 1),
            random.randint(0, 1),
            random.randint(0, 1)
        )
    
    @classmethod
    def get_trade_strategy(cls, candle_pattern: int, r1: int, r2: int, r3: int) -> Tuple[OrderType, TradeStrategy]:
        """根据4位序列获取交易策略"""
        sequence = (candle_pattern, r1, r2, r3)
        strategy = cls.STRATEGY_MAP.get(sequence, TradeStrategy(2, 2))
        
        # 判断开仓方向：随机数中阳的数量大于阴就开多，否则开空
        yang_count = sum([r1, r2, r3])
        order_type = OrderType.BUY if yang_count > 1 else OrderType.SELL
        
        return order_type, strategy


class MartingaleManager:
    """马丁格尔管理器"""
    
    def __init__(self, base_lot_size: float, max_multiplier: int = 8):
        self.base_lot_size = base_lot_size
        self.max_multiplier = max_multiplier
        self.cumulative_loss = 0.0
    
    def calculate_next_lot_size(self, current_lot_size: float, result: TradeResult, pnl: float) -> float:
        """计算下一次交易的手数"""
        max_lot_size = self.base_lot_size * self.max_multiplier
        
        if result == TradeResult.PROFIT:
            # 更新累计亏损：减去本次盈利
            self.cumulative_loss = max(0, self.cumulative_loss - abs(pnl))
            
            if self.cumulative_loss > 0:
                # 还有未回本的亏损，马丁倍数减半
                new_lot_size = max(self.base_lot_size, current_lot_size / 2)
                multiplier = new_lot_size / self.base_lot_size
                logger.info(f"盈利 +{abs(pnl):.2f} USD | 累计亏损: -{self.cumulative_loss:.2f} USD | 未回本，马丁减半: {multiplier:.0f}x")
            else:
                # 已回本，重置为基础手数
                new_lot_size = self.base_lot_size
                logger.info(f"盈利 +{abs(pnl):.2f} USD | 已回本 | 马丁重置: 1x")
        
        elif result == TradeResult.LOSS:
            # 累计亏损增加
            self.cumulative_loss += abs(pnl)
            
            # 亏损后倍增手数，但不超过最大手数
            new_lot_size = min(max_lot_size, current_lot_size * 2)
            multiplier = new_lot_size / self.base_lot_size
            logger.error(f"亏损 {pnl:.2f} USD | 累计亏损: -{self.cumulative_loss:.2f} USD | 下一次马丁倍数: {multiplier:.0f}x")
        
        else:  # BREAK_EVEN
            # 平手时保持当前手数
            new_lot_size = current_lot_size
            multiplier = new_lot_size / self.base_lot_size
            logger.info(f"平手 {pnl:.2f} USD | 累计亏损: -{self.cumulative_loss:.2f} USD | 下一次马丁倍数: {multiplier:.0f}x")
        
        return new_lot_size


class MT5Connector:
    """MT5连接器"""
    
    def __init__(self, config: MT5Config):
        self.config = config
        self.connected = False
    
    def connect(self) -> bool:
        """连接到MT5"""
        if not mt5.initialize(
            login=self.config.login,
            server=self.config.server,
            password=self.config.password
        ):
            logger.error(f"MT5初始化失败，错误代码: {mt5.last_error()}")
            return False
        
        self.connected = True
        account_info = mt5.account_info()
        logger.info(f"MT5连接成功！账户: {account_info.login}, 服务器: {account_info.server}, 余额: ${account_info.balance:.2f}")
        return True
    
    def disconnect(self):
        """断开MT5连接"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
    
    def __enter__(self):
        if not self.connect():
            raise ConnectionError("Failed to connect to MT5")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


class TradeExecutor:
    """交易执行器"""
    
    def __init__(self, magic_number: int = 234000, deviation: int = 20):
        self.magic_number = magic_number
        self.deviation = deviation
    
    def execute_trade(self, symbol: str, order_type: OrderType, strategy: TradeStrategy, 
                     lot_size: float, pattern_sequence: Tuple[int, int, int, int]) -> Optional[PositionInfo]:
        """执行交易"""
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logger.error(f"获取价格失败: {mt5.last_error()}")
            return None
        
        if order_type == OrderType.BUY:
            price = tick.ask
            tp_price = price + strategy.tp_points * 1.0
            sl_price = price - strategy.sl_points * 1.0
            direction = "BUY"
        else:
            price = tick.bid
            tp_price = price - strategy.tp_points * 1.0
            sl_price = price + strategy.sl_points * 1.0
            direction = "SELL"
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type.value,
            "price": price,
            "sl": sl_price,
            "tp": tp_price,
            "deviation": self.deviation,
            "magic": self.magic_number,
            "comment": "RandomMartingale",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"交易失败: {result.retcode}, {result.comment}")
            return None
        
        # 格式化阴阳组合显示
        pattern_display = ''.join(['阳' if x == 1 else '阴' for x in pattern_sequence])
        multiplier = lot_size / 0.01  # 假设基础手数是0.01
        
        logger.info(f"RandomMartingale | {direction} | 开仓: {price:.5f} | "
                   f"止损: {strategy.sl_points:.5f} | 止盈: {strategy.tp_points:.5f} | "
                   f"马丁倍数: {multiplier:.0f}x --( {pattern_display} )--")
        
        return PositionInfo(
            open_price=price,
            order_type=order_type,
            lot_size=lot_size,
            ticket=result.order
        )
    
    def has_position(self, symbol: str) -> bool:
        """检查是否有持仓"""
        positions = mt5.positions_get(symbol=symbol)
        return positions is not None and len(positions) > 0
    
    def wait_for_close(self, symbol: str, position_info: PositionInfo) -> Tuple[TradeResult, float]:
        """等待持仓平仓并返回交易结果"""
        while self.has_position(symbol):
            time.sleep(5)
        
        return self._calculate_pnl(position_info, symbol)
    
    def _calculate_pnl(self, position_info: PositionInfo, symbol: str) -> Tuple[TradeResult, float]:
        """计算交易盈亏"""
        # 尝试从历史记录获取实际平仓信息
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=10)
        
        try:
            deals = mt5.history_deals_get(start_time, end_time)
            if deals:
                for deal in reversed(deals):
                    if (deal.magic == self.magic_number and 
                        deal.symbol == symbol and
                        deal.entry == mt5.DEAL_ENTRY_OUT):
                        pnl = deal.profit
                        account_info = mt5.account_info()
                        logger.info(f"实际平仓价格: {deal.price:.5f} | 实际盈亏: {pnl:.2f} USD | 余额: ${account_info.balance:.2f}")
                        
                        if pnl > 0:
                            return TradeResult.PROFIT, pnl
                        elif pnl < 0:
                            return TradeResult.LOSS, pnl
                        else:
                            return TradeResult.BREAK_EVEN, pnl
        except Exception as e:
            logger.warning(f"获取历史记录失败: {e}")
        
        # 如果无法获取历史记录，使用当前市场价格估算
        logger.warning("无法获取实际平仓价格，使用当前市场价格估算")
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return TradeResult.BREAK_EVEN, 0
        
        if position_info.order_type == OrderType.BUY:
            estimated_close_price = tick.bid
            price_diff = estimated_close_price - position_info.open_price
        else:
            estimated_close_price = tick.ask
            price_diff = position_info.open_price - estimated_close_price
        
        estimated_pnl = price_diff * position_info.lot_size * 100
        
        if estimated_pnl > 0:
            return TradeResult.PROFIT, estimated_pnl
        elif estimated_pnl < 0:
            return TradeResult.LOSS, estimated_pnl
        else:
            return TradeResult.BREAK_EVEN, estimated_pnl


class TradingBot:
    """交易机器人主类"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.trading_config = self.config_manager.get_trading_config()
        self.mt5_config = self.config_manager.get_mt5_config()
        self.seed_manager = SeedManager()
        self.martingale_manager = MartingaleManager(
            self.trading_config.base_lot_size,
            self.trading_config.max_martingale_multiplier
        )
        self.trade_executor = TradeExecutor(self.trading_config.magic_number)
        self.current_lot_size = self.trading_config.base_lot_size
    
    def _get_initial_lot_size(self) -> float:
        """获取初始手数"""
        if self.trade_executor.has_position(self.trading_config.symbol):
            positions = mt5.positions_get(symbol=self.trading_config.symbol)
            if positions and len(positions) > 0:
                position_lot_size = positions[0].volume
                multiplier = position_lot_size / self.trading_config.base_lot_size
                logger.info(f"检测到现有持仓 | 持仓手数: {position_lot_size} | 当前马丁倍数: {multiplier:.0f}x")
                return position_lot_size
        else:
            try:
                user_multiplier = float(input("请输入开仓马丁倍数 (默认1): ") or "1")
                if user_multiplier <= 0:
                    user_multiplier = 1
                    logger.warning("输入倍数无效，使用默认值1")
                lot_size = self.trading_config.base_lot_size * user_multiplier
                logger.info(f"用户设置马丁倍数: {user_multiplier:.0f}x | 开仓手数: {lot_size}")
                return lot_size
            except ValueError:
                logger.warning("输入格式错误，使用默认倍数1x")
                return self.trading_config.base_lot_size
    
    def run(self):
        """运行交易机器人"""
        logger.info("交易机器人启动")
        logger.info(f"当前随机数种子: {self.seed_manager.get_seed()}")
        
        try:
            with MT5Connector(self.mt5_config) as connector:
                self.current_lot_size = self._get_initial_lot_size()
                multiplier = self.current_lot_size / self.trading_config.base_lot_size
                logger.info(f"程序启动 | 启动倍数: {multiplier:.0f}x")
                
                while True:
                    try:
                        self._trading_loop()
                    except Exception as e:
                        logger.error(f"交易循环出错: {e}")
                        time.sleep(60)
                        
        except KeyboardInterrupt:
            logger.info("程序被用户中断")
        except Exception as e:
            logger.error(f"程序运行出错: {e}")
    
    def _trading_loop(self):
        """交易循环"""
        # 检查是否有持仓
        if self.trade_executor.has_position(self.trading_config.symbol):
            logger.info("检测到已有持仓，等待平仓...")
            while self.trade_executor.has_position(self.trading_config.symbol):
                time.sleep(self.trading_config.check_interval)
            logger.info("持仓已平仓，继续交易循环")
            time.sleep(self.trading_config.cooling_time)
            return
        
        # 获取当前K线形态
        candle_pattern = StrategyCalculator.get_candle_pattern(self.trading_config.symbol)
        if candle_pattern is None:
            time.sleep(60)
            return
        
        # 生成随机数序列
        current_seed = self.seed_manager.get_seed()
        r1, r2, r3 = StrategyCalculator.generate_random_sequence(current_seed)
        
        # 获取交易策略
        order_type, strategy = StrategyCalculator.get_trade_strategy(candle_pattern, r1, r2, r3)
        
        # 执行交易
        pattern_sequence = (candle_pattern, r1, r2, r3)
        position_info = self.trade_executor.execute_trade(
            self.trading_config.symbol, order_type, strategy, 
            self.current_lot_size, pattern_sequence
        )
        
        if position_info:
            # 等待平仓并处理结果
            result, pnl = self.trade_executor.wait_for_close(self.trading_config.symbol, position_info)
            self.current_lot_size = self.martingale_manager.calculate_next_lot_size(
                self.current_lot_size, result, pnl
            )
        
        # 等待下一个周期
        time.sleep(60)


def main():
    """主函数入口"""
    bot = TradingBot()
    bot.run()


if __name__ == "__main__":
    main()