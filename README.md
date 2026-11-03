# 智能车辆研究工作区

整理日期：2026-11-03。面向两人轮流推进、指导老师审阅和本地仿真复现。

当前主线是**乡镇集市等时变狭窄通行环境中的车辆运动规划与控制**，仿真车辆为通用纯电动乘用车。乡镇集市提供问题背景，研究重点保持在车辆自身的运动与执行能力。

当前成果是研究准备、仿真基线和失败诊断，**尚未确认独立创新，尚未形成可投稿的完整方法验证**。

2026-11-03 论文修订：已在[原 Word 路径](STV_ED_reproducible_pilot_bundle/rural_narrow_road_research/STV_ED_english_pilot_manuscript.docx)覆盖修订正文，并提供[PDF](STV_ED_motion_study/STV_ED_final.pdf)、[可检索正文](STV_ED_motion_study/manuscript.md)和[中文修订与文献核验](STV_ED_motion_study/论文修订与文献核验.md)。纳入车辆执行与观测更新，补充 SIPP/SIPP-IP/FaSTrack，保留失败与研究边界；原稿可由历史提交或原 ZIP 恢复。此前的原包“内层不变”说明只描述此前整理阶段。

## 从哪里开始

1. 了解当前做到了哪里：读[成果总览](成果导航/01_研究说明/README.md)。
2. 接着开发：读[共享工作记录](STV_ED_motion_study/WORK_LOG.md)和[当前仿真入口](STV_ED_motion_study/bev/README.md)。
3. 看最新证据：读[观测预测分离与滚动更新报告](STV_ED_motion_study/bev/观测预测分离与滚动更新验证记录.md)。
4. 找已有研究与创新边界：读[文献与查新导航](成果导航/04_文献与查新/README.md)。
5. 给队友交接或复现：读[复现与交接说明](成果导航/06_复现与交接/README.md)。

## 六类成果

| 类别 | 内容 |
|---|---|
| [01 研究说明](成果导航/01_研究说明/README.md) | 主线、各阶段成果、证据边界和未解决问题 |
| [02 仿真代码](成果导航/02_仿真代码/README.md) | 模型、控制、场景、测试、验证和绘图脚本的对应关系 |
| [03 实验结果](成果导航/03_实验结果/README.md) | 当前结果、历史数据、失败和计时诊断的区别 |
| [04 文献与查新](成果导航/04_文献与查新/README.md) | 本地论文、BibTeX、文献核查及阅读材料 |
| [05 历史探索](成果导航/05_历史探索/README.md) | ACC观测中断、TimeTrap、等待位姿等早期方向 |
| [06 复现与交接](成果导航/06_复现与交接/README.md) | 运行命令、环境要求、文件核对和轮流工作约定 |

分类采用导航和原目录README，代码及数据保持原位。避免改变模块导入、输出路径及原始交付包的文件哈希。全量可检索记录见[文件清单](成果导航/文件清单.csv)，每项包含相对路径、类别、阶段、大小与SHA256；记录是整理时的快照。

## GitHub获取

仓库：[GGGGGaara/project](https://github.com/GGGGGaara/project)。获取完整文件：

```powershell
git clone https://github.com/GGGGGaara/project.git
Set-Location -LiteralPath '.\project'
```

仓库保留代码、报告、文献材料及各阶段结果；第三方安装包、Python缓存和本地环境由[.gitignore](.gitignore)排除。[.gitattributes](.gitattributes)关闭自动换行转换，以保留已有结果及源文件哈希。复现环境请重新安装依赖。第三方文献的著作权归原作者或出版方，本仓库未对这些文献授予额外许可。

## 当前主要结果

| 阶段 | 已完成 | 解释限制 |
|---|---|---|
| 原始时间窗调度 | 原数据复现和独立审阅 | 资源时间重叠不等同车辆物理碰撞 |
| 纯电动车停车v2 | 48组输入中36组完成，12组未找到指定参考 | 毫米级误差仅是合成仿真结果；搜索失败不是物理不可停车 |
| 二维恒速横穿 | 60次运行；stop_wait、candidate各15/15无碰撞完成 | 固定路径、理想预测、手工场景 |
| 观测误差与滚动更新 | 72次运行；三策略分别8/24、10/24、22/24无碰撞完成 | 最后一个策略仍有2次碰撞；不是现实事故率或安全保证 |

最新的两次碰撞完整保留。下一项研究任务是检查：根据车速、驱动转矩、制动建立状态和观测延迟限制前进动作，能否持续保留可执行的停车备选；需与固定低速、固定安全裕量作同条件对照并继续查新。

## 原目录用途

| 目录或文件 | 定位 |
|---|---|
| [STV_ED_motion_study](STV_ED_motion_study/README.md) | 当前开发主线 |
| [STV_ED_review_20261103](STV_ED_review_20261103/README.md) | 原架构审阅、复现和补充文献 |
| [STV_ED_reproducible_pilot_bundle](STV_ED_reproducible_pilot_bundle/README.md) | 原始15文件交付快照，内层内容保持原样 |
| [market_decision_research](market_decision_research/README.md) | 集市相关文献、历史等待位姿探索 |
| [acc_observation_gap](acc_observation_gap/README.md) | 早期ACC候选及最小实验 |
| [timetrap_translation](timetrap_translation/README.md) | TimeTrap译文及精华提炼 |
| [ITSC/ICMA早期报告](智能车辆_ITSC_ICMA文献与选题分析报告.md) | 历史选题背景；会议时间等信息使用前应重新核验 |
| [原始ZIP](STV_ED_reproducible_pilot_bundle.zip) | 原交付压缩包，未在本轮重新打包 |

## 快速使用

现有结果可以直接阅读，无需重新运行。最新阶段在PowerShell中执行：

```powershell
Set-Location -LiteralPath '.\STV_ED_motion_study\bev'
python -m unittest -v test_crossing_uncertain.py
```

完整运行顺序见[BEV README](STV_ED_motion_study/bev/README.md)。仿真、验证和绘图命令会写入对应结果目录；更改实验前先保存快照，勿混用不同阶段的结果。
