# S03 停车v2结果

代码：[stopping_v2.py](../stopping_v2.py)；解释：[停车模块改进与验证记录](../停车模块改进与验证记录.md)。

48组输入中，36组找到参考并完成两次停车，最大停车位置误差约7.3 mm；12组4 m/s、10 m停车距离输入未在指定参考族与约束内找到轨迹。此精度只属于合成平路仿真，搜索失败不等于物理不可停车。

- [sweep.json](sweep.json)、[sweep.csv](sweep.csv)：全部输入与结果，保留无参考工况。
- [verification.json](verification.json)：物理、积分、分类和数值检查。
- [run_metadata.json](run_metadata.json)：运行参数及快照记录。
- `diagnostics_before_regularization.json`：低速摩擦正则化之前的诊断，不能并入最终扫描。
- 其他轨迹、图和补充工况按原文件名保存，见[全量清单](../../../成果导航/文件清单.csv)。

完整运行顺序见[BEV README](../README.md)。验证器也可能更新本目录文件。
