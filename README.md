# 北京公交KPI看板 - 智能问数与业务数据洞察平台

基于本体驱动的公交经营指标和安全服务保障的智能问数与业务数据洞察平台Demo。

## 🎯 项目概述

本项目实现了一个完整的公交运营管理智能分析平台，包含以下核心功能：

- **智能问数**：基于本体驱动的自然语言查询系统，支持自然语言转SQL
- **业务数据洞察**：基于业务规则自动识别数据异常并生成洞察建议
- **运营分析**：全面的运营指标分析，包括出车率、准点率、客运量等
- **安全监控**：实时安全告警监控与分析
- **驾驶员管理**：驾驶员绩效与安全评分管理

## 🏗️ 系统架构

```
bjbus_kpi_platform/
├── app.py                      # Streamlit主应用
├── requirements.txt            # 依赖管理
├── README.md                   # 说明文档
├── core/                       # 核心模块
│   ├── nl2sql_pipeline_kpi.py  # NL2SQL六层流水线
│   ├── ontology_loader_kpi.py  # 本体加载器
│   └── insight_analyzer.py     # 业务洞察分析器
├── data/                       # 数据模块
│   ├── bjbus_kpi_ontology.ttl  # 业务本体定义(TTL格式)
│   └── data_simulator.py       # 数据模拟器
├── components/                 # 可视化组件
│   └── charts.py               # 图表生成器
└── utils/                      # 工具模块
```

## 🔧 技术栈

- **前端框架**：Streamlit 1.28+
- **数据处理**：Pandas 2.0+, NumPy 1.24+
- **可视化**：Plotly 5.18+
- **本体管理**：RDFlib 7.0+
- **查询引擎**：NL2SQL Pipeline（六层流水线）

## 📊 业务本体设计

### 本体结构

系统基于TTL格式的业务本体，涵盖6大业务域，50个BusinessConcept：

- **O域（运营核心）**：19个概念
  - 路单发车班次、出车率配班率、客运量刷卡量
  - 准点率、时组运力、区域客流、断面客流分析等

- **MD域（主数据）**：10个概念
  - 车辆主数据、人员主数据、线路主数据
  - 场站信息、能源站等

- **S域（安全告警）**：18个概念
  - 事故、ADAS告警、DMS告警、CAN告警
  - 进站违规、出站违规、山区超速等

- **D域（驾驶员管理）**：18个概念
  - 连续运营超时、累计运营超时、休息不足
  - 准驾不符、高血压告警、酒精检测等

- **SC域（稽查客诉）**：2个概念
  - 综合稽查、乘客投诉

- **P域（乘客客流）**：3个概念
  - 时段客流、老年乘客、实时老年客流

### 本体属性

每个BusinessConcept包含以下核心属性：

```turtle
:O-01 a :Report ;
    rdfs:label "路单发车班次"@zh ;
    :domain "运营核心" ;
    :primaryTable "PROD_DW.TA_BS_LD_DAY_MI" ;
    :triggerKeywords "路单,发车,班次,趟次,空放,运行公里,出车,行车" ;
    :keyMetrics """{"FCSJ":"发车时间","BCCS":"班次数"}""" ;
    :queryTemplate """{"o01_daily": "SELECT ..."}""" ;
    :businessRule "[O-01→o01_daily]: 按线路汇总当日班次和运行公里" .
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目（或复制项目文件）
cd bjbus_kpi_platform

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动应用

```bash
streamlit run app.py
```

应用将在浏览器中自动打开，默认地址：`http://localhost:8501`

### 3. 使用指南

#### 智能问数
- 在侧边栏选择"💬 智能问数"
- 输入自然语言问题，如："今日各线路班次统计"
- 系统自动识别意图、解析实体、生成SQL

#### 业务数据洞察
- 自动分析运营、安全、驾驶员数据
- 按优先级（严重/高/中）展示洞察
- 提供针对性改进建议

#### 运营分析
- 查看出车率、准点率、客运量趋势
- 线路排名对比
- 分公司绩效对比

#### 安全监控
- 告警类型分布分析
- 告警处理率监控
- 高风险线路识别

#### 驾驶员管理
- 驾驶员安全评分排名
- 驾驶时长分布
- 违章情况统计

## 🔍 NL2SQL流水线

系统采用六层流水线实现自然语言查询：

```
用户问题
    ↓
[IC] 意图分类 (Intent Classification)
    ↓
[TP] 时间解析 (Time Parsing)
    ↓
[EP] 实体抽取 (Entity Extraction)
    ↓
[AT] 聚合检测 (Aggregation Detection)
    ↓
[OWL] 本体查询 (Ontology Lookup)
    ↓
[SQL] SQL生成 (SQL Rendering)
    ↓
最终SQL
```

### 示例

**输入**：`"准点率排名前10的线路"`

**处理流程**：
1. IC → 识别为O-06（准点率晚点）
2. TP → time_mode=day, date=CURDATE()
3. EP → 无实体
4. AT → agg_mode=rank_desc, rank_n=10
5. OWL → 获取模板o06_ranking
6. SQL → 生成最终SQL

**输出**：
```sql
SELECT XLH, AVG(ZDL) AS ZDL 
FROM PROD_DW.TA_YYDD_DD_ZDFX_LINE_MI 
WHERE RQ=CURDATE() 
GROUP BY XLH 
ORDER BY ZDL ASC 
LIMIT 10
```

## 💡 业务洞察规则

系统内置业务规则引擎，自动识别数据异常：

```python
rules = {
    'O-02': {
        'name': '出车率配班率',
        'rules': [
            {
                'condition': '出车率 < 0.80',
                'insight': '出车率偏低，影响运力供给',
                'priority': 'high'
            }
        ]
    },
    'S-05': {
        'name': 'DMS告警',
        'rules': [
            {
                'condition': 'DMS疲劳驾驶 > 10',
                'insight': '疲劳驾驶风险高，需安排休息',
                'priority': 'critical'
            }
        ]
    }
}
```

## 📈 数据模拟

项目包含完整的数据模拟器，可生成测试数据：

```python
from data.data_simulator import BJBusDataSimulator

simulator = BJBusDataSimulator()
operation_data = simulator.generate_operation_data(days=30)
safety_data = simulator.generate_safety_data(days=30)
driver_data = simulator.generate_driver_data(days=30)
```

## 🎨 可视化组件

支持多种图表类型：

- 折线图（趋势分析）
- 柱状图（排名对比）
- 饼图（分布占比）
- 热力图（相关性分析）
- 仪表盘（KPI展示）
- 雷达图（多维评估）
- 漏斗图（流程分析）
- 树状图/旭日图（层级结构）

## 📝 扩展开发

### 添加新的业务概念

1. 在`bjbus_kpi_ontology.ttl`中定义新概念
2. 添加触发关键词、SQL模板、业务规则
3. 更新`ontology_loader_kpi.py`中的优先路由规则
4. 在数据模拟器中添加相应数据生成逻辑

### 自定义洞察规则

在`insight_analyzer.py`的`_load_business_rules()`方法中添加新规则：

```python
'NEW-01': {
    'name': '新业务概念',
    'rules': [
        {
            'condition': '指标 > 阈值',
            'insight': '洞察描述',
            'priority': 'high'
        }
    ]
}
```

## 📚 参考资料

- [Streamlit官方文档](https://docs.streamlit.io/)
- [Plotly官方文档](https://plotly.com/python/)
- [RDFlib文档](https://rdflib.readthedocs.io/)
- [OWL本体规范](https://www.w3.org/TR/owl2-overview/)

## 📄 许可证

本项目仅供学习和演示使用。

## 👥 联系方式

如有问题或建议，欢迎反馈。

---

**版本**：v1.0  
**更新时间**：2026-06-10
