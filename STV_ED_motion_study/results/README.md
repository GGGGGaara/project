# S01 车辆运动与占用时间探针结果

生成代码：[motion_window_probe.py](../motion_window_probe.py)；核对：[verify_probe.py](../verify_probe.py)；解释：[首轮运动验证](../研究方案与首轮运动验证.md)。

- [probe_summary.json](probe_summary.json)：参数、经验统计与验证记录。
- [occupancy_windows.csv](occupancy_windows.csv)：采样工况的冲突区占用窗口。
- `v3_offset*.csv`：选定轨迹逐时刻状态。
- [timing_margin_probe.png](timing_margin_probe.png)：占用时间示意。

这些结果来自简化运动/执行误差模型，早于BEV执行链路。扰动采样范围不是证明过的安全界；不能作为S05实验数据。
