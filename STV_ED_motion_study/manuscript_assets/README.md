# 本轮论文证据附件

- `evidence_audit.json`：原始15,000条调度记录再聚合、72例统计、模型哈希、共同成功子集和失败惩罚指标。生成入口为上级目录的 `audit_manuscript.py`，需要 NumPy/Matplotlib。
- `execution_comparison.png`：对应正文图2，以72例汇总生成。
- `replay_verification.json`：本轮重新运行原验证器，检查72条回放并重跑4例细化步长的结果。
- `crossref_verified.json`：本轮 DOI 查询原始记录。三项成功、三项限流，其他身份核查来源和读取范围见上级目录的中文核验报告。
- `render_acceptance.json`：Word 导出后逐页检查记录。标准 LibreOffice 渲染器不可用，后台 Word COM 被拒绝，最终通过已安装 Word 的界面原生导出 PDF，再用 PyMuPDF 栅格化检查全部8页。

既有17项测试本轮全部通过。完整调度数据、历史所有结果不在这里复制；按正文和原目录说明定位，避免递归汇总旧诊断目录。
