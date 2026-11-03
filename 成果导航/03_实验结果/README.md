# 03 实验结果与失败记录

## 结果按阶段使用

| 阶段 | 数据说明 | 地位 |
|---|---|---|
| S00 原调度 | [原包结果与定义](../../STV_ED_reproducible_pilot_bundle/rural_narrow_road_research/README.md) | 原始快照，exposure是调度重叠 |
| S00-R 复跑 | [审阅README](../../STV_ED_review_20261103/README.md) | 核对原调度，非新增车辆实验 |
| S01 运动机制 | [results/README](../../STV_ED_motion_study/results/README.md) | 早期占用时间探针 |
| S02 BEV初版 | [bev/results/README](../../STV_ED_motion_study/bev/results/README.md) | 历史停车结果，不是v2 |
| S03 停车v2 | [results_stopping_v2/README](../../STV_ED_motion_study/bev/results_stopping_v2/README.md) | 当前纵向停车基准 |
| S04 二维横穿 | [results_crossing_2d/README](../../STV_ED_motion_study/bev/results_crossing_2d/README.md) | 理想恒速预测场景 |
| S05 误差与更新 | [results_crossing_uncertain/README](../../STV_ED_motion_study/bev/results_crossing_uncertain/README.md) | 最新场景数据 |

## 最新结果阅读顺序

1. [config_summary.json](../../STV_ED_motion_study/bev/results_crossing_uncertain/config_summary.json)：条件、三种策略、24例/策略及代码哈希。
2. [episodes.csv](../../STV_ED_motion_study/bev/results_crossing_uncertain/episodes.csv)：最终72例逐例状态。
3. [verification_failure_analysis.json](../../STV_ED_motion_study/bev/results_crossing_uncertain/verification_failure_analysis.json)：独立核对、4例步长对照及两次滚动失败。
4. [道路中停顿对照图](../../STV_ED_motion_study/bev/results_crossing_uncertain/pause_comparison.png)和[保留碰撞诊断图](../../STV_ED_motion_study/bev/results_crossing_uncertain/retained_failure.png)。

最新策略的22/24不是现实安全率。三策略各自成功集合不同，不能直接用成功样本均值排名通行效率。碰撞、无参考、超时和无进展应分别解释；参考搜索失败不是物理不可行证明。

## 历史诊断不可并入最终统计

- 停车v2中保留近零速正则化之前的数值诊断。
- S05的 `clock_boundary_diagnostic` 是计时边界修复前的输出；其中 `obsolete_sensor_labels` 保存旧标签文件。
- 最新72例由 `episodes.json` 枚举。不要对结果目录递归匹配所有CSV后求和，这会混入旧版本和逐时刻轨迹。

本轮整理仅增加导航与文件核对，没有重新运行或改写实验数值。
