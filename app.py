"""
北京公交KPI看板 - 智能问数与业务数据洞察平台
基于本体驱动的主应用
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import plotly.graph_objects as go

from core.nl2sql_pipeline_kpi import NL2SQLPipelineKPI
from core.insight_analyzer import InsightAnalyzer
from data.data_simulator import BJBusDataSimulator
from components.charts import ChartGenerator


# 页面配置
st.set_page_config(
    page_title="北京公交KPI看板",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .insight-critical {
        border-left: 4px solid #d32f2f;
        background-color: #ffebee;
        padding: 15px;
        margin: 10px 0;
    }
    .insight-high {
        border-left: 4px solid #f57c00;
        background-color: #fff3e0;
        padding: 15px;
        margin: 10px 0;
    }
    .insight-medium {
        border-left: 4px solid #1976d2;
        background-color: #e3f2fd;
        padding: 15px;
        margin: 10px 0;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


# ── session_state 初始化 ──────────────────────────────────────
# auto_query: 快速查询回传的查询文本
# auto_query_triggered: 是否由快速查询/示例触发（非手动点击查询按钮）
# pending_query: 示例按钮回传的查询文本
# last_quick_query_value: 快速查询 selectbox 上一次的值，用于检测选择变化
if 'auto_query' not in st.session_state:
    st.session_state.auto_query = ''
if 'auto_query_triggered' not in st.session_state:
    st.session_state.auto_query_triggered = False
if 'pending_query' not in st.session_state:
    st.session_state.pending_query = ''
if 'last_quick_query_value' not in st.session_state:
    st.session_state.last_quick_query_value = ''


@st.cache_resource
def init_components():
    """初始化组件"""
    # 加载本体
    ttl_path = os.path.join(os.path.dirname(__file__), 'data', 'bjbus_kpi_ontology.ttl')
    pipeline = NL2SQLPipelineKPI(ttl_path)
    
    # 初始化其他组件
    simulator = BJBusDataSimulator()
    analyzer = InsightAnalyzer()
    chart_gen = ChartGenerator()
    
    return pipeline, simulator, analyzer, chart_gen


@st.cache_data
def generate_data(days: int = 30):
    """生成模拟数据"""
    simulator = BJBusDataSimulator()
    operation_data = simulator.generate_operation_data(days=days)
    safety_data = simulator.generate_safety_data(days=days)
    driver_data = simulator.generate_driver_data(days=days)
    passenger_data = simulator.generate_passenger_data(days=days)
    
    return operation_data, safety_data, driver_data, passenger_data


def render_sidebar():
    """渲染侧边栏"""
    st.sidebar.title("🚌 北京公交KPI看板")
    st.sidebar.markdown("---")
    
    # 功能选择
    PAGES = ["📊 业务数据洞察", "💬 智能问数", "📈 运营分析", "🚨 安全监控", "👨‍✈️ 驾驶员管理"]
    page = st.sidebar.radio("功能模块", PAGES, key="page_radio")
    
    st.sidebar.markdown("---")
    
    # 数据设置
    st.sidebar.subheader("数据设置")
    days = st.sidebar.slider("数据时间范围(天)", 7, 90, 30)
    
    st.sidebar.markdown("---")
    
    # 快速查询
    st.sidebar.subheader("快速查询")
    quick_queries = [
        "今日各线路班次统计",
        "出车率最低的线路",
        "准点率排名前10",
        "今日ADAS告警情况",
        "疲劳驾驶告警统计",
        "客运量趋势分析"
    ]
    
    def on_quick_query_change():
        """快速查询选择变更回调：检测选择变化，自动跳转+填充+触发
        
        核心思路：在 on_change 回调中可以安全修改 widget 绑定的 session_state key。
        通过对比 last_quick_query_value 检测"真正的选择变化"，
        解决"重复选择同一项不触发回调"的 Streamlit 限制（不需要重置 selectbox）。
        """
        new_val = st.session_state.quick_query_select
        old_val = st.session_state.last_quick_query_value
        
        if new_val and new_val != old_val:
            # 用户选择了新的快速查询项
            st.session_state.auto_query = new_val
            st.session_state.auto_query_triggered = True
            st.session_state.page_radio = "💬 智能问数"
            # 在回调中可以安全设置 widget key 的值（回调先于脚本执行）
            st.session_state.query_input = new_val
        elif not new_val:
            # 用户切回空项
            st.session_state.auto_query = ''
            st.session_state.auto_query_triggered = False
        
        # 记录本次值，供下次对比
        st.session_state.last_quick_query_value = new_val
    
    selected_query = st.sidebar.selectbox(
        "选择查询", [""] + quick_queries,
        key="quick_query_select",
        on_change=on_quick_query_change
    )
    
    return page, days, selected_query


def render_metrics_row(metrics: dict):
    """渲染KPI指标行"""
    cols = st.columns(len(metrics))
    
    for i, (key, value) in enumerate(metrics.items()):
        with cols[i]:
            st.metric(
                label=key,
                value=value
            )


def page_business_insight(operation_data, safety_data, driver_data, analyzer, chart_gen):
    """业务数据洞察页面"""
    st.title("📊 业务数据洞察")
    st.markdown("基于本体规则的智能数据分析与洞察")
    
    # 生成综合报告
    report = analyzer.generate_comprehensive_report(operation_data, safety_data, driver_data)
    
    # 关键指标概览
    st.subheader("关键指标概览")
    metrics = {
        '平均出车率': report['summary']['operation']['avg_departure_rate'],
        '平均准点率': report['summary']['operation']['avg_punctuality'],
        '总客运量': report['summary']['operation']['total_passengers'],
        '告警处理率': report['summary']['safety']['process_rate'],
        '驾驶员在岗率': report['summary']['driver']['attendance_rate'],
        '平均安全评分': report['summary']['driver']['avg_safety_score']
    }
    render_metrics_row(metrics)
    
    st.markdown("---")
    
    # 洞察列表
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("智能洞察")
        
        # 按优先级分组显示
        critical_insights = [i for i in report['insights'] if i['priority'] == 'critical']
        high_insights = [i for i in report['insights'] if i['priority'] == 'high']
        medium_insights = [i for i in report['insights'] if i['priority'] == 'medium']
        
        if critical_insights:
            st.markdown("#### 🔴 严重问题")
            for insight in critical_insights:
                st.markdown(f"""
                <div class='insight-critical'>
                    <strong>{insight['category']} - {insight['metric']}</strong><br/>
                    <span style='color: #d32f2f;'>{insight['insight']}</span><br/>
                    <em>建议: {insight['suggestion']}</em>
                </div>
                """, unsafe_allow_html=True)
        
        if high_insights:
            st.markdown("#### 🟠 高优先级")
            for insight in high_insights[:5]:  # 最多显示5个
                st.markdown(f"""
                <div class='insight-high'>
                    <strong>{insight['category']} - {insight['metric']}</strong><br/>
                    <span style='color: #f57c00;'>{insight['insight']}</span><br/>
                    <em>建议: {insight['suggestion']}</em>
                </div>
                """, unsafe_allow_html=True)
        
        if medium_insights:
            with st.expander(f"查看中等优先级洞察 ({len(medium_insights)})"):
                for insight in medium_insights:
                    st.markdown(f"""
                    <div class='insight-medium'>
                        <strong>{insight['category']} - {insight['metric']}</strong><br/>
                        <span style='color: #1976d2;'>{insight['insight']}</span><br/>
                        <em>建议: {insight['suggestion']}</em>
                    </div>
                    """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("洞察统计")
        
        # 洞察分布饼图
        df_dist = pd.DataFrame({
            '优先级': ['严重', '高', '中'],
            '数量': [report['critical_count'], report['high_count'], report['medium_count']]
        })
        fig_pie = chart_gen.create_pie_chart(df_dist, '优先级', '数量', '洞察分布')
        st.plotly_chart(fig_pie)
        
        # 类别分布
        categories = [i['category'] for i in report['insights']]
        if categories:
            st.markdown("#### 按类别")
            for cat in set(categories):
                count = categories.count(cat)
                st.write(f"- **{cat}**: {count}条")


def page_natural_query(pipeline, simulator, operation_data, safety_data, driver_data):
    """智能问数页面"""
    st.title("💬 智能问数")
    st.markdown("基于本体驱动的自然语言查询系统")
    
    # 查询输入
    # 注意：快速查询通过 on_change 回调设置 st.session_state.query_input，
    # 回调在 widget 实例化之前执行，因此可以安全修改。
    # 示例按钮通过 pending_query + st.rerun() 触发，
    # rerun 后在新一轮脚本中 query_input key 还未绑定，可以安全设置。
    if 'pending_query' in st.session_state and st.session_state.pending_query:
        if 'query_input' not in st.session_state:
            # 仅在 key 不存在时设置（首轮渲染或 rerun 后 key 已清空的情况）
            st.session_state.query_input = st.session_state.pending_query
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_query = st.text_input(
            "请输入您的问题",
            key="query_input",
            placeholder="例如：今日各线路班次统计、出车率最低的线路、准点率排名前10...",
            help="支持自然语言查询，系统会自动识别意图并生成SQL"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        query_button = st.button("🔍 查询", type="primary")
    
    # 示例查询
    with st.expander("💡 查询示例"):
        examples = [
            "今日各线路班次统计",
            "101路今日客运量",
            "准点率排名前10的线路",
            "今日交通事故统计",
            "ADAS告警中车道偏离多少次",
            "DMS疲劳驾驶告警排名前5",
            "连续运营超4小时告警"
        ]
        cols = st.columns(3)
        for i, example in enumerate(examples):
            with cols[i % 3]:
                if st.button(example, key=f"example_{i}"):
                    st.session_state.pending_query = example
                    st.session_state.auto_query_triggered = True
                    # 删除 query_input key，使 rerun 后可以安全重新设置
                    if 'query_input' in st.session_state:
                        del st.session_state.query_input
                    st.rerun()
    
    st.markdown("---")
    
    # 执行查询：快速查询/示例自动触发 或 手动点击查询按钮
    should_execute = bool(
        (st.session_state.auto_query_triggered and user_query) or
        (query_button and user_query)
    )
    
    if should_execute:
        # 清除触发标记和待查询，防止重复执行
        st.session_state.auto_query_triggered = False
        st.session_state.auto_query = ''
        st.session_state.pending_query = ''
        # 注意：不重置 quick_query_select（会触发 StreamlitAPIException）
        # 重复选择同一快速查询项时，用户需先切到空项再选回——这是 Streamlit 框架限制
        
        with st.spinner("正在处理查询..."):
            result = pipeline.process(user_query)
        
        if result['sql']:
            # 显示查询结果
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("查询分析")
                st.markdown(f"**识别意图**: `{result['concept_id']}`")
                st.markdown(f"**时间模式**: `{result['time_mode']}`")
                st.markdown(f"**聚合模式**: `{result['agg_mode']}`")
                st.markdown(f"**数据表**: `{result['table']}`")
            
            with col2:
                st.subheader("生成的SQL")
                st.code(result['sql'], language='sql')
            
            st.markdown("---")
            
            # 模拟查询结果
            st.subheader("查询结果")
            
            # 根据concept_id返回模拟数据
            if result['concept_id'] and result['concept_id'].startswith('O-'):
                # 运营数据
                df = operation_data.head(20)
                st.dataframe(df)
            elif result['concept_id'] and result['concept_id'].startswith('S-'):
                # 安全数据
                df = safety_data.head(20)
                st.dataframe(df)
            elif result['concept_id'] and result['concept_id'].startswith('D-'):
                # 驾驶员数据
                df = driver_data.head(20)
                st.dataframe(df)
            else:
                st.info("未识别到明确的查询意图，请尝试更具体的描述")
        
        else:
            st.warning("无法识别查询意图，请尝试使用更具体的关键词")
            st.markdown("**支持的关键词包括**: 班次、出车率、准点率、客运量、ADAS、DMS、事故、告警等")


def page_operation_analysis(operation_data, simulator, chart_gen):
    """运营分析页面"""
    st.title("📈 运营分析")
    
    # 时间筛选
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        start_date = st.date_input("开始日期", operation_data['日期'].min())
    with col2:
        end_date = st.date_input("结束日期", operation_data['日期'].max())
    with col3:
        selected_line = st.selectbox("选择线路", ["全部"] + list(operation_data['线路'].unique()))
    
    # 筛选数据
    filtered_data = operation_data[
        (operation_data['日期'] >= start_date.strftime('%Y-%m-%d')) &
        (operation_data['日期'] <= end_date.strftime('%Y-%m-%d'))
    ]
    if selected_line != "全部":
        filtered_data = filtered_data[filtered_data['线路'] == selected_line]
    
    # 关键指标
    st.subheader("运营指标")
    metrics = {
        '平均出车率': f"{filtered_data['出车率'].mean():.1%}",
        '平均准点率': f"{filtered_data['准点率'].mean():.1%}",
        '总客运量': f"{filtered_data['客运量'].sum():,}",
        '平均配班率': f"{filtered_data['配班率'].mean():.1%}"
    }
    render_metrics_row(metrics)
    
    # 趋势图
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("客运量趋势")
        trend_data = filtered_data.groupby('日期')['客运量'].sum().reset_index()
        fig = chart_gen.create_line_chart(trend_data, '日期', '客运量', '客运量趋势')
        st.plotly_chart(fig)
    
    with col2:
        st.subheader("出车率趋势")
        trend_data = filtered_data.groupby('日期')['出车率'].mean().reset_index()
        fig = chart_gen.create_line_chart(trend_data, '日期', '出车率', '出车率趋势')
        st.plotly_chart(fig)
    
    # 线路排名
    st.subheader("线路排名")
    rank_metric = st.selectbox("排名依据", ['客运量', '出车率', '准点率'])
    
    line_ranking = filtered_data.groupby('线路').agg({
        rank_metric: 'mean' if rank_metric in ['出车率', '准点率', '配班率'] else 'sum'
    }).sort_values(by=rank_metric, ascending=False).head(20).reset_index()
    line_ranking.index = range(1, len(line_ranking) + 1)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        fig = chart_gen.create_bar_chart(line_ranking, '线路', rank_metric, f'{rank_metric}排名TOP20')
        st.plotly_chart(fig)
    
    with col2:
        st.dataframe(line_ranking)


def page_safety_monitoring(safety_data, chart_gen):
    """安全监控页面"""
    st.title("🚨 安全监控")
    
    # 安全指标
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_alarms = len(safety_data)
        st.metric("总告警数", total_alarms, delta=f"{np.random.randint(-20, 20)}")
    
    with col2:
        processed = len(safety_data[safety_data['处理状态'] == '已处理'])
        process_rate = processed / total_alarms * 100 if total_alarms > 0 else 0
        st.metric("处理率", f"{process_rate:.1f}%")
    
    with col3:
        critical_alarms = len(safety_data[safety_data['告警类型'].str.contains('疲劳|事故')])
        st.metric("严重告警", critical_alarms, delta_color="inverse")
    
    st.markdown("---")
    
    # 告警类型分布
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("告警类型分布")
        alarm_dist = safety_data['告警类型'].value_counts().reset_index()
        alarm_dist.columns = ['告警类型', '数量']
        fig = chart_gen.create_pie_chart(alarm_dist, '告警类型', '数量')
        st.plotly_chart(fig)
    
    with col2:
        st.subheader("每日告警趋势")
        daily_alarms = safety_data.groupby('日期').size().reset_index(name='告警数')
        fig = chart_gen.create_line_chart(daily_alarms, '日期', '告警数', '告警数趋势')
        st.plotly_chart(fig)
    
    # 告警明细
    st.subheader("告警明细")
    
    # 筛选
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_type = st.multiselect("告警类型", safety_data['告警类型'].unique())
    with col2:
        selected_status = st.multiselect("处理状态", safety_data['处理状态'].unique())
    with col3:
        selected_org = st.multiselect("分公司", safety_data['分公司'].unique())
    
    filtered_alarms = safety_data.copy()
    if selected_type:
        filtered_alarms = filtered_alarms[filtered_alarms['告警类型'].isin(selected_type)]
    if selected_status:
        filtered_alarms = filtered_alarms[filtered_alarms['处理状态'].isin(selected_status)]
    if selected_org:
        filtered_alarms = filtered_alarms[filtered_alarms['分公司'].isin(selected_org)]
    
    st.dataframe(filtered_alarms)


def page_driver_management(driver_data, chart_gen):
    """驾驶员管理页面"""
    st.title("👨‍✈️ 驾驶员管理")
    
    # 驾驶员指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_drivers = driver_data['工号'].nunique()
        st.metric("驾驶员总数", total_drivers)
    
    with col2:
        on_duty = len(driver_data[driver_data['在岗状态'] == '在岗'])
        on_duty_rate = on_duty / len(driver_data) * 100
        st.metric("在岗率", f"{on_duty_rate:.1f}%")
    
    with col3:
        avg_score = driver_data['安全评分'].mean()
        st.metric("平均安全评分", f"{avg_score:.0f}")
    
    with col4:
        violations = driver_data['违章次数'].sum()
        st.metric("总违章次数", violations, delta_color="inverse")
    
    st.markdown("---")
    
    # 安全评分分布
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("安全评分分布")
        score_dist = driver_data.groupby('工号')['安全评分'].mean().reset_index()
        fig = go.Figure(data=[go.Histogram(x=score_dist['安全评分'], nbinsx=20,
                                           marker_color='#1f77b4')])
        fig.update_layout(title='安全评分分布', template='plotly_white')
        st.plotly_chart(fig)
    
    with col2:
        st.subheader("驾驶时长分布")
        fig = go.Figure(data=[go.Histogram(x=driver_data['驾驶时长(小时)'], nbinsx=15,
                                           marker_color='#2ca02c')])
        fig.update_layout(title='驾驶时长分布', template='plotly_white')
        st.plotly_chart(fig)
    
    # 驾驶员排名
    st.subheader("驾驶员安全评分排名")
    
    driver_ranking = driver_data.groupby(['工号', '分公司']).agg({
        '安全评分': 'mean',
        '驾驶时长(小时)': 'mean',
        '违章次数': 'sum'
    }).reset_index().sort_values(by='安全评分', ascending=False).head(20)
    driver_ranking.index = range(1, len(driver_ranking) + 1)
    
    st.dataframe(driver_ranking)


def main():
    """主函数"""
    # 初始化
    pipeline, simulator, analyzer, chart_gen = init_components()
    
    # 渲染侧边栏（先渲染以获取 days 参数）
    page, days, selected_query = render_sidebar()
    
    # 生成数据（使用 sidebar slider 的时间范围）
    operation_data, safety_data, driver_data, passenger_data = generate_data(days=days)
    
    # 根据选择渲染页面
    if page == "📊 业务数据洞察":
        page_business_insight(operation_data, safety_data, driver_data, analyzer, chart_gen)
    
    elif page == "💬 智能问数":
        page_natural_query(
            pipeline, simulator, operation_data, safety_data, driver_data
        )
    
    elif page == "📈 运营分析":
        page_operation_analysis(operation_data, simulator, chart_gen)
    
    elif page == "🚨 安全监控":
        page_safety_monitoring(safety_data, chart_gen)
    
    elif page == "👨‍✈️ 驾驶员管理":
        page_driver_management(driver_data, chart_gen)
    
    # 页脚
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #888;'>
        <small>北京公交KPI看板 v1.0 | 基于本体驱动的智能数据分析平台</small>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
