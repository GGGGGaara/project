# S05 观测误差与滚动更新：最终72例

代码：[crossing_uncertain.py](../crossing_uncertain.py)；分析：[最新验证报告](../观测预测分离与滚动更新验证记录.md)。

## 最终数据

| 策略 | 无碰撞完成 | 碰撞终止 |
|---|---:|---:|
| frozen | 8/24 | 16/24 |
| refresh_hold | 10/24 | 14/24 |
| rolling | 22/24 | 2/24 |

72例为4种手工运动、3种确定性观测条件、2种车辆条件和3种策略的组合，不是随机抽样交通事故率。两次滚动失败均保留，普通停车搜索失败也不意味着物理不可避免。

## 文件结构

- [episodes.json](episodes.json)、[episodes.csv](episodes.csv)：唯一的最终72例索引和统计依据。
- [config_summary.json](config_summary.json)：场景、观测、汇总、部分环境信息和主模型哈希。
- 每例 `*_trace.csv`：实际车辆和横穿状态、间距、接触、功率与转矩/制动输出。
- 每例 `*_events.json`：收到的观测、使用的预测、风险检查及决策。
- 每例 `*_observations.json`：观测时间戳、位置和速度；控制器只能依据已收到的观测预测。
- [verification_failure_analysis.json](verification_failure_analysis.json)：72例回放核对、4例步长对照和两次滚动碰撞诊断。
- [source_manifest.json](source_manifest.json)：本阶段7个代码文件哈希。
- [pause_comparison.png](pause_comparison.png)：临时停顿的策略对照。
- [retained_failure.png](retained_failure.png)：未避免的碰撞时间线。
- [clock_boundary_diagnostic](clock_boundary_diagnostic/README.md)：修复前历史诊断，排除在最终72例之外。

每个最终用例恰有轨迹、决策、观测三个文件，共216个逐例文件。请从episodes.json列出的名称定位，勿递归汇总诊断目录。失败的finish_s为空；接触终止后无碰撞物理仿真。

复现命令见[BEV README](../README.md)，重新执行会更新本目录结果。
