# 车辆运动研究：当前主线

当前阶段：S05观测预测分离与行驶中周期更新。入口为[WORK_LOG](WORK_LOG.md)、[BEV代码说明](bev/README.md)和[最新验证报告](bev/观测预测分离与滚动更新验证记录.md)。

当前目标是检验低速车辆在时变狭窄环境中的可执行运动方案；使用通用BEV假设参数，尚无车型标定和独立创新结论。

## 文件分类

| 位置 | 内容 |
|---|---|
| [研究方案与首轮运动验证](研究方案与首轮运动验证.md) | 研究假设、执行误差、FaSTrack/RTD对照边界 |
| [motion_window_probe.py](motion_window_probe.py) | S01简化车辆运动与冲突区占用时间探针 |
| [verify_probe.py](verify_probe.py) | S01物理与输出核对，会写回验证记录 |
| [results](results/README.md) | S01结果，不是最新BEV结果 |
| [bev](bev/README.md) | S02—S05的模型、控制、场景、测试与结果 |
| [requirements.txt](requirements.txt) | 当前主线所需包列表 |
| [environment_snapshot.json](environment_snapshot.json) | 整理时的本机环境记录，非全部实验的统一环境锁 |

## S01历史探针运行

在本目录执行：

```powershell
python motion_window_probe.py
python verify_probe.py
```

会写入本目录的results。其经验占用时间范围不能直接当作安全包络，也不与S05的72例合并。

## 共享约定

轮流推进同一项目，以WORK_LOG交接。每个新实验保留参数、代码哈希、输出和失败。阶段报告记录当时状态，当前工作以WORK_LOG最新章节为准。

完整成果与文献导航见[工作区README](../README.md)。
