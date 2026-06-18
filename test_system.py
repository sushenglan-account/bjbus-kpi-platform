#!/usr/bin/env python3
"""
系统测试脚本
验证本体加载、NL2SQL流水线、数据模拟器、洞察分析器等功能
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_ontology_loader():
    """测试本体加载器"""
    print("\n" + "="*60)
    print("测试1: 本体加载器")
    print("="*60)
    
    from core.ontology_loader_kpi import BJBusKPIOntology
    
    ttl_path = project_root / "data" / "bjbus_kpi_ontology.ttl"
    ont = BJBusKPIOntology(ttl_path)
    
    # 列出概念
    concepts = ont.list_concepts()
    print(f"✓ 成功加载 {len(concepts)} 个业务概念")
    print(f"  示例: {sorted(concepts)[:5]}")
    
    # 测试意图路由
    test_queries = [
        ("今日各线路班次和运行公里", "O-01"),
        ("当前出车率和配班率", "O-02"),
        ("今日事故情况", "S-01"),
        ("ADAS告警类型分布", "S-04"),
        ("疲劳驾驶告警", "S-05"),
    ]
    
    passed = 0
    for query, expected in test_queries:
        result = ont.route_intent(query)
        if result == expected:
            passed += 1
            print(f"  ✓ '{query}' → {result}")
        else:
            print(f"  ✗ '{query}' → {result} (期望: {expected})")
    
    print(f"\n意图路由测试: {passed}/{len(test_queries)} 通过")
    
    # 验证治理规则
    errors = ont.validate_governance()
    if errors:
        print(f"\n⚠ 治理验证发现问题:")
        for e in errors[:3]:
            print(f"  - {e}")
    else:
        print("\n✓ 治理验证通过")
    
    return len(concepts) > 0


def test_nl2sql_pipeline():
    """测试NL2SQL流水线"""
    print("\n" + "="*60)
    print("测试2: NL2SQL流水线")
    print("="*60)
    
    from core.nl2sql_pipeline_kpi import NL2SQLPipelineKPI
    
    ttl_path = project_root / "data" / "bjbus_kpi_ontology.ttl"
    pipeline = NL2SQLPipelineKPI(ttl_path)
    
    test_queries = [
        ("今日各线路班次统计", "O-01"),
        ("准点率排名前10的线路", "O-06"),
        ("今日交通事故统计", "S-01"),
        ("DMS疲劳驾驶告警排名前5", "S-05"),
        ("连续运营超4小时告警", "D-02"),
    ]
    
    passed = 0
    for query, expected_concept in test_queries:
        result = pipeline.process(query)
        
        if result['concept_id'] == expected_concept and result['sql']:
            passed += 1
            print(f"\n✓ 查询: '{query}'")
            print(f"  概念ID: {result['concept_id']}")
            print(f"  SQL: {result['sql'][:80]}...")
        else:
            print(f"\n✗ 查询: '{query}'")
            print(f"  概念ID: {result['concept_id']} (期望: {expected_concept})")
    
    print(f"\n流水线测试: {passed}/{len(test_queries)} 通过")
    
    return passed == len(test_queries)


def test_data_simulator():
    """测试数据模拟器"""
    print("\n" + "="*60)
    print("测试3: 数据模拟器")
    print("="*60)
    
    from data.data_simulator import BJBusDataSimulator
    
    simulator = BJBusDataSimulator(seed=42)
    
    # 生成各类数据
    operation_data = simulator.generate_operation_data(days=7)
    safety_data = simulator.generate_safety_data(days=7)
    driver_data = simulator.generate_driver_data(days=7)
    passenger_data = simulator.generate_passenger_data(days=7)
    
    print(f"✓ 运营数据: {len(operation_data)} 条记录")
    print(f"✓ 安全数据: {len(safety_data)} 条记录")
    print(f"✓ 驾驶员数据: {len(driver_data)} 条记录")
    print(f"✓ 乘客数据: {len(passenger_data)} 条记录")
    
    # 测试KPI汇总
    kpi_summary = simulator.generate_kpi_summary()
    print(f"\n✓ KPI汇总指标: {len(kpi_summary)} 个")
    for key, value in list(kpi_summary.items())[:3]:
        print(f"  - {key}: {value}")
    
    return (len(operation_data) > 0 and len(safety_data) > 0 and 
            len(driver_data) > 0 and len(passenger_data) > 0)


def test_insight_analyzer():
    """测试洞察分析器"""
    print("\n" + "="*60)
    print("测试4: 洞察分析器")
    print("="*60)
    
    from core.insight_analyzer import InsightAnalyzer
    from data.data_simulator import BJBusDataSimulator
    
    simulator = BJBusDataSimulator(seed=42)
    analyzer = InsightAnalyzer()
    
    # 生成测试数据
    operation_data = simulator.generate_operation_data(days=7)
    safety_data = simulator.generate_safety_data(days=7)
    driver_data = simulator.generate_driver_data(days=7)
    
    # 分析运营洞察
    operation_insights = analyzer.analyze_operation_insights(operation_data)
    print(f"✓ 运营洞察: {len(operation_insights)} 条")
    if operation_insights:
        print(f"  示例: {operation_insights[0]['insight'][:50]}...")
    
    # 分析安全洞察
    safety_insights = analyzer.analyze_safety_insights(safety_data)
    print(f"✓ 安全洞察: {len(safety_insights)} 条")
    
    # 分析驾驶员洞察
    driver_insights = analyzer.analyze_driver_insights(driver_data)
    print(f"✓ 驾驶员洞察: {len(driver_insights)} 条")
    
    # 生成综合报告
    report = analyzer.generate_comprehensive_report(operation_data, safety_data, driver_data)
    print(f"\n✓ 综合报告生成成功")
    print(f"  总洞察数: {report['total_insights']}")
    print(f"  严重: {report['critical_count']}")
    print(f"  高优: {report['high_count']}")
    
    return report['total_insights'] > 0


def test_chart_generator():
    """测试图表生成器"""
    print("\n" + "="*60)
    print("测试5: 图表生成器")
    print("="*60)
    
    from components.charts import ChartGenerator
    import pandas as pd
    import numpy as np
    
    chart_gen = ChartGenerator()
    
    # 测试折线图
    df_line = pd.DataFrame({
        '日期': pd.date_range('2026-01-01', periods=30),
        '客运量': np.random.randn(30).cumsum() + 100
    })
    fig_line = chart_gen.create_line_chart(df_line, '日期', '客运量', '测试折线图')
    print("✓ 折线图生成成功")
    
    # 测试柱状图
    df_bar = pd.DataFrame({
        '线路': ['1路', '2路', '3路', '4路', '5路'],
        '客运量': [10000, 12000, 8000, 15000, 9000]
    })
    fig_bar = chart_gen.create_bar_chart(df_bar, '线路', '客运量', '测试柱状图')
    print("✓ 柱状图生成成功")
    
    # 测试饼图
    df_pie = pd.DataFrame({
        '类型': ['A', 'B', 'C', 'D'],
        '数量': [30, 25, 20, 25]
    })
    fig_pie = chart_gen.create_pie_chart(df_pie, '类型', '数量', '测试饼图')
    print("✓ 饼图生成成功")
    
    # 测试仪表盘
    fig_gauge = chart_gen.create_gauge_chart(85, '出车率', max_val=100)
    print("✓ 仪表盘生成成功")
    
    return True


def main():
    """主测试函数"""
    print("\n" + "🚌"*30)
    print("北京公交KPI看板 - 系统测试")
    print("🚌"*30)
    
    results = {
        '本体加载器': test_ontology_loader(),
        'NL2SQL流水线': test_nl2sql_pipeline(),
        '数据模拟器': test_data_simulator(),
        '洞察分析器': test_insight_analyzer(),
        '图表生成器': test_chart_generator()
    }
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for module, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{module}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\n总计: {total_passed}/{total_tests} 模块测试通过")
    
    if total_passed == total_tests:
        print("\n🎉 所有测试通过！系统运行正常。")
        print("\n启动应用: streamlit run app.py")
        return 0
    else:
        print("\n⚠ 部分测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
