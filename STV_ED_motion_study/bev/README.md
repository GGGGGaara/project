# BEV仿真代码与阶段结果

最新入口：[crossing_uncertain.py](crossing_uncertain.py)。最新解释：[观测预测分离与滚动更新记录](观测预测分离与滚动更新验证记录.md)。交接状态：[WORK_LOG](../WORK_LOG.md)。

模型采用通用纯电乘用车假设参数：电机驱动/再生、摩擦制动响应、简化能量记录与二维运动学。没有标定真实车型，也没有轮胎滑移、ABS或完整热模型。再生能力受限时可由摩擦制动补偿，不能概括为“电动车不能刹住”。

## 代码与数据对应

| 阶段 | 主脚本 | 文档 | 数据 |
|---|---|---|---|
| S02 BEV初版 | [bev_probe.py](bev_probe.py) | [模型说明](纯电动车模型与输出特性说明.md) | [results](results/README.md) |
| S03 停车v2 | [stopping_v2.py](stopping_v2.py) | [停车验证](停车模块改进与验证记录.md) | [results_stopping_v2](results_stopping_v2/README.md) |
| S04 二维横穿 | [crossing_2d.py](crossing_2d.py) | [二维联调](二维横穿场景联调记录.md) | [results_crossing_2d](results_crossing_2d/README.md) |
| S05 观测误差与更新 | [crossing_uncertain.py](crossing_uncertain.py) | [最新验证](观测预测分离与滚动更新验证记录.md) | [results_crossing_uncertain](results_crossing_uncertain/README.md) |

文件均保持原位。最新代码依赖前面阶段定义；请保留整个bev目录，而不是只复制一个脚本。

## 最新阶段运行

在本目录执行，需要NumPy、Matplotlib：

```powershell
python -m unittest -v test_crossing_uncertain.py
python crossing_uncertain.py
python verify_crossing_uncertain.py
python plot_crossing_uncertain.py
```

对应6项因果/观测测试、72例执行、独立回放核对及4例步长对照、结果绘图。仿真结果为 frozen 8/24、refresh_hold 10/24、rolling 22/24无碰撞完成；rolling的2次碰撞仍保留。观测为确定性延迟/偏差，未构成随机交通统计。

预测端仍沿名义参考估计占用，尚未传播实际执行器状态及误差；横向路径固定。前进时周期更新不等于各模式下连续重优化；紧急回退未获安全证明。

## 其他阶段运行

S03停车v2：

```powershell
python stopping_v2.py
python verify_stopping_v2.py
python plot_stopping_v2.py
```

S04二维横穿：

```powershell
python -m unittest -v test_crossing_2d.py
python crossing_2d.py
python verify_crossing_2d.py
python plot_crossing_2d.py
```

S02初版只用于追溯与模型依赖，独立重跑时：

```powershell
python -m unittest -v test_bev.py
python bev_probe.py
python verify_cases.py
```

这些命令会更新各自结果目录。验证脚本不一定是只读程序，可能补写验证JSON；如需保留本轮快照，先保存完整副本或另设输出目录。

本次目录整理没有修改这些Python文件，也没有重新运行实验。
