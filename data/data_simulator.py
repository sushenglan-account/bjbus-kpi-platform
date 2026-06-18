"""
数据模拟器 - 生成北京公交KPI测试数据
用于演示和测试业务数据洞察平台
"""
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import json


class BJBusDataSimulator:
    """北京公交KPI数据模拟器"""
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        np.random.seed(seed)
        self.branch_companies = ["第一客运分公司", "第二客运分公司", "第三客运分公司", 
                                 "第四客运分公司", "第五客运分公司", "郊区客运分公司"]
        self.lines = [f"{i}路" for i in range(1, 101)]  # 100条线路
        self.time_periods = ["早高峰(07:00-09:00)", "平峰(09:00-17:00)", 
                            "晚高峰(17:00-19:00)", "夜间(19:00-23:00)"]
        
    def generate_operation_data(self, days: int = 30) -> pd.DataFrame:
        """生成运营核心数据"""
        data = []
        base_date = datetime.now() - timedelta(days=days)
        
        for day in range(days):
            date = base_date + timedelta(days=day)
            for line in random.sample(self.lines, 50):  # 每天随机50条线路
                data.append({
                    '日期': date.strftime('%Y-%m-%d'),
                    '线路': line,
                    '班次数': random.randint(80, 150),
                    '运行公里': random.randint(2000, 5000),
                    '出车次数': random.randint(30, 60),
                    '客运量': random.randint(5000, 15000),
                    '刷卡量': random.randint(3000, 10000),
                    '出车率': round(random.uniform(0.75, 0.98), 2),
                    '配班率': round(random.uniform(0.80, 0.95), 2),
                    '准点率': round(random.uniform(0.85, 0.99), 2),
                    '分公司': random.choice(self.branch_companies)
                })
        
        return pd.DataFrame(data)
    
    def generate_safety_data(self, days: int = 30) -> pd.DataFrame:
        """生成安全告警数据"""
        data = []
        base_date = datetime.now() - timedelta(days=days)
        
        alarm_types = ['ADAS车道偏离', 'ADAS前碰撞', 'DMS疲劳驾驶', 'DMS接打电话',
                      'CAN急加速', 'CAN急刹车', '进站违规', '出站违规', '山区超速']
        
        for day in range(days):
            date = base_date + timedelta(days=day)
            num_alarms = random.randint(20, 100)
            
            for _ in range(num_alarms):
                data.append({
                    '日期': date.strftime('%Y-%m-%d'),
                    '告警类型': random.choice(alarm_types),
                    '线路': random.choice(self.lines),
                    '车辆编号': f"京A{random.randint(10000, 99999)}",
                    '分公司': random.choice(self.branch_companies),
                    '处理状态': random.choice(['已处理', '处理中', '未处理'])
                })
        
        return pd.DataFrame(data)
    
    def generate_driver_data(self, days: int = 30) -> pd.DataFrame:
        """生成驾驶员管理数据"""
        data = []
        base_date = datetime.now() - timedelta(days=days)
        
        # 模拟驾驶员工号
        drivers = [f"D{str(i).zfill(6)}" for i in range(1, 201)]  # 200名驾驶员
        
        for day in range(days):
            date = base_date + timedelta(days=day)
            
            for driver in random.sample(drivers, 80):  # 每天记录80名驾驶员
                data.append({
                    '日期': date.strftime('%Y-%m-%d'),
                    '工号': driver,
                    '分公司': random.choice(self.branch_companies),
                    '线路': random.choice(self.lines),
                    '在岗状态': random.choice(['在岗', '休假', '培训']),
                    '驾驶时长(小时)': round(random.uniform(4, 10), 1),
                    '运营趟次': random.randint(6, 12),
                    '违章次数': random.randint(0, 2),
                    '投诉次数': random.randint(0, 1),
                    '安全评分': random.randint(75, 100)
                })
        
        return pd.DataFrame(data)
    
    def generate_passenger_data(self, days: int = 30) -> pd.DataFrame:
        """生成乘客客流数据"""
        data = []
        base_date = datetime.now() - timedelta(days=days)
        
        for day in range(days):
            date = base_date + timedelta(days=day)
            for period in self.time_periods:
                for line in random.sample(self.lines, 30):
                    data.append({
                        '日期': date.strftime('%Y-%m-%d'),
                        '时段': period,
                        '线路': line,
                        '客流量': random.randint(500, 3000),
                        '老年乘客占比': round(random.uniform(0.1, 0.3), 2),
                        '学生乘客占比': round(random.uniform(0.05, 0.15), 2),
                        '平均等待时间(分钟)': round(random.uniform(3, 10), 1)
                    })
        
        return pd.DataFrame(data)
    
    def generate_kpi_summary(self) -> Dict:
        """生成KPI汇总指标"""
        return {
            '今日客运总量': random.randint(800000, 1200000),
            '今日出车率': round(random.uniform(0.85, 0.95), 2),
            '今日准点率': round(random.uniform(0.90, 0.98), 2),
            '今日事故数': random.randint(0, 5),
            '今日告警数': random.randint(50, 200),
            '在线车辆数': random.randint(5000, 7000),
            '运营线路数': 100,
            '今日投诉数': random.randint(10, 50),
            '驾驶员在岗数': random.randint(8000, 10000),
            '运营班次': random.randint(12000, 15000)
        }
    
    def generate_line_ranking(self, metric: str = '客运量', top_n: int = 20) -> pd.DataFrame:
        """生成线路排名数据"""
        data = []
        for line in self.lines[:top_n]:
            data.append({
                '线路': line,
                metric: random.randint(10000, 50000),
                '分公司': random.choice(self.branch_companies),
                '环比变化': f"{random.choice(['+', '-'])}{random.randint(1, 20)}%"
            })
        
        df = pd.DataFrame(data)
        df = df.sort_values(by=metric, ascending=False)
        df['排名'] = range(1, len(df) + 1)
        return df[['排名', '线路', metric, '分公司', '环比变化']]
    
    def generate_time_series(self, days: int = 30, metric: str = '客运量') -> pd.DataFrame:
        """生成时间序列数据"""
        data = []
        base_date = datetime.now() - timedelta(days=days)
        
        for day in range(days):
            date = base_date + timedelta(days=day)
            # 模拟周期性模式
            weekday_factor = 1.0 if date.weekday() < 5 else 0.7
            base_value = random.randint(100000, 150000)
            
            data.append({
                '日期': date.strftime('%Y-%m-%d'),
                metric: int(base_value * weekday_factor),
                '环比': round(random.uniform(0.95, 1.05), 2)
            })
        
        return pd.DataFrame(data)
    
    def generate_alarm_distribution(self) -> pd.DataFrame:
        """生成告警类型分布"""
        alarm_types = ['ADAS车道偏离', 'ADAS前碰撞', 'DMS疲劳驾驶', 'DMS接打电话',
                      'CAN急加速', 'CAN急刹车', '进站违规', '出站违规', 
                      '山区超速', '倒车超速']
        
        data = []
        total = random.randint(500, 1000)
        
        for alarm_type in alarm_types:
            count = random.randint(20, 150)
            data.append({
                '告警类型': alarm_type,
                '数量': count,
                '占比': f"{round(count / total * 100, 1)}%",
                '处理率': f"{random.randint(70, 95)}%"
            })
        
        df = pd.DataFrame(data)
        df = df.sort_values(by='数量', ascending=False)
        return df


# 使用示例
if __name__ == "__main__":
    simulator = BJBusDataSimulator()
    
    # 生成各类数据
    operation_data = simulator.generate_operation_data(days=30)
    safety_data = simulator.generate_safety_data(days=30)
    driver_data = simulator.generate_driver_data(days=30)
    passenger_data = simulator.generate_passenger_data(days=30)
    
    # 保存数据
    operation_data.to_csv('mock_operation_data.csv', index=False, encoding='utf-8-sig')
    safety_data.to_csv('mock_safety_data.csv', index=False, encoding='utf-8-sig')
    driver_data.to_csv('mock_driver_data.csv', index=False, encoding='utf-8-sig')
    passenger_data.to_csv('mock_passenger_data.csv', index=False, encoding='utf-8-sig')
    
    print("数据生成完成！")
    print(f"运营数据: {len(operation_data)} 条记录")
    print(f"安全数据: {len(safety_data)} 条记录")
    print(f"驾驶员数据: {len(driver_data)} 条记录")
    print(f"乘客数据: {len(passenger_data)} 条记录")
