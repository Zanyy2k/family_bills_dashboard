import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="家庭水电费账单看板",
    page_icon="🏠",
    layout="wide",
)

DATA_PATH = Path(__file__).parent / "dataset" / "sp_bills.csv"
ELEC_DATA_PATH = Path(__file__).parent / "dataset" / "elec_bills.csv"

HIGHLIGHT = "#FF4444"
ESTIMATED_COLOR = "#FFAA88"
WATER_COLOR = "#4488FF"
GAS_COLOR = "#FF8C00"
REFUSE_COLOR = "#66BB6A"
GST_COLOR = "#BDBDBD"
USAVE_COLOR = "#F44336"
ELEC_COLOR = "#9C27B0"
ELEC_OLD_COLOR = "#CE93D8"
ELEC_NEW_COLOR = "#7B1FA2"

MONTH_MAP = {
    1: "1月", 2: "2月", 3: "3月", 4: "4月",
    5: "5月", 6: "6月", 7: "7月", 8: "8月",
    9: "9月", 10: "10月", 11: "11月", 12: "12月",
}


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df["month"] = pd.to_datetime(df["month"])
    df["period_start"] = pd.to_datetime(df["period_start"])
    df["period_end"] = pd.to_datetime(df["period_end"])
    df["usave_deduction"] = df["usave_deduction"].fillna(0)
    df["others_cost"] = df["others_cost"].fillna(0)
    df["water_meter"] = pd.to_numeric(df["water_meter"], errors="coerce")
    df["gas_meter"] = pd.to_numeric(df["gas_meter"], errors="coerce")
    df["month_cn"] = df["month"].apply(
        lambda x: f"{x.year}年{MONTH_MAP[x.month]}"
    )
    return df


@st.cache_data
def load_elec_data():
    df = pd.read_csv(ELEC_DATA_PATH)
    df["month"] = pd.to_datetime(df["month"])
    df["period_start"] = pd.to_datetime(df["period_start"])
    df["period_end"] = pd.to_datetime(df["period_end"])
    df["month_cn"] = df["month"].apply(
        lambda x: f"{x.year}年{MONTH_MAP[x.month]}"
    )
    return df


df = load_data()
edf = load_elec_data()

# ── Header ──────────────────────────────────────────────────────────────
st.title("🏠 家庭水电费账单看板")
st.caption("新加坡家庭 · 水费 + 天然气（SP Services）· 电费（Geneco）")

# ── KPI row ─────────────────────────────────────────────────────────────
latest = df.iloc[-1]
prev = df.iloc[-2]
avg_total = df["total_current_charges"].mean()
max_row = df.loc[df["total_current_charges"].idxmax()]
total_usave = df["usave_deduction"].sum()
elec_latest = edf.iloc[-1]
elec_avg = edf["elec_kwh"].mean()

elec_avg_cost = edf["current_charges"].mean()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric(
    f"💧🔥 水气最新（{latest['month_cn']}）",
    f"${latest['total_current_charges']:.2f}",
    delta=f"vs 上月 ${latest['total_current_charges'] - prev['total_current_charges']:+.2f}",
    delta_color="inverse",
)
k2.metric("💧🔥 水气月均", f"${avg_total:.2f}", delta="15个月均值，含垃圾费和GST")
k3.metric(
    f"⚡ 电费最新（{elec_latest['month_cn']}）",
    f"${elec_latest['current_charges']:.2f}",
    delta=f"实付 ${elec_latest['total_payable']:.2f}（扣U-Save）",
    delta_color="off",
)
k4.metric("⚡ 电费月均", f"${elec_avg_cost:.2f}", delta="17个月均值，含GST")
k5.metric("🎁 U-Save 补贴", f"${total_usave:.0f}", delta="水气账户，每季 $150")

st.divider()

# ── Tabs ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["💧 用水分析", "🔥 燃气分析", "⚡ 电费分析", "💰 账单构成", "📋 完整明细", "📊 综合分析"]
)

# ───────────────────────────── TAB 1: WATER ─────────────────────────────
with tab1:
    st.subheader("每月用水量（吨，1 吨 = 1 立方米 = 1,000 升）")

    bar_colors = [
        HIGHLIGHT if r["bill_label"] == "Aug 2026"
        else (ESTIMATED_COLOR if r["is_estimated"] else WATER_COLOR)
        for _, r in df.iterrows()
    ]

    actual_df = df[~df["is_estimated"]]
    actual_avg = actual_df["water_cum"].mean()

    fig_w = go.Figure()
    fig_w.add_trace(go.Bar(
        x=df["month_cn"],
        y=df["water_cum"],
        marker_color=bar_colors,
        name="用水量（吨）",
        hovertemplate="<b>%{x}</b><br>用水：%{y} 吨<extra></extra>",
    ))
    fig_w.add_hline(
        y=actual_avg, line_dash="dot", line_color="gray",
        annotation_text=f"实测月均 {actual_avg:.1f} 吨",
        annotation_position="top right",
    )
    fig_w.add_annotation(
        x="2026年8月", y=31.8,
        text="⚠️ 实测 31.8 吨<br>（7月低估，这月还账）",
        showarrow=True, arrowhead=2, ay=-55, font=dict(color=HIGHLIGHT),
    )
    fig_w.add_annotation(
        x="2026年6月", y=4.8,
        text="仅 4.8 吨<br>（可能外出？）",
        showarrow=True, arrowhead=2, ay=45, font=dict(color="gray"),
    )
    fig_w.update_layout(
        xaxis_title="账单月份",
        yaxis_title="用水量（吨）",
        height=400,
        showlegend=False,
    )
    st.plotly_chart(fig_w, use_container_width=True)

    st.caption("🔵 实际抄表月份  🟠 SP 估算月份  🔴 本次高峰月")

    # 2-month actual analysis
    st.subheader("📊 两次实测之间的真实用水量（排除估算月份）")
    st.markdown("SP 每两个月抄一次表，中间月份是估算。真实用量要看两次实测之间的总量：")

    actual_periods = actual_df.copy().reset_index(drop=True)
    actual_periods["meter_diff"] = actual_periods["water_meter"].diff()
    actual_periods["period_label"] = (
        actual_periods["month_cn"].shift(1).fillna("—") + " ～ " + actual_periods["month_cn"]
    )
    pairs = actual_periods.dropna(subset=["meter_diff"])[
        ["period_label", "meter_diff"]
    ].copy()
    pairs.columns = ["期间（两次实测）", "两个月合计用水（吨）"]
    pairs["两个月合计用水（吨）"] = pairs["两个月合计用水（吨）"].round(1)
    pairs["评价"] = pairs["两个月合计用水（吨）"].apply(
        lambda x: "⚠️ 偏高" if x > 47 else ("⬇️ 偏低（可能外出）" if x < 30 else "✅ 正常")
    )
    st.dataframe(pairs, use_container_width=True, hide_index=True)

    st.success("""
    **✅ 结论：8月水费没有算错，也没有真的用很多水**

    - 8月单月显示 31.8 吨，是因为7月 SP 只估算了 14.0 吨（严重低估）
    - 6月到8月两个月实际合计 = 2446.5 − 2400.7 = **45.8 吨**，完全正常
    - 6月用水很少（4.8 吨），推测那段时间家里没人或外出
    """)

    st.subheader("💧 水费三层计费说明（新加坡 PUB 规定）")
    r1, r2, r3 = st.columns(3)
    r1.metric("① 用水量费", "$1.43 / 吨", "基本水费，PUB 收取，全程未变")
    r2.metric("② 排污税（Waterborne Tax）", "$1.09 / 吨", "政府税：维护新加坡下水道与污水处理系统")
    r3.metric("③ 节水税（Water Conservation Tax）", "= 用水量费 × 50%", "政府税：鼓励节约用水")
    st.caption("三项合计每吨水约 $3.23（税前），加 9% GST 后实际约 **$3.52 / 吨**")


# ───────────────────────────── TAB 2: GAS ───────────────────────────────
with tab2:
    st.subheader("每月燃气用量（度，1 度 = 1 千瓦时 = kWh）")
    st.caption("新加坡燃气账单以千瓦时（kWh，俗称『度』）计量，不同于中国的立方米计法")

    gas_colors = [
        HIGHLIGHT if r["bill_label"] == "Aug 2026"
        else (ESTIMATED_COLOR if r["is_estimated"] else GAS_COLOR)
        for _, r in df.iterrows()
    ]

    fig_g = go.Figure()
    fig_g.add_trace(go.Bar(
        x=df["month_cn"],
        y=df["gas_kwh"].clip(lower=0),
        marker_color=gas_colors,
        name="燃气用量（度）",
        hovertemplate="<b>%{x}</b><br>用气：%{y} 度<extra></extra>",
    ))
    fig_g.add_annotation(
        x="2026年8月", y=486,
        text="⚠️ 486 度<br>两月合计 615 度，历史最高",
        showarrow=True, arrowhead=2, ay=-65, font=dict(color=HIGHLIGHT),
    )
    fig_g.add_annotation(
        x="2026年6月", y=0,
        text="−20 度\n（纠正上月估算）",
        showarrow=True, arrowhead=2, ay=50, font=dict(color="gray"),
    )
    fig_g.update_layout(
        xaxis_title="账单月份",
        yaxis_title="燃气用量（度 / kWh）",
        height=400,
        showlegend=False,
    )
    st.plotly_chart(fig_g, use_container_width=True)

    st.caption("🟠 实际抄表  🟡 SP 估算月份  🔴 本次高峰月 | 2026年6月 −20 度是纠正上月估算偏高")

    # Gas rate history
    st.subheader("⚡ 燃气费率历史（每季度调整一次）")
    rates = pd.DataFrame({
        "季度": ["2025 Q3\n7–9月", "2025 Q4\n10–12月", "2026 Q1\n1–3月", "2026 Q2\n4–6月", "2026 Q3\n7–9月"],
        "税前单价（$/度）": [0.2228, 0.2235, 0.2168, 0.2192, 0.2348],
        "含 GST（$/度）": [0.2429, 0.2436, 0.2363, 0.2389, 0.2559],
        "变化": ["↓ 降价 −0.0044", "↑ 微调 +0.0007", "↓ 降价 −0.0067", "↑ 小涨 +0.0024", "↑↑ 大涨 +0.0156（+7.1%）"],
    })

    fig_rate = go.Figure()
    fig_rate.add_trace(go.Scatter(
        x=rates["季度"],
        y=rates["税前单价（$/度）"],
        mode="lines+markers",
        line=dict(color=GAS_COLOR, width=2),
        marker=dict(size=10),
        hovertemplate="%{x}<br>税前：$%{y:.4f}/度<extra></extra>",
    ))
    fig_rate.add_shape(
        type="rect", x0=3.5, x1=4.5, y0=0.20, y1=0.25,
        fillcolor="rgba(255,68,68,0.1)", line_width=0,
    )
    fig_rate.add_annotation(
        x=4, y=0.237, text="2026 Q3 大涨 +7.1%",
        font=dict(color=HIGHLIGHT), showarrow=False,
    )
    fig_rate.update_layout(
        xaxis_title="季度", yaxis_title="燃气单价（$/度，税前）",
        height=300, yaxis=dict(range=[0.20, 0.26]),
    )
    st.plotly_chart(fig_rate, use_container_width=True)

    st.dataframe(rates, use_container_width=True, hide_index=True)

    # 2-month actual gas
    st.subheader("📊 两次实测之间的真实用气量")
    actual_g = actual_df.copy().reset_index(drop=True)
    actual_g["gas_meter_diff"] = actual_g["gas_meter"].diff()
    actual_g["est_kwh"] = (actual_g["gas_meter_diff"] * 5.17).round(0)
    actual_g["period_label"] = (
        actual_g["month_cn"].shift(1).fillna("—") + " ～ " + actual_g["month_cn"]
    )
    pairs_g = actual_g.dropna(subset=["gas_meter_diff"])[
        ["period_label", "gas_meter_diff", "est_kwh"]
    ].copy()
    pairs_g.columns = ["期间（两次实测）", "气表差值", "估算用气（度）"]
    pairs_g["评价"] = pairs_g["估算用气（度）"].apply(
        lambda x: "⚠️ 偏高" if x > 600 else ("⬇️ 偏低" if x < 300 else "✅ 正常")
    )
    st.dataframe(pairs_g, use_container_width=True, hide_index=True)

    st.error("""
    **⚠️ 结论：8月燃气费确实偏高，两个原因都是真实的**

    1. **实际用气量增加**：6月到8月两个月实际消耗约 615 度，比历史同期（约 510–570 度）高 ~10–20%
       - 建议检查：炉灶使用频率、热水器设定温度、家里人数有没有变化
    2. **费率大幅上调 +7.1%**：2026年7月起从 $0.2192 涨至 $0.2348/度
       - 同样的用量，光是涨价就多付约 $14

    两个因素叠加 → 单月燃气费 **$111.70**（历史均值约 $55）
    """)


# ───────────────────────────── TAB 3: ELECTRICITY ───────────────────────
with tab3:
    st.subheader("⚡ 每月用电量（度，1 度 = 1 千瓦时 = kWh）")
    st.caption("电力零售商：Geneco（YTL PowerSeraya）· 固定价格套餐")

    # Key metrics
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("月均用电量", f"{edf['elec_kwh'].mean():.0f} 度", delta="17个月平均")
    e2.metric("月均电费（账单价）", f"${edf['current_charges'].mean():.2f}", delta="含9% GST")
    e3.metric("当前电价（套餐价）", "$0.2438 / 度", delta="2025年8月续签后，固定至2027年8月")
    e4.metric("U-Save 用于电费（累计）", f"${edf['usave_deduction'].sum():.2f}", delta="合同续签前更多抵扣")

    # Usage bar chart
    elec_bar_colors = [
        ELEC_OLD_COLOR if r["rate"] == 0.2620 else ELEC_NEW_COLOR
        for _, r in edf.iterrows()
    ]
    elec_bar_colors[edf["elec_kwh"].idxmax()] = HIGHLIGHT

    fig_e = go.Figure()
    fig_e.add_trace(go.Bar(
        x=edf["month_cn"],
        y=edf["elec_kwh"],
        marker_color=elec_bar_colors,
        name="用电量（度）",
        hovertemplate="<b>%{x}</b><br>用电：%{y} 度<extra></extra>",
    ))
    fig_e.add_hline(
        y=edf["elec_kwh"].mean(), line_dash="dot", line_color="gray",
        annotation_text=f"月均 {edf['elec_kwh'].mean():.0f} 度",
        annotation_position="top right",
    )
    # Mark contract renewal month
    fig_e.add_vrect(
        x0="2025年8月", x1="2025年9月",
        fillcolor="rgba(156,39,176,0.08)", line_width=0,
    )
    fig_e.add_annotation(
        x="2025年9月", y=edf["elec_kwh"].max() * 0.95,
        text="合同续签<br>$0.2620→$0.2438<br>(-6.9%)",
        showarrow=True, arrowhead=2, ax=40,
        font=dict(color=ELEC_NEW_COLOR, size=11),
    )
    fig_e.add_annotation(
        x="2026年5月", y=822,
        text="历史最高 822 度",
        showarrow=True, arrowhead=2, ay=-50, font=dict(color=HIGHLIGHT),
    )
    fig_e.add_annotation(
        x="2026年6月", y=232,
        text="仅 232 度<br>（推测外出）",
        showarrow=True, arrowhead=2, ay=55, font=dict(color="gray"),
    )
    fig_e.update_layout(
        xaxis_title="账单月份",
        yaxis_title="用电量（度 / kWh）",
        height=420,
        showlegend=False,
    )
    st.plotly_chart(fig_e, use_container_width=True)
    st.caption("🟣 旧合同（$0.2620/度，2023–2025）  🟪 新合同（$0.2438/度，2025–2027）  🔴 历史最高月")

    # Cost chart
    st.subheader("每月电费支出")
    fig_ec = go.Figure()
    fig_ec.add_trace(go.Bar(
        x=edf["month_cn"],
        y=edf["current_charges"],
        name="账单金额（含GST）",
        marker_color=ELEC_COLOR,
        opacity=0.7,
        hovertemplate="<b>%{x}</b><br>账单：$%{y:.2f}<extra></extra>",
    ))
    fig_ec.add_trace(go.Scatter(
        x=edf["month_cn"],
        y=edf["total_payable"],
        name="实付金额（扣U-Save后）",
        mode="lines+markers",
        line=dict(color="black", width=2, dash="dot"),
        marker=dict(size=6),
        hovertemplate="<b>%{x}</b><br>实付：$%{y:.2f}<extra></extra>",
    ))
    # Mark U-Save months
    for _, row in edf[edf["usave_deduction"] > 0].iterrows():
        fig_ec.add_annotation(
            x=row["month_cn"], y=row["total_payable"],
            text=f"U-Save<br>-${row['usave_deduction']:.2f}",
            showarrow=True, arrowhead=2, ay=35,
            font=dict(color=USAVE_COLOR, size=10),
        )
    fig_ec.update_layout(
        xaxis_title="账单月份",
        yaxis_title="电费（$）",
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_ec, use_container_width=True)

    # Geneco plan info
    st.subheader("📋 Geneco 合同详情")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
**旧合同（Get It Fixed 24）**
- 合同期：2023年8月11日 – 2025年8月10日
- 套餐价：**$0.2620 / 度**（税前）
- 含 GST 9%：约 $0.2856 / 度

**新合同（Get It Fixed 24 - Renewal）**
- 合同期：2025年8月11日 – 2027年8月10日
- 套餐价：**$0.2438 / 度**（税前）
- 含 GST 9%：约 $0.2658 / 度
- 续签节省：约 **-6.9%**，每月少付约 $12–16
        """)
    with c2:
        st.markdown("""
**2025年8月账单说明（过渡月）**

该月账单分两段计费：
- 8月6日–10日（旧合同最后5天）：102.7度 × $0.2620
- 8月11日–9月6日（新合同）：555.3度 × $0.2438

此外8月还有 **Geneco Rebate（好友推荐返现）$30**，
直接抵扣税前账单金额，所以总额比正常低约 $33。
        """)

    st.info("""
    **新加坡电力市场（Open Electricity Market）科普**

    新加坡2018年开放零售电力市场，住户可自由选择电力零售商（如 Geneco、Sembcorp、iSwitch 等），
    通常可以选择：① 固定价格套餐（如 Get It Fixed）、② 市价浮动套餐、③ 折扣套餐。
    买"固定价格"套餐的好处是不用担心电价波动，适合用电量稳定的家庭。
    """)


# ───────────────────────────── TAB 4: COST BREAKDOWN ────────────────────
with tab4:
    st.subheader("每月账单费用构成（水费+燃气+垃圾，不含电费）")

    fig_c = go.Figure()
    fig_c.add_trace(go.Bar(
        name="水费（吨数 × 三层费率）",
        x=df["month_cn"], y=df["water_cost"],
        marker_color=WATER_COLOR,
    ))
    fig_c.add_trace(go.Bar(
        name="燃气费（度数 × 当季费率）",
        x=df["month_cn"], y=df["gas_cost"].clip(lower=0),
        marker_color=GAS_COLOR,
    ))
    fig_c.add_trace(go.Bar(
        name="垃圾清理费",
        x=df["month_cn"], y=df["refuse_cost"],
        marker_color=REFUSE_COLOR,
    ))
    fig_c.add_trace(go.Bar(
        name="GST 9%",
        x=df["month_cn"], y=df["gst"],
        marker_color=GST_COLOR,
    ))
    fig_c.add_trace(go.Bar(
        name="U-Save 补贴（政府抵扣，为负值）",
        x=df["month_cn"], y=-df["usave_deduction"],
        marker_color=USAVE_COLOR, opacity=0.8,
    ))
    fig_c.add_trace(go.Scatter(
        name="实际应付金额",
        x=df["month_cn"], y=df["total_payable"],
        mode="lines+markers",
        line=dict(color="black", width=2, dash="dot"),
        marker=dict(size=6),
    ))
    fig_c.update_layout(
        barmode="relative",
        xaxis_title="账单月份",
        yaxis_title="金额（$）",
        height=460,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_c, use_container_width=True)

    # Aug 2026 detailed breakdown
    st.subheader("🔍 2026年8月账单逐项拆解")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("**💧 水费 $102.87**")
        st.markdown("""
| 费用项目 | 计算方式 | 金额 |
|---|---|---|
| ① 用水量费 | 31.8 吨 × $1.43 | $45.47 |
| ② 排污税 | 31.8 吨 × $1.09 | $34.66 |
| ③ 节水税 | $45.47 × 50% | $22.74 |
| **合计** | | **$102.87** |
        """)

    with c2:
        st.markdown("**🔥 燃气费 $111.70**")
        st.markdown("""
| 费用项目 | 计算方式 | 金额 |
|---|---|---|
| 前期补差（旧费率） | 154 度 × $0.2192 | $33.75 |
| 新季度用量 | 332 度 × $0.2348 | $77.95 |
| **合计** | | **$111.70** |
        """)
        st.caption("154 度 = 7月估算不足部分的补差")

    with c3:
        st.markdown("**📋 账单汇总**")
        st.markdown("""
| 项目 | 金额 |
|---|---|
| 水费 | $102.87 |
| 燃气费 | $111.70 |
| 垃圾清理 | $9.76 |
| **税前小计** | **$224.33** |
| GST 9% | $20.19 |
| **当月应付** | **$244.52** |
| U-Save（已抵扣电费） | −$59.10 |
| **实际净支出** | **$185.42** |
        """)

    # U-Save breakdown
    st.subheader("🎁 U-Save 政府补贴记录（每季发放 $150）")
    usave_rows = df[df["usave_deduction"] > 0][["month_cn", "usave_deduction"]].copy()
    usave_rows.columns = ["账单月份", "补贴金额（$）"]
    usave_rows["抵扣说明"] = [
        "全额抵扣当月账单 $110.56，余 $39.44 转用于电费",
        "抵扣后剩余 $29.27 支付",
        "全额抵扣当月账单，余 $12.02 结转下月",
        "全额抵扣当月账单，余 $23.77 结转下月",
        "全额抵扣当月账单 $90.90，余 $59.10 用于电费",
    ]
    st.dataframe(usave_rows, use_container_width=True, hide_index=True)
    st.metric("U-Save 累计节省", f"${total_usave:.0f}", delta="15个月内共收到5次补贴")


# ───────────────────────────── TAB 5: FULL TABLE ────────────────────────
with tab5:
    st.subheader("水费 + 天然气 + 垃圾 完整明细（15个月）")

    disp = df[[
        "month_cn", "period_start", "period_end",
        "water_cum", "gas_kwh", "is_estimated",
        "water_cost", "gas_cost", "refuse_cost", "gst",
        "total_current_charges", "usave_deduction", "total_payable",
    ]].copy()
    disp["period_start"] = disp["period_start"].dt.strftime("%Y-%m-%d")
    disp["period_end"] = disp["period_end"].dt.strftime("%Y-%m-%d")
    disp["is_estimated"] = disp["is_estimated"].map({True: "估算", False: "实际抄表"})

    disp.columns = [
        "月份", "起始日期", "截止日期",
        "用水（吨）", "用气（度）", "读表方式",
        "水费", "燃气费", "垃圾费", "GST",
        "当月应付", "U-Save抵扣", "实际支付",
    ]

    st.dataframe(
        disp,
        use_container_width=True,
        hide_index=True,
        column_config={
            "水费": st.column_config.NumberColumn(format="$%.2f"),
            "燃气费": st.column_config.NumberColumn(format="$%.2f"),
            "垃圾费": st.column_config.NumberColumn(format="$%.2f"),
            "GST": st.column_config.NumberColumn(format="$%.2f"),
            "当月应付": st.column_config.NumberColumn(format="$%.2f"),
            "U-Save抵扣": st.column_config.NumberColumn(format="$%.2f"),
            "实际支付": st.column_config.NumberColumn(format="$%.2f"),
        },
    )

    st.subheader("Geneco 电费完整明细（17个月）")
    edisp = edf[[
        "month_cn", "period_start", "period_end",
        "elec_kwh", "rate", "elec_pretax", "gst",
        "current_charges", "geneco_rebate", "usave_deduction", "total_payable",
    ]].copy()
    edisp["period_start"] = edisp["period_start"].dt.strftime("%Y-%m-%d")
    edisp["period_end"] = edisp["period_end"].dt.strftime("%Y-%m-%d")
    edisp.columns = [
        "月份", "起始日期", "截止日期",
        "用电（度）", "套餐单价（$/度）", "税前金额",
        "GST", "账单金额", "Geneco返现", "U-Save抵扣", "实际支付",
    ]
    st.dataframe(
        edisp,
        use_container_width=True,
        hide_index=True,
        column_config={
            "税前金额": st.column_config.NumberColumn(format="$%.2f"),
            "GST": st.column_config.NumberColumn(format="$%.2f"),
            "账单金额": st.column_config.NumberColumn(format="$%.2f"),
            "Geneco返现": st.column_config.NumberColumn(format="$%.2f"),
            "U-Save抵扣": st.column_config.NumberColumn(format="$%.2f"),
            "实际支付": st.column_config.NumberColumn(format="$%.2f"),
        },
    )

    st.divider()
    st.markdown("""
    **单位说明：**
    - **吨（Cu M）**：立方米，1 吨水 = 1,000 升 = 1 立方米
    - **度（kWh）**：千瓦时，新加坡燃气和电费账单的标准计量单位

    **税费说明：**
    - **排污税（Waterborne Tax）**：$1.09/吨，用于维护新加坡污水收集和处理系统
    - **节水税（Water Conservation Tax）**：用水量费的 50%，鼓励节约用水
    - **GST**：9% 消费税，适用于所有项目
    """)



# ───────────────────────────── TAB 6: ANALYSIS ──────────────────────────
with tab6:
    st.subheader("📊 账单综合分析")

    sp_total = df["total_payable"].sum()
    elec_total = edf["total_payable"].sum()
    sp_months = len(df)
    elec_months = len(edf)

    col1, col2, col3 = st.columns(3)
    col1.metric("水费+天然气总支出（15个月）", f"${sp_total:.2f}", delta="含垃圾费，扣U-Save后")
    col2.metric("Geneco电费总支出（17个月）", f"${elec_total:.2f}", delta="扣U-Save和返现后")
    col3.metric("月均综合水电费", f"${(sp_total/sp_months + elec_total/elec_months):.2f}", delta="水气月均+电费月均")

    st.divider()

    st.markdown("### 💧 用水分析")
    st.markdown("""
**8月2026水费为何显示 $102.87？是算多了吗？**

不是。这是 SP **估算制度**造成的视觉误差：SP 每两个月才实际抄一次水表，中间月份是估算。

- 2026年7月（估算月）：SP 估算用水仅 14.0 吨，实际严重低估
- 2026年8月（实抄月）：系统"补回"7月低估的部分，导致单月显示 31.8 吨

**真实情况**：6月至8月两个月合计用水 = 水表读数差 = 2446.5 − 2400.7 = **45.8 吨**，完全处于正常范围（历史两月均值约 41–48 吨）。

另外，2026年6月用水极少（仅 4.8 吨），推测家里人员外出或长时间不在家。
    """)

    st.markdown("### 🔥 燃气分析")
    st.markdown("""
**8月2026燃气费 $111.70，是真的偏高吗？**

是的，这次燃气偏高是**真实的**，有两个同时发生的原因：

**① 用气量确实增加**
2026年6月至8月两月实测合计约 615 度，比历史同期（约 510–570 度）偏高约 10–20%。
可能原因：热水器使用频率增加、烹饪更多、或家庭成员变化。

**② 燃气费率大幅上调 +7.1%**
2026年7月起，SP 管道燃气费率从 $0.2192/度 涨至 $0.2348/度，是过去12个月中最大的一次涨幅。同等用量，单此一项就多付约 $14。

两个因素叠加，是8月燃气费大幅超出历史均值（约 $55）的直接原因。
    """)

    st.markdown("### ⚡ 电费分析")
    st.markdown("""
**合同续签节省了多少？**

2025年8月，Geneco 套餐从旧合同（$0.2620/度）续签为新合同（$0.2438/度），电价下调 **6.9%**。以家庭月均用电 600 度计算，每月节省约 **$13**，合同两年期（2025–2027）累计可节省约 **$310**。

**用电量规律**

| 月份特征 | 用电量 | 原因推测 |
|---|---|---|
| 2025年8月 | 849 度（旧合同期最高） | 夏季空调高频使用 |
| 2025年12月 | 409 度（年度低谷） | 年末假期外出 / 天气凉快 |
| 2026年3月 | 386 度（历史最低） | 天气转凉，空调减少 |
| 2026年5月 | **822 度（历史最高）** | 热季高峰，空调全开 |
| 2026年6月 | 232 度（异常低） | 家庭外出旅游 |

**用电量偏高的提示**

家庭月均用电约 **600 度**，显著高于新加坡3–4人家庭均值（约360–440度）。主要高耗电设备通常是：空调（占家庭用电50–60%）、热水器（15–20%）、冰箱（10%）。建议检查空调设定温度是否合理（建议不低于25°C），以及是否存在长时间待机情况。

**U-Save 电费抵扣**
Geneco 账户共收到三次 U-Save 抵扣：
- 2025年4月：$19.51（旧合同期）
- 2025年7月：$39.44（旧合同期）
- 2026年7月：$59.10（新合同期，金额增加）

U-Save 金额逐步增加，与政府近年来为应对生活成本上涨而加大补贴力度的政策一致。
    """)

    st.markdown("### 💰 综合支出总结")
    st.markdown("""
家庭**月均综合水电费**（水+燃气+垃圾+电）约 **$310–350**，其中电费占比最大（约 55%），燃气次之（约 20%），水费和垃圾费合计约 25%。

政府 U-Save 补贴每季度 $150，全年合计 $600，分配给 SP 账户和电力账户，有效减轻家庭水电负担约 15–18%。
    """)

