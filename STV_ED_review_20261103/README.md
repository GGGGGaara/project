# 原架构审阅、复现与补充文献

日期：2026-11-03。原包位于[原始快照](../STV_ED_reproducible_pilot_bundle/README.md)。本目录是审阅工作区，非当前BEV仿真入口。

## 报告与结论

- [架构与文献审阅报告](STV_ED_架构与文献审阅报告.md)：原15文件检查、原数值复现、边界反例和相关工作对照。
- [创新性重构建议](创新性重构方案_车辆等待姿态与通行恢复.md)：历史研究建议，后续已转向[车辆运动研究](../STV_ED_motion_study/README.md)，不代表当前算法。
- [source_manifest.json](source_manifest.json)：原包15文件的哈希，整理校验以此核对内层原文件。
- [reproduction_verification.json](reproduction_verification.json)：原结果复现与独立核对。

原调度数据可复现，不等于完成车辆闭环或确认原创。报告中的资源重叠不可当作车体碰撞。

## 目录分类

| 内容 | 位置 |
|---|---|
| 原文与提取内容 | `tmp/papers`，含6篇下载PDF及逐页提取记录 |
| 文献身份与下载记录 | [crossref_metadata.json](crossref_metadata.json)、[paper_downloads.json](paper_downloads.json) |
| 补充BibTeX | [supplementary_references.bib](supplementary_references.bib) |
| 文档提取 | 两个STV_ED文本文件、`embedded_media`内嵌图、`render_english`渲染尝试 |
| 原脚本复跑 | `rerun`，与原包相互独立 |
| 审阅/探针脚本 | inspect_bundle、extract_papers、verify_outputs、probe_model |
| 审阅环境 | [requirements-review.txt](requirements-review.txt)、`python_packages`局部第三方安装 |

文献入口见[文献分类](../成果导航/04_文献与查新/README.md)。`python_packages`不列入研究成果清单，避免将依赖源码误算为自编研究成果。文档提取和渲染尝试不代表原DOCX最终排版已经验收。

如复跑原调度，请在副本中运行，命令和参数见审阅报告。当前BEV开发无需运行本目录的文档提取或下载脚本。
