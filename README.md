## 📖 项目简介 | Project Introduction  
本项目是一个基于 **MetaTrader5 (MT5)** 的自动化交易机器人，  
结合 **梅花易数的随机卦象推演** 与 **马丁格尔资金管理策略**，  
目标是在 **两天内实现翻仓**（高风险高收益）。  

This project is an automated trading bot based on **MetaTrader5 (MT5)**.  
It integrates **Meihua Yishu (random divination-based strategy)** with **Martingale money management**,  
aiming to **double the account within two days** (high risk, high reward).  

---

## ⚙️ 核心逻辑 | Core Logic  

### 1. 梅花易数推演 | Meihua Yishu Calculation  
- 每根 K 线（阴/阳）对应卦象中的爻。  
- 使用 **K 线形态 + 随机数种子 + 时间戳** 生成 3 个随机数。  
- 最终形成 **4位组合（K线阴阳 + 3个随机数）**。  
- 对应 **止盈 / 止损 点数** 配置表。  

Each candlestick (bullish/bearish) corresponds to a hexagram line.  
- Use **candlestick pattern + random seed + timestamp** to generate 3 random numbers.  
- Form a **4-digit sequence (candle + 3 random numbers)**.  
- Map the sequence to a **Take Profit (TP) / Stop Loss (SL)** rule.  

---

### 2. 马丁格尔资金管理 | Martingale Money Management  
- 初始手数由 `config.json` 配置（默认 0.01）。  
- 每次亏损 → **加倍手数**，追求一次盈利覆盖前面亏损。  
- 每次盈利 → **回退手数**，直至恢复到基础手数。  
- 最大马丁倍数：`max_martingale_multiplier = 8`。  

Initial lot size is defined in `config.json` (default 0.01).  
- After each **loss → double the lot size** until recovery.  
- After each **profit → reduce lot size** until back to base.  
- Max Martingale multiplier: `8x`.  

---

### 3. 风控与冷却 | Risk Control & Cooling  
- 每次交易后，等待 **持仓平仓** 才能继续下一次循环。  
- 平仓后等待 **64 秒冷却时间**（对应六十四卦）。  
- 交易方向由随机卦象中的“阴阳数量”决定：  
  - 阳数多 → 买入 (BUY)  
  - 阴数多 → 卖出 (SELL)  

After each trade, the bot waits for **position closure** before starting the next.  
- After closure, wait for **64 seconds cooling time** (matching 64 hexagrams).  
- Trade direction is based on the balance of Yin/Yang in the random sequence:  
  - More Yang → **BUY**  
  - More Yin → **SELL**  

---

## 📊 卦象对照表 | Hexagram Strategy Table  

| K线 (Candle) | 随机数1 | 随机数2 | 随机数3 | TP点数 (TP Points) | SL点数 (SL Points) | 组合 (Sequence) |  
|--------------|---------|---------|---------|--------------------|--------------------|-----------------|  
| 阳 (1) | 1 | 1 | 1 | 4 | 1 | 阳阳阳阳 |  
| 阳 (1) | 1 | 1 | 0 | 3 | 2 | 阳阳阳阴 |  
| 阳 (1) | 1 | 0 | 1 | 2 | 3 | 阳阳阴阳 |  
| 阳 (1) | 1 | 0 | 0 | 3 | 2 | 阳阳阴阴 |  
| 阳 (1) | 0 | 1 | 1 | 2 | 3 | 阳阴阳阳 |  
| 阳 (1) | 0 | 1 | 0 | 1 | 4 | 阳阴阳阴 |  
| 阳 (1) | 0 | 0 | 1 | 2 | 3 | 阳阴阴阳 |  
| 阳 (1) | 0 | 0 | 0 | 3 | 2 | 阳阴阴阴 |  
| 阴 (0) | 1 | 1 | 1 | 3 | 2 | 阴阳阳阳 |  
| 阴 (0) | 1 | 1 | 0 | 2 | 3 | 阴阳阳阴 |  
| 阴 (0) | 1 | 0 | 1 | 1 | 4 | 阴阳阴阳 |  
| 阴 (0) | 1 | 0 | 0 | 2 | 3 | 阴阳阴阴 |  
| 阴 (0) | 0 | 1 | 1 | 3 | 2 | 阴阴阳阳 |  
| 阴 (0) | 0 | 1 | 0 | 2 | 3 | 阴阴阳阴 |  
| 阴 (0) | 0 | 0 | 1 | 3 | 2 | 阴阴阴阳 |  
| 阴 (0) | 0 | 0 | 0 | 4 | 1 | 阴阴阴阴 |  

---

## 📂 文件结构 | File Structure  

```
XAUUSD.py       # 主程序 Main trading bot
config.json     # 配置文件 (交易参数 & MT5 账户信息)
trading_bot.log # 运行日志 Logs
```

---

## 🔧 配置说明 | Configuration  

`config.json` 示例 | Example:  

```json
{
  "mt5": {
    "login": 123456789,
    "server": "BrokerServer",
    "password": "password"
  },
  "trading": {
    "symbol": "XAUUSDm",
    "base_lot_size": 0.01,
    "max_martingale_multiplier": 8,
    "cooling_time": 64,
    "magic_number": 234000,
    "deviation": 20,
    "seed": 1006111951111
  }
}
```

---

## 🚀 使用方法 | Usage  

1. 安装依赖 | Install dependencies  
   ```bash
   pip install MetaTrader5
   ```  

2. 修改 `config.json`，填入你的 MT5 账户信息。  
   Edit `config.json` with your MT5 account info.  

3. 运行机器人 | Run the bot  
   ```bash
   python XAUUSD.py
   ```  

4. 查看日志 | Check logs  
   - 终端实时输出 | Real-time console output  
   - `trading_bot.log` 文件 | Log file  

---

## ⚠️ 风险提示 | Risk Warning  

⚠️ 本策略属于 **极高风险投机策略**，  
目标是 **两天翻仓**，但同样可能在短时间内爆仓。  

⚠️ This strategy is **extremely high risk**.  
While it targets **doubling in two days**, it may also **blow up the account quickly**.  

---

## ✨ 总结 | Summary  
- 结合 **梅花易数卦象推演**（随机数+K线阴阳）  
- 搭配 **马丁格尔资金管理**  
- 高风险 → 高收益（或高亏损）  
- 适用于 **实验性/研究性交易**，不推荐实盘大额资金使用。  

Integrates **Meihua Yishu divination** (randomness + candlesticks)  
with **Martingale money management**.  
High risk → High reward (or loss).  
Best suited for **experimental / research trading**, not recommended for large real accounts.  

Use candlestick pattern + random seed + timestamp to generate 3 random numbers.

Form a 4-digit sequence (candle + 3 random numbers).

Map the sequence to a Take Profit (TP) / Stop Loss (SL) rule.



---

2. 马丁格尔资金管理 | Martingale Money Management

初始手数由 config.json 配置（默认 0.01）。

每次亏损 → 加倍手数，追求一次盈利覆盖前面亏损。

每次盈利 → 回退手数，直至恢复到基础手数。

最大马丁倍数：max_martingale_multiplier = 8。


Initial lot size is defined in config.json (default 0.01).

After each loss → double the lot size until recovery.

After each profit → reduce lot size until back to base.

Max Martingale multiplier: 8x.



---

3. 风控与冷却 | Risk Control & Cooling

每次交易后，等待 持仓平仓 才能继续下一次循环。

平仓后等待 64 秒冷却时间（对应六十四卦）。

交易方向由随机卦象中的“阴阳数量”决定：

阳数多 → 买入 (BUY)

阴数多 → 卖出 (SELL)



After each trade, the bot waits for position closure before starting the next.

After closure, wait for 64 seconds cooling time (matching 64 hexagrams).

Trade direction is based on the balance of Yin/Yang in the random sequence:

More Yang → BUY

More Yin → SELL




---

📂 文件结构 | File Structure

XAUUSD.py       # 主程序 Main trading bot
config.json     # 配置文件 (交易参数 & MT5 账户信息)
trading_bot.log # 运行日志 Logs


---

🔧 配置说明 | Configuration

config.json 示例 | Example:

{
  "mt5": {
    "login": 123456789,
    "server": "BrokerServer",
    "password": "password"
  },
  "trading": {
    "symbol": "XAUUSDm",
    "base_lot_size": 0.01,
    "max_martingale_multiplier": 8,
    "cooling_time": 64,
    "magic_number": 234000,
    "deviation": 20,
    "seed": 1006111951111
  }
}


---

🚀 使用方法 | Usage

1. 安装依赖 | Install dependencies

pip install MetaTrader5


2. 修改 config.json，填入你的 MT5 账户信息。
Edit config.json with your MT5 account info.


3. 运行机器人 | Run the bot

python XAUUSD.py


4. 查看日志 | Check logs

终端实时输出 | Real-time console output

trading_bot.log 文件 | Log file





---

⚠️ 风险提示 | Risk Warning

⚠️ 本策略属于 极高风险投机策略，
目标是 两天翻仓，但同样可能在短时间内爆仓。

⚠️ This strategy is extremely high risk.
While it targets doubling in two days, it may also blow up the account quickly.


---

✨ 总结 | Summary

结合 梅花易数卦象推演（随机数+K线阴阳）

搭配 马丁格尔资金管理

高风险 → 高收益（或高亏损）

适用于 实验性/研究性交易，不推荐实盘大额资金使用。


Integrates Meihua Yishu divination (randomness + candlesticks)
with Martingale money management.
High risk → High reward (or loss).
Best suited for experimental / research trading, not recommended for large real accounts.
