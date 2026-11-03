# 06 复现、校验与轮流交接

## 使用现有成果

从[根README](../../README.md)进入，不必重新运行即可查看各阶段报告、CSV和图。两人轮流工作，统一以[WORK_LOG](../../STV_ED_motion_study/WORK_LOG.md)记录当前状态，无需按个人划分目录。

## 当前仿真环境

当前BEV代码使用Python、NumPy、Matplotlib；记录环境为Python 3.14.7、NumPy 2.5.3，当前绘图版本见[环境快照](../../STV_ED_motion_study/environment_snapshot.json)。这些是本机记录，不代表验证过所有Python版本。

在独立环境中可依据[requirements.txt](../../STV_ED_motion_study/requirements.txt)安装依赖。该文件提供包列表，没有声称跨平台严格锁定；各实验JSON里的环境及代码哈希才对应其结果生成记录。

原始调度复现还需要pandas，其审阅环境有单独的[requirements-review.txt](../../STV_ED_review_20261103/requirements-review.txt)，不要与当前BEV依赖版本混为同一实验环境。`STV_ED_review_20261103/python_packages`是当时局部安装的第三方包，不属于自编算法成果。

## 最新阶段完整命令

从工作区根目录开始：

```powershell
Set-Location -LiteralPath '.\STV_ED_motion_study\bev'
python -m unittest -v test_crossing_uncertain.py
python crossing_uncertain.py
python verify_crossing_uncertain.py
python plot_crossing_uncertain.py
```

第一个命令运行单元测试；后面三个会写入 `results_crossing_uncertain`，其中验证器也会更新验证JSON。若要保留本轮快照，先复制整个相关阶段或另设新的输出目录再运行。只复制单个最新脚本会缺失导入依赖。

其他阶段命令见[BEV README](../../STV_ED_motion_study/bev/README.md)及[主线README](../../STV_ED_motion_study/README.md)。本轮整理未重跑物理实验；验证集中在文件完整性、代码哈希和导航链接。

## 文件核对

在工作区根目录执行：

```powershell
python 成果导航/tools/catalog_artifacts.py
```

脚本输出[文件清单](../文件清单.csv)、[分类统计](../分类统计.json)及[整理校验](../整理校验.json)。会检查整理前文件是否仍在、旧内容是否只发生允许的交接记录更新、原包15文件是否与原始清单一致、最新阶段7个源文件是否与保存哈希一致，并检查本轮README及导航的本地链接。

若以后有意修改模型，原实验代码哈希不再匹配是正常的追溯信号，应生成新的实验快照并更新说明。不要为了让校验通过而无说明地替换旧实验哈希。文件清单本身和校验JSON不自我计入清单，避免自引用哈希。

## 每轮交接

1. 先读当前状态与失败证据，明确本轮研究问题及同条件对照。
2. 修改前保存参数、代码与结果的对应关系，避免覆盖历史证据。
3. 运行与改动相称的测试；记录失败、无参考和超时，不只记录成功。
4. 更新WORK_LOG：改了什么、怎么运行、数据在哪、结果和边界、下一件具体任务。
5. 如新增文件或目录，更新分类导航和文件清单。

报告中的模型精度、零碰撞与创新性均受各自证据范围约束。未来投稿前仍需完成公式级文献对照和公平基准实验。
