# 每月账单更新方法

收到新账单后，下载 PDF，从账单里找到以下数字，手动追加到对应 CSV 末尾一行。

---

## 水费 + 天然气（SP Services）

文件：`dataset/sp_bills.csv`

每行格式：
```
month, bill_label, period_start, period_end,
water_cum, gas_kwh,
water_cost, gas_cost, refuse_cost, others_cost, gst,
total_current_charges, usave_deduction, total_payable,
is_estimated, water_meter, gas_meter
```

- `month`：账单月份，格式 `YYYY-MM`（如 `2026-09`）
- `water_cum`：本月用水量（吨），账单上写的 Cu M
- `gas_kwh`：本月用气量（度），估算月可能是负数（纠正上月）
- `is_estimated`：估算月填 `True`，实际抄表月填 `False`
- `water_meter` / `gas_meter`：实际抄表月才有读数，估算月留空

---

## 电费（Geneco）

文件：`dataset/elec_bills.csv`

每行格式：
```
month, bill_label, period_start, period_end,
elec_kwh, rate, elec_pretax, gst, current_charges,
geneco_rebate, usave_deduction, total_payable
```

- `rate`：当前套餐单价，固定合同到2027年8月，目前是 `0.2438`
- `elec_pretax`：税前金额 = `elec_kwh × rate`
- `gst`：税前金额 × 9%
- `current_charges`：账单总额（含GST），即账单上显示的 Current Charges
- `geneco_rebate`：如有 Geneco 返现（好友推荐等），填税前金额；没有填 `0`
- `usave_deduction`：当月 U-Save 抵扣额；没有填 `0`
- `total_payable`：实付金额 = `current_charges - usave_deduction`

---

## 更新后发布

追加完 CSV 后，在终端执行：
```bash
git add dataset/ && git commit -m "Add YYYY-MM bill" && git push
```
Streamlit Cloud 会自动重新加载，几分钟后看板更新。
