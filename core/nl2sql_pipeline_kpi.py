"""
nl2sql_pipeline_kpi.py
北京公交KPI看板 NL2SQL 六层流水线
IC→TP→EP→AT→OWL→SQL

依赖: rdflib (pip install rdflib)
"""
from __future__ import annotations
import re, sys, json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    from .ontology_loader_kpi import BJBusKPIOntology
except ImportError:
    from ontology_loader_kpi import BJBusKPIOntology


@dataclass
class ParsedQuery:
    question:   str           = ""
    concept_id: Optional[str] = None
    time_mode:  str           = "day"
    date:       Optional[str] = None
    date_start: Optional[str] = None
    date_end:   Optional[str] = None
    n_min:      int           = 30
    line_id:    Optional[str] = None    # 线路编号，如 "101"
    org_name:   Optional[str] = None    # 分公司名称
    driver_gh:  Optional[str] = None    # 驾驶员工号
    vehicle_id: Optional[str] = None    # 车辆自编号
    agg_mode:   str           = "none"  # rank_desc/rank_asc/sum/count/none
    rank_n:     int           = 10


class TimeParser:
    _DATE_PAT  = re.compile(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})')
    _NEAR_PAT  = re.compile(r'近(\d+)分钟|最近(\d+)分钟|last\s+(\d+)\s*min', re.I)

    def parse(self, q: ParsedQuery) -> None:
        text = q.question
        m = self._NEAR_PAT.search(text)
        if m:
            q.time_mode = "near_n_min"
            q.n_min = int(next(x for x in m.groups() if x))
            return
        if any(kw in text for kw in ["实时", "当前", "现在"]):
            q.time_mode = "realtime"
            return
        dates = self._DATE_PAT.findall(text)
        if len(dates) >= 2:
            q.time_mode = "range"
            q.date_start = dates[0].replace("/", "-")
            q.date_end   = dates[1].replace("/", "-")
            return
        q.time_mode = "day"
        if dates:
            q.date = dates[0].replace("/", "-")
        elif "昨天" in text or "昨日" in text:
            q.date = "DATE_SUB(CURDATE(), INTERVAL 1 DAY)"
        else:
            q.date = "CURDATE()"


class EntityExtractor:
    _LINE_PAT   = re.compile(r'(\d{1,4})[路线]')
    _GH_PAT     = re.compile(r'工号[：:＝=\s]*(\w+)')
    _VEHICLE_PAT= re.compile(r'[京津沪][A-Z]\d{5}|\b[A-Z]{2}\d{4,6}\b')

    _ORG_MAP = {
        "第一客运": "第一客运分公司", "一客": "第一客运分公司",
        "第二客运": "第二客运分公司", "二客": "第二客运分公司",
        "第三客运": "第三客运分公司", "三客": "第三客运分公司",
        "第四客运": "第四客运分公司", "四客": "第四客运分公司",
        "第五客运": "第五客运分公司", "五客": "第五客运分公司",
        "郊区": "郊区客运分公司", "特种": "特种车辆分公司",
    }

    def extract(self, q: ParsedQuery) -> None:
        text = q.question
        m = self._LINE_PAT.search(text)
        if m:
            q.line_id = m.group(1)
        m = self._GH_PAT.search(text)
        if m:
            q.driver_gh = m.group(1)
        m = self._VEHICLE_PAT.search(text)
        if m:
            q.vehicle_id = m.group()
        for label, full in self._ORG_MAP.items():
            if label in text:
                q.org_name = full
                break


class AggregationDetector:
    def detect(self, q: ParsedQuery) -> None:
        text = q.question
        if any(kw in text for kw in ["最多", "最高", "第一", "TOP", "排名前", "排行"]):
            q.agg_mode = "rank_desc"
        elif any(kw in text for kw in ["最少", "最低", "垫底", "最差"]):
            q.agg_mode = "rank_asc"
        elif any(kw in text for kw in ["总量", "合计", "总计", "累计"]):
            q.agg_mode = "sum"
        elif any(kw in text for kw in ["多少", "数量", "几辆", "几人", "计数"]):
            q.agg_mode = "count"
        m = re.search(r'前(\d+)', text)
        if m:
            q.rank_n = int(m.group(1))


class SQLRenderer:
    def __init__(self, ontology: BJBusKPIOntology):
        self._ont = ontology

    def render(self, q: ParsedQuery) -> str:
        if not q.concept_id:
            return ""
        key = self._pick_template(q)
        templates = self._ont.list_templates(q.concept_id)
        if not templates:
            return f"-- No templates for {q.concept_id}"
        if key not in templates:
            key = next(iter(templates))  # fallback to first template
        return self._fill(templates[key], q)

    def _pick_template(self, q: ParsedQuery) -> str:
        cid = q.concept_id.lower().replace("-", "")
        if q.agg_mode in ("rank_desc", "rank_asc"):
            # prefer ranking template
            templates = self._ont.list_templates(q.concept_id)
            for k in templates:
                if "ranking" in k or "rank" in k:
                    return k
        if q.time_mode == "near_n_min":
            templates = self._ont.list_templates(q.concept_id)
            for k in templates:
                if "realtime" in k or "near" in k:
                    return k
        if q.time_mode == "range":
            templates = self._ont.list_templates(q.concept_id)
            for k in templates:
                if "range" in k:
                    return k
        if q.time_mode == "day" and q.date and "SUB" in str(q.date):
            templates = self._ont.list_templates(q.concept_id)
            for k in templates:
                if "yesterday" in k:
                    return k
        # default: first template
        templates = self._ont.list_templates(q.concept_id)
        return next(iter(templates), "")

    def _fill(self, sql: str, q: ParsedQuery) -> str:
        reps = {
            "{date}":       q.date or "CURDATE()",
            "{date_start}": q.date_start or "",
            "{date_end}":   q.date_end or "",
            "{n_min}":      str(q.n_min),
            "{zbh}":        q.vehicle_id or "",
            "{org}":        q.org_name or "",
            "{line}":       q.line_id or "",
            "{gh}":         q.driver_gh or "",
            "{rank_n}":     str(q.rank_n),
            "{type}":       "",
            "{name}":       "",
            "{station}":    "",
        }
        for k, v in reps.items():
            sql = sql.replace(k, v)
        return sql


class NL2SQLPipelineKPI:
    """六层 NL2SQL 流水线：IC→TP→EP→AT→OWL→SQL"""

    def __init__(self, ttl_path: str | Path):
        self._ont = BJBusKPIOntology(ttl_path)
        self._tp  = TimeParser()
        self._ep  = EntityExtractor()
        self._at  = AggregationDetector()
        self._sql = SQLRenderer(self._ont)

    def process(self, question: str) -> dict:
        q = ParsedQuery(question=question)
        # IC
        q.concept_id = self._ont.route_intent(question)
        if not q.concept_id:
            return {"sql": None, "concept_id": None, "reasoning_trace": "no concept matched"}
        # TP
        self._tp.parse(q)
        # EP
        self._ep.extract(q)
        # AT
        self._at.detect(q)
        # OWL
        table = self._ont.get_table(q.concept_id)
        # SQL
        sql = self._sql.render(q)
        return {
            "sql":            sql,
            "concept_id":     q.concept_id,
            "table":          table,
            "time_mode":      q.time_mode,
            "agg_mode":       q.agg_mode,
            "reasoning_trace": repr(q),
        }


if __name__ == "__main__":
    ttl = Path(__file__).parent / "bjbus_kpi_ontology.ttl"
    pipeline = NL2SQLPipelineKPI(ttl)

    tests = [
        # (问题, 期望concept_id, SQL片段或None)
        ("今日各线路班次统计",              "O-01", "TA_BS_LD_DAY_MI"),
        ("当前出车率和配班率",              "O-02", "TA_YYDD_DD_YLFX_LINE_DAY_MI"),
        ("101路今日客运量",                 "O-03", "TA_YYDD_DD_KLFX_LINE_DAY_MI"),
        ("近14日客流趋势",                  "O-04", "TA_CA_CLEAN_LINE_DI"),
        ("准点率排名前10的线路",            "O-06", "TA_YYDD_DD_ZDFX_LINE_MI"),
        ("五峰时段区域客流分析",            "O-08", "TA_YYDD_KLFX_QY_WF_SZ_MI"),
        ("断面客流满载率",                  "O-12", "TA_YYDD_DD_DMFX_QY_WF_MI"),
        ("备车率最低的分公司",              "O-16", "TA_YYDD_DD_BCLFX_FGS_GJY_DI"),
        ("当前车辆状态实时",                "O-15", "TA_SJC_CLZT_BUS_LATEST_MI_VIEW"),
        ("近6月运营质量趋势",               "O-14", "TA_YYDD_DD_XLYYZL_QY_DAY_DI"),
        ("车辆燃料类型分布",                "MD-01", "TD_MD_HX_CL_DA"),
        ("查询工号10001的驾驶员信息",       "MD-02", "TD_MD_HX_RY_NEW_DA"),
        ("在营车辆实时数量",                "MD-10", "TA_BUS_MTONLINE_MI"),
        ("加氢站位置",                      "MD-06", "TA_MD_NYZ_DA"),
        ("今日交通事故统计",                "S-01", "TI_ANF_SSSG_DAY_MI"),
        ("ADAS告警中车道偏离多少次",        "S-04", "TF_BT_ADASALARM_EXT_MI"),
        ("DMS疲劳驾驶告警排名前5",          "S-05", "TF_AF_JSYYCXW_DAY_MI"),
        ("近30天ADAS历史汇总",              "S-14", "TA_BT_ADASALARM_LINE_SUM_DI"),
        ("进站违规次数统计",                "S-07", "TF_ZHAQ_JZWG_MX_MI"),
        ("山区超速告警",                    "S-13", "TF_ZHAQ_SQCS_MX_MI"),
        ("鸣笛违规记录",                    "S-12", "TF_ZHAQ_JSGCMDWG_MX_MI"),
        ("车辆故障统计",                    "S-18", "TA_BUSFAULT_ANALYSE_MI"),
        ("酒精检测不合格驾驶员",            "D-15", "TA_CZFZSB_RYKQJL_DAY_MI"),
        ("连续运营超4小时告警",             "D-02", "TF_AQTS_LXYYALARM_MI"),
        ("体检超期驾驶员",                  "D-18", "TF_PS_RL_TJRYXX_DA"),
        ("季度评价得分最高的驾驶员",        "D-16", "TA_AQJH_PJQK_QUARTER_DI"),
        ("综合稽查问题类型分布",            "SC-01", "TF_PS_ZHJC_JCWTGDCLJL_DA"),
        ("近30天乘客投诉统计",              "SC-02", "TA_PS_SMYJ_GDMX_DA"),
        ("老年乘客比例最高线路",            "P-02", "TA_YYDD_ONBOARD_BUS_MI"),
        ("时段客流峰值",                    "P-01", "TA_YYDD_DD_KLFX_TC_DAY_MI"),
    ]

    passed = 0
    for q_text, exp_cid, exp_sql_frag in tests:
        result = pipeline.process(q_text)
        ok = True
        if result["concept_id"] != exp_cid:
            print(f"  [FAIL] '{q_text}' concept={result['concept_id']} (expected {exp_cid})")
            ok = False
        elif exp_sql_frag and (result["sql"] is None or exp_sql_frag not in result["sql"]):
            print(f"  [FAIL] '{q_text}' sql missing '{exp_sql_frag}'\n    got: {result['sql']}")
            ok = False
        passed += ok

    status = "✓" if passed == len(tests) else "✗"
    print(f"{status} {passed}/{len(tests)} pipeline self-tests passed")
    sys.exit(0 if passed == len(tests) else 1)
