# ACC观测中断：历史候选

入口：[研究可行性与查新报告](研究可行性与查新报告.md)。结论为本地最小原型可行，有明显相近工作，新颖性尚未确立。

- [experiment.py](experiment.py)：标准库实现的一维纵向探针，含制动轨迹筛选和舒适/紧急约束切换。
- [results.csv](results.csv)、[summary.json](summary.json)：72种确定性场景、5种内部策略的结果。
- [checks.json](checks.json)：积分、边界和选定步长检查。
- `trace_*.csv`、[example.png](example.png)：示例回放和图。

尚未实现报告设想的完整“可容忍观测中断预算”；不是文献算法复现或当前BEV执行模型。部分策略在指定场景零碰撞，不构成无条件安全；边界失配压力测试中存在碰撞。

在本目录运行 `python experiment.py` 会重写此处结果；如需保留请先复制。当前车辆研究从[主线README](../STV_ED_motion_study/README.md)进入。
