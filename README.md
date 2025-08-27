# RandomMartingale Trading Bot / 随机马丁格尔交易机器人

## Overview / 概述
This is an automated trading robot based on MetaTrader 5 platform, implementing a unique trading strategy that combines traditional candlestick patterns with random number generation and martingale money management.
Measured change from 100 USD to 200 USD in three days

这是一个基于MetaTrader 5平台的自动化交易机器人，实现了独特的交易策略，结合了传统K线形态分析、随机数生成和马丁格尔资金管理。
100U三天翻仓

## Features / 功能特点
- **Yin-Yang Candlestick Analysis** / 阴阳K线分析: Analyzes current candlestick pattern (bullish/bearish)
- **Random Number Strategy** / 随机数策略: Generates trading signals based on a combination of candlestick pattern and random numbers
- **Martingale Money Management** / 马丁格尔资金管理: Automatically adjusts position size based on trading results
- **Configurable Random Seed** / 可配置随机种子: Allows users to modify the random number generation behavior
- **Real-time Trading** / 实时交易: Executes trades automatically on MT5 platform

## Requirements / 系统要求
- **MetaTrader 5** platform installed
- **Python 3.7+** with following packages:
  - `MetaTrader5`
  - `pandas`
  - `logging` (custom module)
- MT5 account with valid credentials

## Installation / 安装步骤
1. Install Python dependencies:
```bash
pip install MetaTrader5 pandas
```

2. Configure your MT5 account credentials in the script:
```python
登录名 = 账户
服务器 = 服务器
密码 = 账户密码
```

3. Adjust trading parameters as needed:
```python
交易品种 = "XAUUSDm"  # Trading symbol
基础手数 = 0.01      # Base lot size
冷却时间 = 64        # Cooldown time in seconds
```

## Configuration / 配置说明
The bot uses a seed configuration file (`种子配置.txt`) to control random number generation:

机器人使用种子配置文件(`种子配置.txt`)来控制随机数生成：

### Seed File Format / 种子文件格式
```
# Random seed configuration file
# Modify the seed value in this file, the script will auto-read new seeds
# Format: One seed value per line, script reads the first valid number

100611193115

# Instructions:
# 1. Seed value must be a positive integer
# 2. Lines starting with # are comments and will be ignored
# 3. Empty lines will be ignored
# 4. Script periodically checks file modification time and re-reads if changed
```

## Strategy Details / 策略详情
### Trading Signal Generation / 交易信号生成
1. Gets current candlestick pattern (bullish=1, bearish=0)
2. Generates 3 random numbers (0 or 1) based on seed + timestamp
3. Combines these 4 values to determine trading strategy from a predefined strategy table
4. Determines order direction based on majority of random numbers

### Money Management / 资金管理
- Implements martingale strategy: doubles position size after losses
- Resets to base lot size after profitable trade
- Maximum multiplier limit prevents excessive risk

## Risk Warning / 风险警告
- Martingale strategy can lead to significant losses during prolonged losing streaks
- Use proper risk management and only risk capital you can afford to lose
- Test thoroughly in demo account before live trading

## Usage / 使用说明
1. Ensure MT5 platform is running and logged in
2. Run the script: `python 邵庸.py`
3. Input initial martingale multiplier when prompted
4. The bot will automatically monitor market and execute trades

## File Structure / 文件结构
- `邵庸.py` - Main trading bot script
- `种子配置.txt` - Random seed configuration file
- `Logging.py` - Custom logging module (not provided)

## Disclaimer / 免责声明
This trading bot is for educational purposes only. Use at your own risk. Past performance is not indicative of future results. The authors are not responsible for any financial losses incurred.

本交易机器人仅用于教育目的。使用风险自负。过去的表现并不代表未来的结果。作者不对任何财务损失负责。