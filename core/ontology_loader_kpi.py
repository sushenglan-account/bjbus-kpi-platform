"""
ontology_loader_kpi.py
北京公交KPI看板本体加载器
覆盖 50 个 BusinessConcept / 6 个业务域（O/MD/S/D/SC/P）

依赖: rdflib (pip install rdflib)
"""
from __future__ import annotations
import re, sys, json
from pathlib import Path
from typing import Optional

try:
    from rdflib import Graph, Namespace, URIRef, Literal
    from rdflib.namespace import OWL, RDFS, RDF
except ImportError:
    print("ERROR: rdflib not installed. Run: pip install rdflib", file=sys.stderr)
    sys.exit(1)

NS = Namespace("http://transit.beijing.cn/bjbus-kpi#")

# ─────────────────────────────────────────────────────────────
# 优先路由规则（AND 逻辑：列表内所有词必须同时出现才命中）
# 按优先级从高到低排列
# ─────────────────────────────────────────────────────────────
_PRIORITY_RULES: list[tuple[list[str], str]] = [
    # S 域 - 安全告警（多词优先）
    (["ADAS", "历史"],          "S-14"),
    (["DMS", "历史"],           "S-15"),
    (["CAN", "历史"],           "S-16"),
    (["ADAS"],                  "S-04"),
    (["DMS"],                   "S-05"),
    (["CAN", "告警"],           "S-06"),
    (["一键", "告警"],          "S-02"),
    (["进站", "不打灯"],        "S-10"),
    (["出站", "不打灯"],        "S-11"),
    (["进站", "违规"],          "S-07"),
    (["出站", "违规"],          "S-08"),
    (["山区", "超速"],          "S-13"),
    (["倒车", "超速"],          "S-09"),
    (["鸣笛"],                  "S-12"),
    (["滞站"],                  "S-03"),
    (["交通违法"],              "S-17"),
    (["违章"],                  "S-17"),
    (["车辆故障"],              "S-18"),
    (["故障", "维保"],          "S-18"),
    (["事故"],                  "S-01"),
    # D 域 - 驾驶员管理
    (["连续运营", "超时"],      "D-02"),
    (["累计运营", "超时"],      "D-03"),
    (["连续", "7天"],           "D-04"),
    (["连续驾驶", "超"],        "D-04"),
    (["休息不足"],              "D-05"),
    (["休息时间"],              "D-05"),
    (["准驾不符"],              "D-06"),
    (["驾驶资质"],              "D-06"),
    (["硬翻班"],                "D-07"),
    (["临时调度"],              "D-08"),
    (["换线"],                  "D-09"),
    (["班型更换"],              "D-10"),
    (["没开本班"],              "D-11"),
    (["没开本车"],              "D-12"),
    (["高血压"],                "D-13"),
    (["血压"],                  "D-13"),
    (["重大阳性"],              "D-14"),
    (["酒测"],                  "D-15"),
    (["酒精"],                  "D-15"),
    (["驾驶员", "画像"],        "D-16"),
    (["季度评价"],              "D-16"),
    (["模范驾驶员"],            "D-16"),
    (["体检"],                  "D-18"),
    (["工号"],                  "MD-02"),
    (["员工信息"],              "MD-02"),
    (["驾龄"],                  "D-17"),
    (["驾驶员", "信息"],        "D-17"),
    (["重点驾驶员"],            "D-01"),
    (["驾驶员", "在岗"],        "D-01"),
    # O 域 - 运营核心
    (["历史客运量"],            "O-04"),
    (["近14日"],                "O-04"),
    (["客流趋势"],              "O-04"),
    (["计划车次"],              "O-05"),
    (["计划配班率"],            "O-05"),
    (["兑现率"],                "O-05"),
    (["时组运力"],              "O-07"),
    (["分时段", "出车"],        "O-07"),
    (["高峰时段", "运力"],      "O-07"),
    (["区域客流"],              "O-08"),
    (["五峰", "客流"],          "O-08"),
    (["站点历史客流"],          "O-18"),
    (["站点历史"],              "O-18"),
    (["站点", "客流"],          "O-09"),
    (["断面客流"],              "O-12"),
    (["断面分析"],              "O-12"),
    (["区域运力"],              "O-10"),
    (["五峰", "运力"],          "O-10"),
    (["区域里程"],              "O-11"),
    (["五峰", "里程"],          "O-11"),
    (["五峰", "间隔"],          "O-13"),
    (["区域", "间隔"],          "O-13"),
    (["运营质量"],              "O-14"),
    (["近6月"],                 "O-14"),
    (["车辆状态"],              "O-15"),
    (["当前", "车辆"],          "O-15"),
    (["备车率"],                "O-16"),
    (["备车"],                  "O-16"),
    (["满座率"],                "O-17"),
    (["座位占用"],              "O-17"),
    (["站点历史客流"],          "O-18"),
    (["复工"],                  "O-19"),
    (["出车率"],                "O-02"),
    (["配班率"],                "O-02"),
    (["运力分析"],              "O-02"),
    (["客运量"],                "O-03"),
    (["百公里客运量"],          "O-03"),
    (["准点率"],                "O-06"),
    (["晚点"],                  "O-06"),
    (["发车间隔"],              "O-06"),
    (["路单"],                  "O-01"),
    (["班次"],                  "O-01"),
    (["出车"],                  "O-01"),
    # MD 域 - 主数据
    (["运营在册"],              "MD-03"),
    (["在册车辆"],              "MD-03"),
    (["事故看板", "驾驶员"],    "MD-04"),
    (["能源站"],                "MD-06"),
    (["加气站"],                "MD-06"),
    (["加氢站"],                "MD-06"),
    (["线路主数据"],            "MD-07"),
    (["线路编号"],              "MD-07"),
    (["人员分布"],              "MD-08"),
    (["在册人员"],              "MD-09"),
    (["线路人员"],              "MD-09"),
    (["在线车辆"],              "MD-10"),
    (["在营车辆"],              "MD-10"),
    (["车辆主数据"],            "MD-01"),
    (["车龄"],                  "MD-01"),
    (["燃料类型"],              "MD-01"),
    (["人员主数据"],            "MD-02"),
    (["工号"],                  "MD-02"),
    (["场站"],                  "MD-05"),
    # SC 域 - 稽查客诉
    (["稽查"],                  "SC-01"),
    (["综合稽查"],              "SC-01"),
    (["客诉"],                  "SC-02"),
    (["投诉"],                  "SC-02"),
    (["市民意见"],              "SC-02"),
    # P 域 - 乘客客流
    (["当前老年"],              "P-03"),
    (["实时老年"],              "P-03"),
    (["老年客流"],              "P-02"),
    (["老年乘客"],              "P-02"),
    (["老年人"],                "P-02"),
    (["时段客流"],              "P-01"),
    (["趟次客流"],              "P-01"),
]


class BJBusKPIOntology:
    """北京公交KPI本体加载器：从TTL文件加载BusinessConcept，提供意图路由和模板查询。"""

    def __init__(self, ttl_path: str | Path):
        self._g = Graph()
        self._g.parse(str(ttl_path), format="turtle")
        self._ns = NS

    def route_intent(self, question: str) -> Optional[str]:
        """意图分类：返回 concept_id，未命中返回 None。先走优先规则，再走TTL兜底。"""
        q_lower = question.lower()
        for keywords, cid in _PRIORITY_RULES:
            if all(kw.lower() in q_lower for kw in keywords):
                return cid
        for concept in self._iter_concepts():
            cid = self._local_name(concept)
            kw_str = self._prop(concept, "triggerKeywords")
            if kw_str:
                for kw in [k.strip() for k in kw_str.split(",")]:
                    if kw and kw.lower() in q_lower:
                        return cid
        return None

    def get_table(self, concept_id: str) -> Optional[str]:
        return self._prop(self._ns[concept_id], "primaryTable")

    def list_templates(self, concept_id: str) -> dict:
        raw = self._prop(self._ns[concept_id], "queryTemplate")
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def get_business_rules(self, concept_id: str) -> str:
        return self._prop(self._ns[concept_id], "businessRule") or ""

    def validate_governance(self) -> list[str]:
        """验证每个businessRule声明的templateKey确实存在于queryTemplate。"""
        errors = []
        for concept in self._iter_concepts():
            cid = self._local_name(concept)
            rule = self._prop(concept, "businessRule") or ""
            templates = self.list_templates(cid)
            for m in re.finditer(r'\[.+?→(.+?)\]', rule):
                key = m.group(1).strip()
                if key not in templates:
                    errors.append(f"{cid}: businessRule declares templateKey '{key}' not in queryTemplate")
        return errors

    def list_concepts(self) -> list[str]:
        return [self._local_name(c) for c in self._iter_concepts()]

    def _iter_concepts(self):
        bc = self._ns["BusinessConcept"]
        seen = set()
        for s in self._g.subjects(RDF.type, None):
            if s in seen:
                continue
            for cls in self._g.objects(s, RDF.type):
                superclasses = list(self._g.objects(cls, RDFS.subClassOf))
                if bc in superclasses or cls == bc:
                    seen.add(s)
                    yield s
                    break

    def _prop(self, subject, prop_name: str) -> Optional[str]:
        val = self._g.value(subject, self._ns[prop_name])
        return str(val).strip() if val else None

    def _local_name(self, uri) -> str:
        return str(uri).split("#")[-1]


if __name__ == "__main__":
    ttl = Path(__file__).parent / "bjbus_kpi_ontology.ttl"
    ont = BJBusKPIOntology(ttl)

    concepts = ont.list_concepts()
    print(f"Loaded {len(concepts)} concepts: {sorted(concepts)[:5]}...")

    errs = ont.validate_governance()
    if errs:
        for e in errs:
            print(f"  [GOVERNANCE ERROR] {e}")
    else:
        print("  [OK] Governance validation passed")

    tests = [
        # O 域
        ("今日各线路班次和运行公里", "O-01"),
        ("当前出车率和配班率", "O-02"),
        ("今日客运量和刷卡量", "O-03"),
        ("近14日客流趋势", "O-04"),
        ("今日计划车次完成情况", "O-05"),
        ("各线路准点率排名", "O-06"),
        ("高峰时段运力分布", "O-07"),
        ("五峰时段区域客流", "O-08"),
        ("站点客流排名", "O-09"),
        ("区域运力投放分析", "O-10"),
        ("区域里程统计", "O-11"),
        ("断面客流分析", "O-12"),
        ("五峰发车间隔", "O-13"),
        ("近6月运营质量趋势", "O-14"),
        ("当前车辆状态", "O-15"),
        ("各分公司备车率", "O-16"),
        ("高峰时段满座率", "O-17"),
        ("站点历史客流", "O-18"),
        ("复工运营总数", "O-19"),
        # MD 域
        ("新能源车燃料类型分布", "MD-01"),
        ("查询工号12345的员工信息", "MD-02"),
        ("运营在册车辆总数", "MD-03"),
        ("场站信息查询", "MD-05"),
        ("加气站和加氢站分布", "MD-06"),
        # S 域
        ("今日事故情况", "S-01"),
        ("一键告警次数", "S-02"),
        ("滞站记录", "S-03"),
        ("ADAS告警类型分布", "S-04"),
        ("DMS疲劳驾驶告警", "S-05"),
        ("CAN告警违规", "S-06"),
        ("进站违规次数", "S-07"),
        ("出站不打灯记录", "S-11"),
        ("山区超速情况", "S-13"),
        ("ADAS历史汇总", "S-14"),
        ("交通违法记录", "S-17"),
        ("车辆故障维保记录", "S-18"),
        # D 域
        ("连续运营超4小时告警", "D-02"),
        ("酒精检测不合格驾驶员", "D-15"),
        ("驾驶员画像季度评价", "D-16"),
        ("体检记录查询", "D-18"),
        ("重点驾驶员在岗情况", "D-01"),
        # SC 域
        ("综合稽查问题统计", "SC-01"),
        ("乘客投诉记录", "SC-02"),
        # P 域
        ("时段客流分析", "P-01"),
        ("老年乘客比例", "P-02"),
        ("当前老年乘客数量", "P-03"),
    ]

    passed = 0
    failed_cases = []
    for q, expected in tests:
        got = ont.route_intent(q)
        ok = (got == expected)
        if not ok:
            failed_cases.append(f"  [FAIL] '{q}' → {got} (expected {expected})")
        passed += ok

    for f in failed_cases:
        print(f)

    status = "✓" if passed == len(tests) else "✗"
    print(f"{status} {passed}/{len(tests)} routing tests passed")
    sys.exit(0 if passed == len(tests) else 1)
