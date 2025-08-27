import MetaTrader5 as mt5
import time
import random
import os
from datetime import datetime
from Logging import logger
import pandas as pd

def 初始化MT5连接():
    """初始化MT5连接"""
    # MT5连接参数
    登录名 = 账户
    服务器 = 服务器
    密码 = 账户密码
    
    if not mt5.initialize(login=登录名, server=服务器, password=密码):
        print(f"MT5初始化失败，错误代码: {mt5.last_error()}")
        return False
    
    return True

def 获取当前K线阴阳(交易品种):
    """获取当前K线的阴阳形态"""
    # 获取最新的K线数据
    rates = mt5.copy_rates_from_pos(交易品种, mt5.TIMEFRAME_M1, 0, 1)
    
    if rates is None or len(rates) == 0:
        return None
    
    最新K线 = rates[0]
    开盘价 = 最新K线['open']
    收盘价 = 最新K线['close']
    
    # 判断阴阳：收盘价 > 开盘价为阳线(1)，否则为阴线(0)
    K线形态 = 1 if 收盘价 > 开盘价 else 0
    
    return K线形态

def 生成随机数序列(随机数种子):
    """基于种子和当前时间戳生成3个随机数"""
    当前时间戳 = int(time.time())
    组合种子 = 随机数种子 + 当前时间戳
    
    random.seed(组合种子)
    
    随机数1 = random.randint(0, 1)
    随机数2 = random.randint(0, 1)
    随机数3 = random.randint(0, 1)
    
    return 随机数1, 随机数2, 随机数3

def 获取交易策略(K线形态, 随机数1, 随机数2, 随机数3):
    """根据4位序列获取交易策略"""
    # 创建策略映射表
    策略表 = {
        (1, 1, 1, 1): {"TP": 4, "SL": 1},  # 阳阳阳阳
        (1, 1, 1, 0): {"TP": 3, "SL": 2},  # 阳阳阳阴
        (1, 1, 0, 1): {"TP": 2, "SL": 3},  # 阳阳阴阳
        (1, 1, 0, 0): {"TP": 3, "SL": 2},  # 阳阳阴阴
        (1, 0, 1, 1): {"TP": 2, "SL": 3},  # 阳阴阳阳
        (1, 0, 1, 0): {"TP": 1, "SL": 4},  # 阳阴阳阴
        (1, 0, 0, 1): {"TP": 2, "SL": 3},  # 阳阴阴阳
        (1, 0, 0, 0): {"TP": 3, "SL": 2},  # 阳阴阴阴
        (0, 1, 1, 1): {"TP": 3, "SL": 2},  # 阴阳阳阳
        (0, 1, 1, 0): {"TP": 2, "SL": 3},  # 阴阳阳阴
        (0, 1, 0, 1): {"TP": 1, "SL": 4},  # 阴阳阴阳
        (0, 1, 0, 0): {"TP": 2, "SL": 3},  # 阴阳阴阴
        (0, 0, 1, 1): {"TP": 3, "SL": 2},  # 阴阴阳阳
        (0, 0, 1, 0): {"TP": 2, "SL": 3},  # 阴阴阳阴
        (0, 0, 0, 1): {"TP": 3, "SL": 2},  # 阴阴阴阳
        (0, 0, 0, 0): {"TP": 4, "SL": 1},  # 阴阴阴阴
    }
    
    序列 = (K线形态, 随机数1, 随机数2, 随机数3)
    策略 = 策略表.get(序列, {"TP": 2, "SL": 2})  # 默认策略
    
    # 判断开仓方向：随机数中阳的数量大于阴就开多，否则开空
    阳的数量 = sum([随机数1, 随机数2, 随机数3])
    阴的数量 = 3 - 阳的数量
    
    if 阳的数量 > 阴的数量:
        订单类型 = mt5.ORDER_TYPE_BUY
    else:
        订单类型 = mt5.ORDER_TYPE_SELL
    
    return 订单类型, 策略["TP"], 策略["SL"]

def 执行交易(交易品种, 订单类型, TP值, SL值, 手数=0.1, 当前倍数=1, 阴阳组合=None):
    """执行交易订单"""
    # 获取当前价格
    tick = mt5.symbol_info_tick(交易品种)
    if tick is None:
        print(f"获取价格失败: {mt5.last_error()}")
        return False, None, None
    
    if 订单类型 == mt5.ORDER_TYPE_BUY:
        价格 = tick.ask
        TP价格 = 价格 + TP值 * 1.0
        SL价格 = 价格 - SL值 * 1.0
        方向 = "BUY"
    else:
        价格 = tick.bid
        TP价格 = 价格 - TP值 * 1.0
        SL价格 = 价格 + SL值 * 1.0
        方向 = "SELL"
    
    # 构建交易请求
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": 交易品种,
        "volume": 手数,
        "type": 订单类型,
        "price": 价格,
        "sl": SL价格,
        "tp": TP价格,
        "deviation": 20,
        "magic": 234000,
        "comment": "RandomMartingale",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    # 发送交易请求
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"交易失败: {result.retcode}, {result.comment}")
        return False, None, None
    
    # 格式化阴阳组合显示
    if 阴阳组合 is not None:
        阴阳显示 = ''.join(['阳' if x == 1 else '阴' for x in 阴阳组合])
    else:
        阴阳显示 = "未知组合"
    
    # 格式化输出开仓信息 - 仿照Terminal#4-9风格
    logger.success(f"RandomMartingale | {方向} | 开仓: {round(价格, 5)} | 止损: {round(SL值, 5)} | 止盈: {round(TP值, 5)} | 马丁倍数: {当前倍数:.0f}x --( {阴阳显示} )--")
    
    # 返回交易成功状态、订单号和开仓价格
    return True, result.order, {"开仓价格": 价格, "订单类型": 订单类型, "手数": 手数}

def 检查持仓状态(交易品种):
    """检查当前持仓状态"""
    positions = mt5.positions_get(symbol=交易品种)
    
    if positions is None:
        return False
    
    return len(positions) > 0

def 等待平仓(交易品种, 订单号, 开仓信息, 检查间隔=5):
    """等待当前持仓平仓并返回交易结果"""
    while True:
        if not 检查持仓状态(交易品种):
            break
        time.sleep(检查间隔)
    
    # 获取平仓价格并计算盈亏
    return 计算交易盈亏(开仓信息, 交易品种)

def 计算交易盈亏(开仓信息, 交易品种):
    """根据开仓和平仓价格计算交易盈亏"""
    from datetime import datetime, timedelta
    
    开仓价格 = 开仓信息["开仓价格"]
    订单类型 = 开仓信息["订单类型"]
    手数 = 开仓信息["手数"]
    
    # 方法1：尝试从MT5历史记录获取实际平仓价格
    实际平仓价格 = None
    实际盈亏 = None
    account_info = mt5.account_info()
    try:
        # 获取最近的历史交易记录
        结束时间 = datetime.now()
        开始时间 = 结束时间 - timedelta(minutes=10)  # 查看最近10分钟的记录
        
        # 获取历史交易记录
        deals = mt5.history_deals_get(开始时间, 结束时间)
        
        if deals is not None and len(deals) > 0:
            # 查找本策略最新的平仓交易
            for deal in reversed(deals):  # 从最新的开始查找
                if (deal.magic == 234000 and 
                    deal.symbol == 交易品种 and
                    deal.entry == mt5.DEAL_ENTRY_OUT):  # 平仓交易
                    实际平仓价格 = deal.price
                    实际盈亏 = deal.profit
                    logger.info(f"获取到实际平仓价格: {round(实际平仓价格, 5)} | 实际盈亏: {实际盈亏:.2f} USD | 余额: ${account_info.balance:.2f}")
                    break
    except Exception as e:
        logger.warning(f"获取历史记录失败: {e}")
    
    # 方法2：如果无法获取历史记录，使用当前市场价格估算
    if 实际平仓价格 is None or 实际盈亏 is None:
        logger.warning("无法获取实际平仓价格，使用当前市场价格估算")
        
        tick = mt5.symbol_info_tick(交易品种)
        if tick is None:
            logger.error(f"获取市场价格失败: {mt5.last_error()}")
            return "未知", 0
        
        # 根据订单类型确定平仓价格
        if 订单类型 == mt5.ORDER_TYPE_BUY:
            估算平仓价格 = tick.bid
            价格差 = 估算平仓价格 - 开仓价格
        else:
            估算平仓价格 = tick.ask
            价格差 = 开仓价格 - 估算平仓价格
        
        # 计算盈亏（ETH每点价值约为手数*1美元）
        估算盈亏 = 价格差 * 手数 * 100
        
        # logger.info(f"估算平仓价格: {round(估算平仓价格, 5)} | 价格差: {round(价格差, 5)} | 估算盈亏: {估算盈亏:.2f} USD")
        
        # 使用估算值
        实际盈亏 = 估算盈亏
    
    # 判断交易结果
    if 实际盈亏 > 0:
        return "盈利", 实际盈亏
    elif 实际盈亏 < 0:
        return "亏损", 实际盈亏
    else:
        return "平手", 实际盈亏

def 分析连续亏损次数():
    """分析连续亏损次数并计算建议马丁倍数"""
    from datetime import datetime, timedelta
    
    # 获取两天内的历史订单数据
    结束时间 = datetime.now()
    开始时间 = 结束时间 - timedelta(days=2)
    
    # 获取历史订单记录
    history_orders = mt5.history_orders_get(开始时间, 结束时间)
    
    if history_orders is None:
        return 0, 1  # 返回连续亏损次数0，建议倍数1
    
    # 过滤出本策略的订单（通过magic number识别）
    本策略订单 = [order for order in history_orders if order.magic == 234000]
    
    if not 本策略订单:
        return 0, 1  # 返回连续亏损次数0，建议倍数1
    
    # 按时间倒序排列，从最新订单开始分析
    本策略订单.sort(key=lambda x: x.time_setup, reverse=True)
    
    连续亏损次数 = 0
    
    # 从最新订单开始倒序分析
    for order in 本策略订单:
        # 获取该订单的交易记录
        deals = mt5.history_deals_get(ticket=order.ticket)
        
        if deals is None or len(deals) == 0:
            # 尝试通过position_id获取
            deals = mt5.history_deals_get(position=order.position_id)
            
        if deals is None or len(deals) == 0:
            continue
        
        # 计算该订单的盈亏
        订单盈亏 = 0
        for deal in deals:
            if deal.type == mt5.DEAL_TYPE_BUY or deal.type == mt5.DEAL_TYPE_SELL:
                订单盈亏 += deal.profit
        
        # 如果是亏损，增加连续亏损次数
        if 订单盈亏 < 0:
            连续亏损次数 += 1
        else:
            # 如果不是亏损，停止统计
            break
    
    # 根据连续亏损次数计算建议倍数：2^连续亏损次数
    建议倍数 = 2 ** 连续亏损次数
    
    return 连续亏损次数, 建议倍数

# 全局变量：累计亏损记录
累计亏损金额 = 0.0

def 马丁格尔手数管理(当前手数, 交易结果, 盈亏金额, 基础手数=0.1, 最大倍数=8):
    """马丁格尔手数管理策略 - 基于当前交易结果和累计亏损"""
    global 累计亏损金额
    
    最大手数 = 基础手数 * 最大倍数
    account_info = mt5.account_info()
    
    if 交易结果 == "盈利":
        # 更新累计亏损：减去本次盈利
        累计亏损金额 = max(0, 累计亏损金额 - 盈亏金额)  # 盈亏金额为正数，所以是减法
        
        if 累计亏损金额 > 0:
            # 还有未回本的亏损，马丁倍数减半
            新手数 = max(基础手数, 当前手数 / 2)
            新倍数 = 新手数 / 基础手数
            logger.trace(f"平仓结果: 盈利 +{盈亏金额:.2f} USD | 累计亏损: -{累计亏损金额:.2f} USD | 未回本，马丁减半: {新倍数:.0f}x | 余额: ${account_info.balance:.2f}")
        else:
            # 已回本，重置为基础手数
            新手数 = 基础手数
            新倍数 = 1
            logger.trace(f"平仓结果: 盈利 +{盈亏金额:.2f} USD | 已回本 | 马丁重置: {新倍数:.0f}x | 余额: ${account_info.balance:.2f}")
    elif 交易结果 == "亏损":
        # 累计亏损增加
        累计亏损金额 += abs(盈亏金额)  # 盈亏金额为负数，取绝对值
        
        # 亏损后倍增手数，但不超过最大手数
        新手数 = min(最大手数, 当前手数 * 2)
        新倍数 = 新手数 / 基础手数
        logger.error(f"平仓结果: 亏损 {盈亏金额:.2f} USD | 累计亏损: -{累计亏损金额:.2f} USD | 下一次马丁倍数: {新倍数:.0f}x | 余额: ${account_info.balance:.2f}")
    else:
        # 平手时保持当前手数，累计亏损不变
        新手数 = 当前手数
        新倍数 = 新手数 / 基础手数
        logger.success(f"平仓结果: 平手 {盈亏金额:.2f} USD | 累计亏损: -{累计亏损金额:.2f} USD | 下一次马丁倍数: {新倍数:.0f}x | 余额: ${account_info.balance:.2f}")
    
    return 新手数

def 读取种子配置():
    """从配置文件读取随机数种子"""
    配置文件路径 = "种子配置.txt"
    默认种子 = 1006111951111
    
    try:
        if os.path.exists(配置文件路径):
            # 尝试多种编码方式读取文件
            编码列表 = ['utf-8', 'gbk', 'utf-16', 'ascii']
            for 编码 in 编码列表:
                try:
                    with open(配置文件路径, 'r', encoding=编码) as f:
                        for line in f:
                            line = line.strip()
                            # 跳过注释行和空行
                            if line and not line.startswith('#'):
                                try:
                                    种子值 = int(line)
                                    if 种子值 > 0:
                                        return 种子值
                                except ValueError:
                                    continue
                    break  # 成功读取后跳出编码循环
                except UnicodeDecodeError:
                    continue  # 尝试下一种编码
        return 默认种子
    except Exception as e:
        logger.error(f"读取种子配置文件失败: {e}")
        return 默认种子

def 主程序():
    """主程序入口"""
    global 累计亏损金额
    
    # 初始化参数
    交易品种 = "XAUUSDm"
    随机数种子 = 读取种子配置()  # 从配置文件读取种子
    冷却时间 = 64  # 秒
    基础手数 = 0.01  # 马丁格尔基础手数
    
    # 注意：累计亏损金额使用全局变量，不在此处重置
    
    # 初始化MT5连接
    if not 初始化MT5连接():
        return
    
    account_info = mt5.account_info()
    logger.info(f"MT5连接成功！")
    logger.info(f"账户: {account_info.login}")
    logger.info(f"服务器: {account_info.server}")
    logger.info(f"余额: ${account_info.balance:.2f}")
    logger.info(f"当前累计亏损状态: ${累计亏损金额:.2f}")
    
    # 检查当前持仓状态并计算初始手数
    当前手数 = 基础手数  # 默认值
    
    if 检查持仓状态(交易品种):
        # 如果存在持仓，根据持仓手数计算马丁倍数
        positions = mt5.positions_get(symbol=交易品种)
        if positions and len(positions) > 0:
            持仓手数 = positions[0].volume
            当前倍数 = 持仓手数 / 基础手数
            当前手数 = 持仓手数
            logger.info(f"检测到现有持仓 | 持仓手数: {持仓手数} | 当前马丁倍数: {当前倍数:.0f}x")
    else:
        # 如果没有持仓，询问用户输入倍数
        try:
            用户输入倍数 = float(input("请输入开仓马丁倍数 (默认1): ") or "1")
            if 用户输入倍数 <= 0:
                用户输入倍数 = 1
                logger.warning("输入倍数无效，使用默认值1")
            当前手数 = 基础手数 * 用户输入倍数
            logger.info(f"用户设置马丁倍数: {用户输入倍数:.0f}x | 开仓手数: {当前手数}")
        except ValueError:
            logger.warning("输入格式错误，使用默认倍数1x")
            当前手数 = 基础手数
    
    当前倍数 = 当前手数 / 基础手数
    logger.info(f"程序启动 | 启动倍数: {当前倍数:.0f}x")
    logger.info(f"当前随机数种子: {随机数种子}")
    
    # 记录配置文件的最后修改时间
    配置文件路径 = "种子配置.txt"
    上次修改时间 = 0
    if os.path.exists(配置文件路径):
        上次修改时间 = os.path.getmtime(配置文件路径)
    
    try:
        while True:
            # 检查种子配置文件是否有更新
            if os.path.exists(配置文件路径):
                当前修改时间 = os.path.getmtime(配置文件路径)
                if 当前修改时间 > 上次修改时间:
                    新种子 = 读取种子配置()
                    if 新种子 != 随机数种子:
                        随机数种子 = 新种子
                        random.seed(随机数种子)
                        logger.info(f"种子配置已更新: {随机数种子}")
                    上次修改时间 = 当前修改时间
            # 优先检查是否有持仓（无论什么时间都要处理平仓）
            if 检查持仓状态(交易品种):
                # 这里需要获取当前持仓的订单号，简化处理
                positions = mt5.positions_get(symbol=交易品种)
                if positions and len(positions) > 0:
                    订单号 = positions[0].ticket
                    # 注意：这里无法获取开仓信息，需要在新开仓时处理
                    logger.warning("检测到已有持仓，等待平仓...")
                    while 检查持仓状态(交易品种):
                        time.sleep(5)
                    logger.info("持仓已平仓，继续交易循环")
                
                time.sleep(冷却时间)
                continue
            
            # 检查当前时间是否大于12:00
            # 当前时间 = datetime.now()
            # if not ((0 <= 当前时间.hour < 12) or (20 <= 当前时间.hour < 22)):
            #     time.sleep(5)  # 等待1分钟后再次检查
            #     continue
            
            # 获取当前K线阴阳
            K线形态 = 获取当前K线阴阳(交易品种)
            if K线形态 is None:
                time.sleep(60)
                continue
            
            # 生成随机数序列
            随机数1, 随机数2, 随机数3 = 生成随机数序列(随机数种子)
            
            # 获取交易策略
            订单类型, TP值, SL值 = 获取交易策略(K线形态, 随机数1, 随机数2, 随机数3)
            
            # 执行交易
            当前倍数 = 当前手数 / 基础手数
            阴阳组合 = (K线形态, 随机数1, 随机数2, 随机数3)

            交易成功, 订单号, 开仓信息 = 执行交易(交易品种, 订单类型, TP值, SL值, 当前手数, 当前倍数, 阴阳组合)
            if 交易成功:
                交易结果, 盈亏金额 = 等待平仓(交易品种, 订单号, 开仓信息)
                当前手数 = 马丁格尔手数管理(当前手数, 交易结果, 盈亏金额, 基础手数)
            
            # 等待下一个周期
            time.sleep(60)  # 等待1分钟后再次检查
            
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    主程序()