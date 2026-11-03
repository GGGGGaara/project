# 02 仿真代码

当前代码主入口见[BEV README](../../STV_ED_motion_study/bev/README.md)。各阶段共用文件，保持原位可避免导入和输出路径失效。

| 阶段 | 模型/运行 | 测试与验证 | 绘图 |
|---|---|---|---|
| S01 运动机制 | [motion_window_probe.py](../../STV_ED_motion_study/motion_window_probe.py) | [verify_probe.py](../../STV_ED_motion_study/verify_probe.py) | 主脚本内生成 |
| S02 BEV初版 | [bev_probe.py](../../STV_ED_motion_study/bev/bev_probe.py) | [test_bev.py](../../STV_ED_motion_study/bev/test_bev.py)、[verify_cases.py](../../STV_ED_motion_study/bev/verify_cases.py) | 主脚本内生成 |
| S03 停车v2 | [stopping_v2.py](../../STV_ED_motion_study/bev/stopping_v2.py) | [verify_stopping_v2.py](../../STV_ED_motion_study/bev/verify_stopping_v2.py) | [plot_stopping_v2.py](../../STV_ED_motion_study/bev/plot_stopping_v2.py) |
| S04 二维横穿 | [crossing_2d.py](../../STV_ED_motion_study/bev/crossing_2d.py) | [test_crossing_2d.py](../../STV_ED_motion_study/bev/test_crossing_2d.py)、[verify_crossing_2d.py](../../STV_ED_motion_study/bev/verify_crossing_2d.py) | [plot_crossing_2d.py](../../STV_ED_motion_study/bev/plot_crossing_2d.py) |
| S05 观测误差与更新 | [crossing_uncertain.py](../../STV_ED_motion_study/bev/crossing_uncertain.py) | [test_crossing_uncertain.py](../../STV_ED_motion_study/bev/test_crossing_uncertain.py)、[verify_crossing_uncertain.py](../../STV_ED_motion_study/bev/verify_crossing_uncertain.py) | [plot_crossing_uncertain.py](../../STV_ED_motion_study/bev/plot_crossing_uncertain.py) |

最新链路的主要依赖是 `crossing_uncertain → crossing_2d → stopping_v2 → bev_probe`，具体导入以源码为准。`bev_probe.py`虽然包含历史实验入口，其参数等定义仍被后续代码复用，不能当作纯废弃文件删除。

原始调度代码在[原交付包](../../STV_ED_reproducible_pilot_bundle/rural_narrow_road_research/README.md)，复跑副本在[审阅目录](../../STV_ED_review_20261103/README.md)。ACC和等待位姿探针是独立历史模型，见[历史探索](../05_历史探索/README.md)，不要合并其结果作为同一BEV实验。
