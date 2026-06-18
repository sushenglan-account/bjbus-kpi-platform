"""
业务数据洞察分析模块
基于本体规则实现智能数据分析与洞察
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import json


class InsightAnalyzer:
    """业务数据洞察分析器"""
    
    def __init__(self):
        self.rules = self._load_business_rules()
    
    def _load_business_rules(self) -> Dict:
        """加载业务规则（从本体中提取）"""
        return {
            'O-01': {
                'name': '路单发车班次',
                'rules': [
                    {'condition': '班次数 < 50', 'insight': '班次严重不足，需排查车辆或人员问题', 'priority': 'high'},
                    {'condition': '运行公里 > 4000', 'insight': '运行里程较长，注意车辆维护', 'priority': 'medium'}
                ]
            },
            'O-02': {
                'name': '出车率配班率',
                'rules': [
                    {'condition': '出车率 < 0.80', 'insight': '出车率偏低，影响运力供给', 'priority': 'high'},
                    {'condition': '配班率 < 0.85', 'insight': '配班率不足，需优化排班计划', 'priority': 'medium'}
                ]
            },
            'O-03': {
                'name': '客运量刷卡量',
                'rules': [
                    {'condition': '客运量 > 12000', 'insight': '客流高峰，考虑增加班次', 'priority': 'medium'},
                    {'condition': '刷卡量/客运量 < 0.5', 'insight': '现金支付比例高，推广移动支付', 'priority': 'low'}
                ]
            },
            'O-06': {
                'name': '准点率晚点',
                'rules': [
                    {'condition': '准点率 < 0.90', 'insight': '准点率不达标，影响服务质量', 'priority': 'high'},
                    {'condition': '晚点次数 > 10', 'insight': '晚点频发，需优化调度', 'priority': 'high'}
                ]
            },
            'S-01': {
                'name': '事故实时',
                'rules': [
                    {'condition': '事故次数 > 3', 'insight': '事故频发，需加强安全管理', 'priority': 'critical'}
                ]
            },
            'S-04': {
                'name': 'ADAS告警',
                'rules': [
                    {'condition': 'ADAS告警 > 50', 'insight': 'ADAS告警集中，驾驶员培训需加强', 'priority': 'high'}
                ]
            },
            'S-05': {
                'name': 'DMS告警',
                'rules': [
                    {'condition': 'DMS疲劳驾驶 > 10', 'insight': '疲劳驾驶风险高，需安排休息', 'priority': 'critical'},
                    {'condition': 'DMS接打电话 > 20', 'insight': '违规使用手机频繁，需加强教育', 'priority': 'high'}
                ]
            },
            'D-02': {
                'name': '连续运营超时',
                'rules': [
                    {'condition': '连续运营 > 4小时', 'insight': '违反劳动法规，强制休息', 'priority': 'critical'}
                ]
            }
        }
    
    def analyze_operation_insights(self, df: pd.DataFrame) -> List[Dict]:
        """分析运营数据洞察"""
        insights = []
        
        # 1. 出车率分析
        avg_departure_rate = df['出车率'].mean()
        if avg_departure_rate < 0.85:
            insights.append({
                'category': '运力供给',
                'metric': '平均出车率',
                'value': f"{avg_departure_rate:.1%}",
                'status': 'warning' if avg_departure_rate < 0.80 else 'attention',
                'insight': f"平均出车率为{avg_departure_rate:.1%}，低于85%的目标值",
                'suggestion': '建议排查车辆故障率、驾驶员出勤率等影响因素',
                'priority': 'high'
            })
        
        # 2. 准点率分析
        avg_punctuality = df['准点率'].mean()
        if avg_punctuality < 0.92:
            insights.append({
                'category': '服务质量',
                'metric': '平均准点率',
                'value': f"{avg_punctuality:.1%}",
                'status': 'warning' if avg_punctuality < 0.90 else 'attention',
                'insight': f"平均准点率为{avg_punctuality:.1%}，未达到92%的服务标准",
                'suggestion': '建议优化高峰期发车间隔，加强路况监控与调度',
                'priority': 'medium'
            })
        
        # 3. 线路排名分析
        line_passenger = df.groupby('线路')['客运量'].sum().sort_values(ascending=False)
        top_lines = line_passenger.head(5)
        bottom_lines = line_passenger.tail(5)
        
        insights.append({
            'category': '客流分布',
            'metric': '线路客运量差异',
            'value': f"前5名:{top_lines.index.tolist()}",
            'status': 'info',
            'insight': f"客流最高的5条线路占总客流的{top_lines.sum()/line_passenger.sum()*100:.1f}%",
            'suggestion': '建议在客流高峰期适当增加高频线路的班次密度',
            'priority': 'medium'
        })
        
        # 4. 分公司对比
        org_performance = df.groupby('分公司').agg({
            '客运量': 'sum',
            '出车率': 'mean',
            '准点率': 'mean'
        }).round(3)
        
        worst_org = org_performance['出车率'].idxmin()
        worst_rate = org_performance.loc[worst_org, '出车率']
        
        if worst_rate < 0.85:
            insights.append({
                'category': '组织绩效',
                'metric': '分公司出车率',
                'value': worst_org,
                'status': 'warning',
                'insight': f"{worst_org}出车率最低，仅{worst_rate:.1%}",
                'suggestion': '建议重点调研该分公司运力配置与调度管理',
                'priority': 'high'
            })
        
        return insights
    
    def analyze_safety_insights(self, df: pd.DataFrame) -> List[Dict]:
        """分析安全数据洞察"""
        insights = []
        
        # 1. 告警类型分布
        alarm_dist = df['告警类型'].value_counts()
        
        # ADAS告警分析
        adas_count = alarm_dist.get('ADAS车道偏离', 0) + alarm_dist.get('ADAS前碰撞', 0)
        if adas_count > 100:
            insights.append({
                'category': 'ADAS安全',
                'metric': 'ADAS告警总数',
                'value': str(adas_count),
                'status': 'warning',
                'insight': f"ADAS告警数量较高（{adas_count}次），主要集中在车道偏离和前碰撞",
                'suggestion': '建议加强驾驶员安全培训，重点关注弯道、复杂路况的驾驶技巧',
                'priority': 'high'
            })
        
        # DMS告警分析
        dms_fatigue = alarm_dist.get('DMS疲劳驾驶', 0)
        if dms_fatigue > 20:
            insights.append({
                'category': '驾驶员健康',
                'metric': 'DMS疲劳驾驶告警',
                'value': str(dms_fatigue),
                'status': 'critical',
                'insight': f"检测到{dms_fatigue}次疲劳驾驶告警，存在重大安全隐患",
                'suggestion': '立即安排相关驾驶员休息，优化排班制度，强制执行驾驶时长限制',
                'priority': 'critical'
            })
        
        # 2. 处理率分析
        processed = df[df['处理状态'] == '已处理'].shape[0]
        total = df.shape[0]
        process_rate = processed / total if total > 0 else 0
        
        if process_rate < 0.8:
            insights.append({
                'category': '安全管理',
                'metric': '告警处理率',
                'value': f"{process_rate:.1%}",
                'status': 'warning',
                'insight': f"告警处理率仅为{process_rate:.1%}，仍有{total-processed}条告警未处理",
                'suggestion': '建议建立告警分级响应机制，优先处理高风险告警',
                'priority': 'high'
            })
        
        # 3. 线路安全风险
        line_alarm = df.groupby('线路').size().sort_values(ascending=False)
        risk_lines = line_alarm.head(5)
        
        insights.append({
            'category': '线路风险',
            'metric': '高风险线路',
            'value': risk_lines.index.tolist(),
            'status': 'warning',
            'insight': f"告警最集中的5条线路占总量{risk_lines.sum()/total*100:.1f}%",
            'suggestion': '建议对高风险线路开展专项整治，加强路段巡查',
            'priority': 'medium'
        })
        
        return insights
    
    def analyze_driver_insights(self, df: pd.DataFrame) -> List[Dict]:
        """分析驾驶员管理数据洞察"""
        insights = []
        
        # 1. 驾驶时长分析
        overwork_drivers = df[df['驾驶时长(小时)'] > 8]['工号'].nunique()
        if overwork_drivers > 0:
            insights.append({
                'category': '劳动保护',
                'metric': '超时驾驶员',
                'value': str(overwork_drivers),
                'status': 'critical',
                'insight': f"发现{overwork_drivers}名驾驶员单日驾驶时长超过8小时",
                'suggestion': '立即调整排班计划，确保符合劳动法规要求',
                'priority': 'critical'
            })
        
        # 2. 安全评分分析
        low_score_drivers = df[df['安全评分'] < 80]['工号'].nunique()
        if low_score_drivers > 10:
            insights.append({
                'category': '驾驶员素质',
                'metric': '低安全评分驾驶员',
                'value': str(low_score_drivers),
                'status': 'warning',
                'insight': f"有{low_score_drivers}名驾驶员安全评分低于80分",
                'suggestion': '建议开展专项安全培训，建立重点人员档案',
                'priority': 'high'
            })
        
        # 3. 在岗率分析
        attendance_rate = df[df['在岗状态'] == '在岗'].shape[0] / df.shape[0]
        if attendance_rate < 0.85:
            insights.append({
                'category': '人员管理',
                'metric': '驾驶员在岗率',
                'value': f"{attendance_rate:.1%}",
                'status': 'warning',
                'insight': f"驾驶员在岗率为{attendance_rate:.1%}，低于目标值",
                'suggestion': '排查休假、培训、病假等原因，优化人力资源配置',
                'priority': 'medium'
            })
        
        return insights
    
    def generate_comprehensive_report(self, operation_df: pd.DataFrame, 
                                     safety_df: pd.DataFrame, 
                                     driver_df: pd.DataFrame) -> Dict:
        """生成综合洞察报告"""
        operation_insights = self.analyze_operation_insights(operation_df)
        safety_insights = self.analyze_safety_insights(safety_df)
        driver_insights = self.analyze_driver_insights(driver_df)
        
        all_insights = operation_insights + safety_insights + driver_insights
        
        # 按优先级排序
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        all_insights.sort(key=lambda x: priority_order.get(x['priority'], 5))
        
        return {
            'report_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_insights': len(all_insights),
            'critical_count': sum(1 for i in all_insights if i['priority'] == 'critical'),
            'high_count': sum(1 for i in all_insights if i['priority'] == 'high'),
            'medium_count': sum(1 for i in all_insights if i['priority'] == 'medium'),
            'insights': all_insights,
            'summary': {
                'operation': {
                    'total_records': len(operation_df),
                    'avg_departure_rate': f"{operation_df['出车率'].mean():.1%}",
                    'avg_punctuality': f"{operation_df['准点率'].mean():.1%}",
                    'total_passengers': f"{operation_df['客运量'].sum():,}"
                },
                'safety': {
                    'total_alarms': len(safety_df),
                    'process_rate': f"{safety_df[safety_df['处理状态']=='已处理'].shape[0]/len(safety_df):.1%}",
                    'top_alarm_type': safety_df['告警类型'].value_counts().index[0] if len(safety_df) > 0 else 'N/A'
                },
                'driver': {
                    'total_drivers': driver_df['工号'].nunique(),
                    'attendance_rate': f"{driver_df[driver_df['在岗状态']=='在岗'].shape[0]/len(driver_df):.1%}",
                    'avg_safety_score': f"{driver_df['安全评分'].mean():.0f}"
                }
            }
        }


# 使用示例
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from data.data_simulator import BJBusDataSimulator
    
    # 生成测试数据
    simulator = BJBusDataSimulator()
    operation_data = simulator.generate_operation_data(days=30)
    safety_data = simulator.generate_safety_data(days=30)
    driver_data = simulator.generate_driver_data(days=30)
    
    # 分析洞察
    analyzer = InsightAnalyzer()
    report = analyzer.generate_comprehensive_report(operation_data, safety_data, driver_data)
    
    print("=" * 60)
    print(f"业务数据洞察报告 - {report['report_time']}")
    print("=" * 60)
    print(f"\n总洞察数: {report['total_insights']}")
    print(f"  - 严重: {report['critical_count']}")
    print(f"  - 高优先级: {report['high_count']}")
    print(f"  - 中优先级: {report['medium_count']}")
    
    print("\n关键洞察:")
    for i, insight in enumerate(report['insights'][:10], 1):
        print(f"\n{i}. [{insight['priority'].upper()}] {insight['category']} - {insight['metric']}")
        print(f"   洞察: {insight['insight']}")
        print(f"   建议: {insight['suggestion']}")
