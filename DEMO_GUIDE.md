# 项目演示指南

## 快速启动

### 1. 环境准备

```bash
# 进入项目目录
cd bjbus_kpi_platform

# 安装依赖
pip3 install -r requirements.txt
```

### 2. 启动应用

```bash
# 方式1: 使用启动脚本
chmod +x start.sh
./start.sh

# 方式2: 直接运行
streamlit run app.py
```

应用将在浏览器中自动打开：http://localhost:8501

## 功能演示

### 1. 智能问数演示

**场景1：基础查询**
- 输入："今日各线路班次统计"
- 系统自动识别意图O-01，生成SQL查询路单数据

**场景2：排名查询**
- 输入："准点率排名前10的线路"
- 系统识别聚合模式rank_desc，生成排序查询

**场景3：安全监控**
- 输入："DMS疲劳驾驶告警排名前5"
- 系统识别S-05概念，查询驾驶员行为告警

**场景4：时间范围**
- 输入："近14日客流趋势"
- 系统识别时间模式range，查询历史数据

### 2. 业务数据洞察演示

**自动洞察生成**
1. 系统自动分析运营、安全、驾驶员数据
2. 识别数据异常和业务规则违规
3. 按优先级分类展示（严重/高/中）
4. 提供针对性改进建议

**洞察示例**
- 🔴 严重：发现5名驾驶员单日驾驶时长超过8小时
- 🟠 高优：平均出车率为87.5%，低于90%的目标值
- 🔵 中等：客流最高的5条线路占总客流的10%

### 3. 运营分析演示

**指标分析**
- 查看出车率、准点率、客运量趋势
- 线路排名对比
- 分公司绩效对比

**操作步骤**
1. 在侧边栏选择"📈 运营分析"
2. 设置时间范围
3. 选择特定线路或查看全部
4. 查看趋势图和排名表

### 4. 安全监控演示

**告警分析**
- 告警类型分布
- 每日告警趋势
- 处理率监控
- 高风险线路识别

**操作步骤**
1. 在侧边栏选择"🚨 安全监控"
2. 查看总告警数和处理率
3. 分析告警类型分布
4. 筛选特定类型、状态或分公司

### 5. 驾驶员管理演示

**绩效管理**
- 驾驶员安全评分排名
- 驾驶时长分布
- 违章情况统计

**操作步骤**
1. 在侧边栏选择"👨‍✈️ 驾驶员管理"
2. 查看在岗率和平均安全评分
3. 分析评分分布和时长分布
4. 查看安全评分排名

## 测试验证

### 运行系统测试

```bash
python3 test_system.py
```

**测试覆盖**
- ✓ 本体加载器（70个概念）
- ✓ NL2SQL流水线（六层处理）
- ✓ 数据模拟器（运营/安全/驾驶员数据）
- ✓ 洞察分析器（自动洞察生成）
- ✓ 图表生成器（多种可视化）

### 单元测试示例

```python
# 测试本体加载
from core.ontology_loader_kpi import BJBusKPIOntology

ont = BJBusKPIOntology('data/bjbus_kpi_ontology.ttl')
concept_id = ont.route_intent("今日班次统计")
print(f"识别概念: {concept_id}")  # O-01

# 测试NL2SQL流水线
from core.nl2sql_pipeline_kpi import NL2SQLPipelineKPI

pipeline = NL2SQLPipelineKPI('data/bjbus_kpi_ontology.ttl')
result = pipeline.process("准点率排名前10")
print(f"生成的SQL: {result['sql']}")

# 测试数据模拟
from data.data_simulator import BJBusDataSimulator

simulator = BJBusDataSimulator()
data = simulator.generate_operation_data(days=30)
print(f"生成数据: {len(data)}条")

# 测试洞察分析
from core.insight_analyzer import InsightAnalyzer

analyzer = InsightAnalyzer()
insights = analyzer.analyze_operation_insights(data)
print(f"发现洞察: {len(insights)}条")
```

## 数据说明

### 模拟数据生成

系统使用数据模拟器生成测试数据：

**运营数据**
- 线路：100条
- 时间范围：可配置（默认30天）
- 指标：班次数、运行公里、出车率、客运量、准点率等

**安全数据**
- 告警类型：ADAS、DMS、CAN、进站违规、山区超速等
- 时间范围：可配置
- 状态：已处理、处理中、未处理

**驾驶员数据**
- 驾驶员：200名
- 指标：在岗状态、驾驶时长、运营趟次、安全评分等

### 本体配置

**业务概念**
- O域（运营核心）：19个概念
- MD域（主数据）：10个概念
- S域（安全告警）：18个概念
- D域（驾驶员管理）：18个概念
- SC域（稽查客诉）：2个概念
- P域（乘客客流）：3个概念

**触发关键词**
每个概念配置多个触发关键词，支持模糊匹配

**SQL模板**
每个概念配置多个查询模板，支持参数化

## 扩展开发

### 添加新业务概念

1. 编辑 `data/bjbus_kpi_ontology.ttl`
2. 添加新的BusinessConcept定义
3. 配置触发关键词和SQL模板
4. 更新优先路由规则

### 自定义洞察规则

编辑 `core/insight_analyzer.py`：

```python
rules = {
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
}
```

## 性能优化

- 使用Streamlit缓存机制 (@st.cache_data)
- 数据模拟器使用随机种子保证可重现
- 图表使用Plotly实现交互式可视化
- 本体加载使用RDFlib高效解析

## 常见问题

**Q: 如何修改数据时间范围？**
A: 在侧边栏调整"数据时间范围"滑块

**Q: 如何添加新的查询类型？**
A: 在本体TTL文件中添加新概念和SQL模板

**Q: 如何自定义洞察规则？**
A: 编辑insight_analyzer.py中的_load_business_rules方法

**Q: 如何导出分析结果？**
A: 使用Streamlit的下载功能，或导出为CSV/Excel

## 技术支持

- 项目文档：README.md
- 本体规范：data/bjbus_kpi_ontology.ttl
- API文档：参考各模块代码注释

---

**版本**：v1.0  
**更新**：2026-06-10
