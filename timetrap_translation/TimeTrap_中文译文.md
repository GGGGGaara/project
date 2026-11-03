# 性能干扰的实证研究：时序违规模式及其影响

**原题：** An Empirical Study of Performance Interference: Timing Violation Patterns and Impacts  
**作者：** Ao Li、Jinwen Wang、Sanjoy Baruah、Bruno Sinopoli、Ning Zhang  
**机构：** 美国圣路易斯华盛顿大学  
**发表：** IEEE RTAS 2024，320–333 页，DOI：10.1109/RTAS61025.2024.00033。  
**译本依据：** 用户提供的 `C:/Users/ll175/Desktop/li2024_timetrap.pdf`，17 页作者版本。2026-11-01 整理。

## 译本说明

本文按原文章节、论证与段落内容翻译，包含正文和补充案例。英文参考文献、项目名、代码标识符与文献编号保留，以便检索。原图不重绘；图中文字与图注另作中文说明，并提供原页图像入口。原文代码保留其逻辑含义，正文中解释；可逐行对照原页。公式已通过页面图像核对。个别原文排版错误或前后不一致之处以“译注”标明，不擅自改成新的作者结论。本文不是官方译本；独立的研究判断见《精华提炼与选题影响》，不属于作者原文。

术语：performance interference＝性能干扰；temporal displacement＝时间偏移；deadline miss＝截止时间违约／超时；aggressor workload＝干扰负载；victim task＝受扰任务；jitter＝抖动；fail-safe＝故障安全保护；CPS＝信息物理系统；HiTL＝硬件在环；SiTL＝软件在环。

## 摘要

多核平台在汽车、机器人等信息物理系统中日益普及，但共享资源竞争使时序可预测性难以得到保证。已有研究主要刻画这类干扰能够造成多大延迟，通常采用对抗视角；对于不同信息物理平台中这些时序延迟的物理影响，认识仍不充分。本文通过真实应用的实证研究填补这一空白，考察性能干扰的端到端影响，分析有害干扰的根因，并总结潜在的实现陷阱。

为自动开展分析，我们提出 TimeTrap，从控制结果的角度研究自主系统中的性能干扰。为了理解时序干扰在多大程度上造成控制偏差，TimeTrap 有策略地利用不同强度的资源竞争，触发特定的截止时间违约模式。研究发现，简单地通过性能干扰最大化任务延迟，可能由于内置故障安全保护而无法触发最坏结果，即物理损害。因此，需要以不触发保护的方式引入延迟。

为此，TimeTrap 首先主动向目标软件注入细粒度延迟，并依据测量反馈调整持续时间；随后利用 CPS 执行模式和资源使用的可预测性，自动调节干扰负载，使其匹配目标模式，在受扰任务中造成预期的执行延迟。我们在两个真实物理平台和六个硬件在环平台上评价 TimeTrap，覆盖机械臂、无人地面车、无人机、自动驾驶汽车和人形机器人。研究表明，从感知到规划和控制，CPS 流水线的多个阶段都存在基于性能干扰的攻击面。

## I．引言

多核架构能在嵌入式平台的尺寸、重量和功耗（SWaP）约束下有效增加计算资源。但实时 CPS 强调时序可预测性，并发任务竞争共享资源引发的性能干扰越来越值得关注。这种干扰会延迟现代 CPS 处理流水线中的数据传播，进而降低性能。

### 已有研究

理解性能干扰的影响，需要同时分析干扰的来源、特征以及控制后果。Arm 提出的工业挑战[1]也强调了这一需求。相关研究大致分为三类：第一类只考察最坏性能干扰[2]–[12]，未继续分析软件与系统行为；第二类研究延迟在执行流水线中的传播[13]–[19]，主要采用调度视角，往往未评价控制结果；第三类抽象建模单个任务中不同截止时间违约模式造成的控制退化[20]–[23]，却未充分考虑多个任务的级联效应。

为了将软件属性、实时属性与控制属性联系起来[24]，本文实证研究不同 CPS 平台中性能干扰的表现，以揭示现实物理安全风险。

### 真实 CPS 软件时序问题的系统化分析

为建立合适的时序问题抽象，我们分析了八个知名 CPS 应用中的 241 个真实时序相关缺陷。它们常源于时序语义规定不充分或执行不到位。并非所有时序缺陷都会产生不良物理控制结果；本文用“时序问题”特指会产生这种后果的缺陷。

这些分析使我们将性能干扰的影响概括为：CPS 过程中的某些关键状态变量发生了时间偏移，详见第二节。

### TimeTrap 的技术挑战与解决方案

TimeTrap 通过对抗性干扰最大化控制偏差，即物理结果的差异，刻画性能干扰的最坏端到端影响。但直接耗尽系统资源常被内置安全检查化解。因此，需要识别应延迟哪些任务，才能造成显著控制偏差。

延迟量同样难以确定：太小不足以破坏安全条件，太大则可能触发故障安全保护。TimeTrap 借鉴软件故障注入方法[25]，主动注入延迟，寻找可利用的执行时序模式；还通过程序分析与插桩自动确定合适的注入位置和延迟量。

即便找到这类模式，还必须验证它能否由实际性能干扰产生。不同干扰方式[4]、[8]、[26]–[32]具有不同触发机制和效果，且效果高度依赖受扰线程的资源使用方式。TimeTrap 利用不同执行阶段对不同资源竞争通道的敏感性差异，对策略参数化并调整强度，在目标阶段制造所需延迟。

### 实验与结果

TimeTrap 可作用于感知、定位、规划和控制组件。本文在自主汽车、无人机和人形机器人等平台上开展硬件在环实验，并在 OpenManipulator 机械臂[33]和 Turtlebot3 室内机器人[34]上实测。结果表明，高 CPU 带宽、高优先级的直接拒绝服务（DoS）不一定造成有害物理结果，而 TimeTrap 能构造触发特定时序模式的负载。

本文贡献如下：

1. 系统梳理多个真实自主系统的时序缺陷，包括根因、表现和修复策略。
2. 实证研究性能干扰如何触发缺陷并影响控制，将根因表述为安全关键计算所使用的部分关键数据发生时间偏移。
3. 提出自动发现显著控制退化时序问题并合成对应干扰负载的 TimeTrap。在八个自主系统中，两个采用实物实验、六个采用硬件在环，覆盖感知、定位、规划和控制。

项目材料：https://github.com/WUSTL-CSPL/TimeTrap ；https://timetrap-rtas.github.io/ 。

> 译注：原文“Experiments and Results”一段提及八个平台的硬件在环实验，后又描述两个实物系统；摘要与贡献列表则概括为八个平台、两个实物及六个硬件在环。这里保留表述差异，平台与实验方式应结合表 III 理解。

## II．真实问题的系统化分析与时间偏移

本节先以 ORB-SLAM 为例剖析真实时序问题，再解释时间偏移，最后系统分析实际软件开发中的相关问题。

### A．剖析时序问题：时间偏移

ORB-SLAM[35]、[36]是自动驾驶应用[37]常用的定位流水线。它从视频流提取特征和地标描述，将其与地图库中已保存的描述匹配，估计车辆位置。为避免代价高昂的穷举搜索，它利用基于 IMU 的运动模型缩小搜索范围，因此需要组合 IMU 数据与相机图像。系统也会定期更新地图，以反映环境变化。

图 1 展示三个主要跟踪器及各自数据流。原本应在预期时刻可用的惯性数据 IMUₖ₊₁ 因干扰而延迟，既影响惯性跟踪器，也影响数据融合。前者的运动预测不确定性增加；更严重的是，地标跟踪器可能使用时间上未对齐的惯性数据，导致当前地标与地图匹配失败，使定位跟踪丢失。

这一数据使用错误可概括为时间偏移：

\[
\delta=T_{\mathrm{actual}}-T_{\mathrm{expected}}.
\]

即实际更新时间与预期更新时间之差。时间偏移实际上一直存在，内置系统机制的作用是尽量减小它。

**图 1 中文说明：** 惯性、地图与地标跟踪器分别沿时间线更新；延迟的 IMU 数据既影响单一跟踪器，也影响融合过程。[原页图像](./source_pages/page_03.png)

#### 软件中的时序问题示例

即使自主系统已检查并处理异常时序，也不代表一定能够保证正确时序。

一种直接做法是检查数据年龄并据此处理，但复杂时序行为需要精细条件检查。许多编程语言缺乏时序语义，无法完整表达程序员意图。图 2(a)中的 ORB-SLAM2 代码提取两个图像帧之间的 IMU 数据：丢弃早于上一图像的样本，收集时间戳位于前后两帧之间的样本，遇到更晚样本则停止。

若 IMU 与相机采样率分别为 \(R_i\)、\(R_c\)，通常 \(R_i>R_c\)，两帧之间理想上应有约 \(R_i/R_c\) 个 IMU 样本。但该代码没有检测样本缺失。时间戳即使有效，数据缺失仍会造成错误。

图 2(b)中，地标跟踪器检查距上次地图更新是否已超过 0.5 秒，若超过则设置标志触发地图更新。在资源充足时，另一线程中的 `BAOptimization()` 应立即执行。但系统开销增大时，CPU 调度器不知道应用内含的时序要求，函数未必及时运行。

**图 2 图注：** ORB-SLAM2 的简化代码。(a) 对图像帧间 IMU 数据的时间戳检查；(b) 用户态应用规定的时序策略。[原代码及图像](./source_pages/page_03.png)

### B．真实应用中的时间偏移

我们检查了 GitHub 上较流行 CPS 项目的时序相关 issue 和 pull request，覆盖感知、规划、控制等组件：Autoware.Auto[38]、MoveIt[39]、Google Cartographer[40]、Baidu Apollo[41]、ORB-SLAM2/3[42]、[43]、ROS-Planning Navigation[44]及 ROS2 rcl 中间件[45]。我们人工核查讨论并排除误报。应用的代表性及人工检查方法构成研究有效性的潜在威胁。

**表 I：不同 GitHub 项目的时序问题分析**

| 项目 | 代码量 | 类别 | 总 issue/PR 数 | 时序相关数 | I 类 | II 类 | III 类 |
|---|---:|---|---:|---:|---:|---:|---:|
| Autoware |101k|全栈|1243|17|3|5|2|
| MoveIt |143k|控制*|2740|27|4|11|9|
| Cartographer |60k|定位|1953|43|10|16|10|
| Apollo |571k|全栈|15251|55|12|23|12|
| ORB-SLAM2/3 |69k|定位|1064|12|8|—|6|
| Navigation |120k|控制*|3352|22|2|6|1|
| ROS2 rcl |149k|中间件|2066|65|5|2|37|

全栈包括感知、定位、规划和控制；控制*包括任务规划、运动规划和控制器。

> 译注：数字按原表保留，不能未经核实就将分类列解释为互斥且必然与时序总数相加一致。

#### 普遍程度

各项目在开发中均遭遇若干至数十个时序问题，约占总体缺陷的 0.5%–2%。issue 数量不直接代表项目质量，它还受项目流行程度及开发活跃度影响。以下讨论基于这 241 个问题的分析与部分复现。

#### 当前时序约束实践

实践中可分为控制流中心与数据流中心两类。前者从程序执行出发，通过截止时间、周期、锁协议等规定约束；后者将时间信息与数据绑定，并用于决定软件行为。例如 ROS 消息附带时间戳，开发者检查新鲜度或时间对齐后决定如何处理。

除 ROS2 rcl 外，用户态应用更偏好数据流中心方式，69.3%的问题与之有关。原因是无需修改底层调度基础设施，且能更直接反映任务依赖，便于推理复杂任务链中的约束。

#### 根本原因

- **I 类：** 时序约束缺失，或仅被默认成立而未有效执行，占 23.9%。任务执行时刻变化即可造成时间偏移。
- **II 类：** 已规定约束但不完整，占 34.2%。只允许部分数据或一定阈值内的时间偏移。
- **III 类：** 约束已完整定义但执行无效，占 41.8%，常因调度器等执行器缺陷或其协调不当。

许多 I 类问题源于数据缺少时间戳等信息。虽然 ROS API 提供时间戳接口，开发者仍常未将它沿较长处理链传递，多个传感流在同一组件融合时更严重。

II 类问题源于准确表达不同场景时序语义的困难，包括取值范围不精确、检查到使用之间的时间差（TOCTOU）问题，例如 Apollo #14461 中检查过早；也包括时间戳粒度不足，如 Cartographer #600。触发此类问题需要在特定执行阶段产生精确延迟。

III 类多见于 ROS2 中间件调度实现，常涉及竞争条件（rclcpp #2012）及定时器等多个调度实体（rclpy #1016）。时序工具自身也可能出错，如不同时钟系统的时间格式不兼容（rcl #947）。

#### 表现

这些问题与传统并发缺陷[46]都可能由异常时序触发，因而难以区分。本文关注算法语义与控制性能；并发缺陷的一般症状已有充分研究。

时序问题不一定使控制输出变迟，因为执行器命令往往由另一未受影响的任务发送。但它常导致错误使用数据，以过期数据为主，偶尔也使用过早数据。消费不同传感器或组件的数据时会产生失同步；不等间隔更新还会造成抖动，例如 Cartographer #242。超过 30%的问题涉及失同步，反映多线程推理的复杂性。大部分问题涉及进程内或跨进程的两三个线程，延迟其中一部分就会改变执行关系。

多数问题生成错误计算结果，继而破坏物理控制稳定性；少于5%导致软件无响应，少于10%导致崩溃。失同步与抖动更隐蔽，常引起控制退化。相比之下，程序员更容易在顺序处理情境中注意到端到端数据年龄并进行补偿。

复现还显示，机器人软件往往能滤除偶发中间错误，连续异常时序才会传播到最终任务输出。

**认识：** 发现这类问题需要只延迟部分线程，制造异常执行顺序；连续注入有助于错误传播至最终控制结果。

#### 缓解策略

241 个问题中已有141个（58.5%）在代码库修复。修复通常通过保证正确执行时序，或改变异常时序处理。前者多采用增加或修改互斥锁等同步原语，很少修改底层调度器、定时器。但加锁可能增加实时开销或引入锁顺序反转，例如 rcl #1121。

超过80%的相关修复采用数据流中心方式：向数据结构补充时间戳，再加入异常时序检测和处理。常见方法包括终止任务实例（如 ROS 回调），并触发运行安全／故障安全动作（如速度置零）；或通过预测模型近似缺失的正确数据。这些机制也给 TimeTrap 带来第四节讨论的挑战。

**认识：** 除传统截止时间、周期等调度约束外，开发者也常通过异常时序检测和情境专用处理，避免不良控制后果。

## III．系统模型

本文面向同时支持事件触发（例如数据驱动）和时间触发（例如周期执行）的实时系统，第六节平台均原生支持这些机制。考虑的干扰行为满足：

1. 干扰负载与目标应用运行在同一计算平台。
2. 干扰任务优先级低于系统所有其他任务，不能直接修改任何任务（包括自身）的优先级或 CPU 亲和性。
3. 干扰负载处于非特权级，不能访问其他任务地址空间。

## IV．TimeTrap 设计

### 概述

TimeTrap 的目标是发现时序问题，并生成干扰负载以验证问题能被实际触发。工作流见图3。

**第一步：发现可利用时间偏移（IV-A）。** 并非所有偏移都触发缺陷，也并非所有缺陷都严重影响控制。借鉴并发缺陷发现研究[47]，注入延迟、观察中间变量与控制行为；物理影响明显的模式被视为可利用模式。

**第二步：执行阶段划分与干扰分析（IV-B）。** 画像目标负载资源使用和竞争敏感性。为精细控制延迟，将执行划成具有不同资源使用特征的阶段，并测量各干扰原语对其时序的影响。

**第三步：生成干扰负载（IV-C）。** 结合可利用偏移与敏感性分析，将生成过程写成优化问题，在实现目标任务预期延迟的同时，减小对不相关共运行任务的影响。

**图3 图注：** TimeTrap 工作流：目标软件与测试平台→可利用时间偏移发现→任务执行阶段划分及干扰分析→干扰负载生成→攻击程序；中间输出包括可利用条件、敏感性与不确定性。[原图](./source_pages/page_05.png)

### A．发现可利用条件

#### 挑战

要产生时间偏移，必须选择性延迟某些线程，尽量不影响其他线程。所有任务一起变慢，常只造成端到端延迟，内置终止或预测机制可能处理它。TimeTrap 要制造特定数据失同步或抖动，避免这些保护化解影响。

#### 通过延迟注入控制执行时序

遵循软件故障注入原则[25]，在不同位置注入延迟，探索导致错误控制输出的执行模式。关键问题是：哪些代码位置适合注入，以及注入多少延迟。

#### 在哪里注入？

可选方法有：操作系统层操纵调度、运行库层拦截调用、编译期变换直接改写源码。前两者无需源码，但调度层缺少数据依赖等语义；库调用可保留发送者／接收者语义，却依赖具体实现，无法覆盖不通过 API 的共享变量通信。

因此 TimeTrap 在源码层注入。编译时静态识别访问任务间共享数据的区域，共享可能是进程内内存或跨进程消息。进程内使用指向分析[48]，跨进程使用字符串匹配。该分析直接报告位置，不检查其上下文。每个注入点与其他访问同一共享数据的位置配对，每对至少一处为写操作。

系统进行 A/B 测试：在目标平台回放相同数据，一次注入延迟、一次不注入，再比较中间或最终控制结果。结果由插桩或原生日志记录，差异程度衡量延迟影响。每对点选择一个在运行时注入。一次运行注入一个或多个延迟存在权衡；若能观察中间结果并区分各点贡献，可在一轮运行中注入多个点。

#### 延迟多少？

由于控制错误常需连续异常时序才显现，一次性注入的传统并发缺陷方法[47]不合适。TimeTrap 在整个任务过程中持续注入相同执行模式，模式由代码位置、延迟／抖动类型和幅度三个因素表示。

弱硬实时任务模型[49]、[50]不适合本文场景：它只计截止时间命中／违约次数，不表示延迟幅度，而应用常有新鲜度阈值；共享数据也不一定在截止时刻才更新，因此违约未必影响依赖任务的数据消费。

为确定有效延迟范围，在同一点由大到小调整注入量，每次观察中间结果和最终控制。若触发故障安全动作，就减小延迟；若中间结果显著变化而最终控制不变，说明下游对该问题鲁棒，该点被移出候选；预设范围探索完仍无效也移除。能产生不良物理后果的执行模式被记录，供后续使用。

### B．面向资源的执行画像

#### 挑战

真实性能干扰要只影响部分任务，并把延迟限制在特定范围内。为此利用任务资源使用及干扰通道敏感性的差异。

#### 面向资源的任务执行阶段

例如运动规划通常执行缓存密集的优化，而传感驱动更依赖 I/O；单一任务内部资源使用也随时间改变。借鉴[51]，先精细画像，再划分为各自集中使用相似资源的阶段。按所需粒度，每阶段可含数千至数万条指令。

随后测量阶段对各竞争通道的敏感性：画像时将受扰阶段放在指定核心，将干扰任务放在其他核心，测量阶段延迟。该分析有三项益处：聚焦最耗资源阶段，以较小 CPU 预算在恰当阶段触发延迟；分离通道以选择性影响线程；每阶段只针对一种通道，缩小优化搜索空间。

**图4 图注：** 任务资源竞争敏感性画像。将任务分为若干阶段，检查缓存、DRAM、网络I/O和磁盘I/O；建立干扰强度与延迟倍数之间的敏感性曲线。[原图](./source_pages/page_06.png)

#### 干扰通道敏感性

干扰必须足以破坏算法结果，又不能过大而触发保护。性能干扰可参数化[9]，例如调整内存访问步长改变竞争强度。逐级增加强度，记录任务延迟，插值得到敏感性曲线[52]，用于预测给定强度的延迟。还分析不同任务对齐方式带来的集体资源使用差异。

局限在于参数与延迟的关系非线性，不同通道也可能相互依赖，预测因此会有误差；提高敏感性分析精度可缓解。

### C．生成干扰负载

根据可利用时序模式与敏感性，将生成负载建模为优化问题。目标系统有 \(K\) 个任务：

\[
T=\{\tau_1,\tau_2,\ldots,\tau_K\},
\]

其中 \(\tau_v\) 为受扰任务。每个任务有执行阶段 \(\{p_1,p_2,\ldots,p_n\}\)。针对每阶段 \(p_i\) 设计策略 \(A_{p_i}=\{R_{p_i},I_{p_i}\}\)，优化资源通道 \(R\) 和强度 \(I\)。策略造成各任务延迟 \(D=\{t_1,t_2,\ldots,t_K\}\)，由第二步的敏感性画像推断。

用映射 \(S\) 将策略 \(A\) 与系统执行阶段 \(p_{sys}\) 联系到各任务延迟的概率表示：

\[
S(A,p_{sys})\rightarrow D,\qquad D=\{d_{\tau_1},d_{\tau_2},\ldots,d_{\tau_K}\}.\tag{1}
\]

其中 \(d_{\tau_i}\) 是含不同概率下延迟的向量。目标是增大受扰任务延迟、减小其他任务延迟；选择性延迟不同调用还可引入抖动。受扰延迟也须处于 IV-A 得到的合适范围，避免触发保护。原文优化式为：

\[
A^*=\arg\max_A\sum_{i=1}^{K}(d_{\tau_v}-d_{\tau_i})^2,
\]
\[
\text{s.t.}\quad d^{min}_{\tau_v}\le d_{\tau_v}<d^{max}_{\tau_v};\quad
d_{\tau_i}<d^{max}_{\tau_i},\ i\ne v.\tag{2}
\]

> 译注：原文先将 \(d_{\tau_i}\) 介绍为概率下延迟向量，后在式(2)中直接使用平方差与不等式；这里忠实保留，并未替作者补充范数、期望或逐元素运算定义。公式可对照原页。

虽然公式只表示一个受扰任务，实际数量依平台变化。Apollo、Autoware 等复杂自动驾驶系统可能需要延迟多达三个任务，无人机通常只需一个。

## V．TimeTrap 实现

本节说明 OpenManipulator X、Turtlebot3 等 Linux 系统上的实现。不同平台需针对具体资源与执行阶段定制，但基本构建方式一致。

### 发现可利用条件

延迟注入组件由编译期插桩器和运行时系统组成。插桩器以 LLVM-13[54]编译器 pass 实现。对于主要使用 ROS 的进程间通信，将 `publish()` 等函数识别为注入点；对于更细的线程间共享变量，将 SVF 指向分析工具[48]集成到 pass。识别点位后，在每个点位之前插入延迟函数。

运行时系统动态设置睡眠时长，减弱自然运行变化，使执行模式更确定。延迟函数由 POSIX `usleep()` 改造，使注入点等待至指定时刻。Python 脚本计算各任务输出与期望值的偏差，衡量控制性能；运行时依据反馈调整延迟量或移除候选点对。

### 性能干扰敏感性分析

资源画像使用 Linux `perf` 子系统，通过硬件性能计数器监测缓存未命中等事件。相关事件数量反映特定资源使用强度。为减小计数器数量有限、复用计数器带来的误差[55]，多次运行并对齐结果，每轮捕获与物理计数器数量相同的事件。

基于 PolyRhythm[9]实现八类资源竞争原语：缓存、行缓冲、TLB、内存总线等体系结构通道，以及网络I/O、磁盘I/O、文件系统和线程创建等操作系统通道。调节对应参数，可产生不同强度的干扰。

## VI．评价

本节首先给出三个案例，其中两个在真实机器人上评价（VI-A）；其次分析干扰策略、合成流程以及资源通道、优先级和 CPU 预算的影响（VI-B）；最后考察不同 CPS 平台上的适用性（VI-C）。

### A．案例研究

以下介绍三个平台，另外五个平台的材料见项目网站。

#### 案例 I：机械臂

实验采用 OpenManipulator X[33]及工业与学术界广泛使用的 MoveIt[39]软件栈，其应用包括 NASA、Intel 等[56]–[61]。Raspberry Pi 3B 承担计算，Pi Camera M2 提供感知。任务是识别并抓取饮料罐。

**干扰方法。** MoveIt 控制任务在 Linux `SCHED_RR` 类中使用优先级80，TimeTrap 为20。合成流程发现：受扰任务的释放时刻出现差异时，机械臂行为异常。因此在任务预定释放前对缓存资源施加竞争，制造抖动。

**结果。** 正常情况下，机械臂依次识别、接近、抓取饮料罐并运至指定位置。TimeTrap 下机械臂偏离路径，撞到桌面，使罐子掉落。计划位置与力矩等中间变量出现异常尖峰。图5(c)为了显示清晰，将正常曲线在横轴上略作平移。

**根因：用户态实现的定时器。** 进一步检查发现中间值异常来自数据竞争。任务分多个阶段，每阶段激活一个回调线程，利用部分路点求解运动路径。若两个任务同时生成轨迹，求解器可能同时处理两组不同路点而输出错误。正常情况下，定时器间隔为数秒、计算仅需数十毫秒，竞争很少发生；但 MoveIt 使用的 ROS 定时器在用户态实现，容易受干扰。

ROS 定时器到期后先将事件加入队列，再交给可用线程。内核 `hrtimer` 路径很短，较能抵御干扰；POSIX 定时器由于用户态语义，释放可被活动任务干扰延迟约800毫秒；ROS 定时器抖动甚至超过2秒。这可能使原本分开的子任务同时触发。用户态定时器虽灵活易用，在落实时序约束方面却存在缺陷。

**图5 图注：** 机械臂案例。(a)正常抓取与撞桌实验；(b)不同定时器抖动；(c)控制偏离；(d)ROS定时器、回调队列及轨迹数据竞争的根因分析。[原图](./source_pages/page_08.png)

#### 案例 II：Turtlebot3

平台是配有 LDS-01 激光雷达与 IMU 的 Turtlebot3 Burger 室内服务机器人，使用自适应蒙特卡洛定位（AMCL）和 ROS Navigation[44]。办公场景中，它持续向另一台计算机上的地面控制站（GCS）发送位置与任务信息，GCS定期发送轨迹数据引导运动。

**干扰方法。** 同样采用 Linux 实时 RR，干扰任务优先级低于所有受扰任务。合成流程识别出的目标线程负责生成运动规划所需地图。

**结果。** 机器人每轮控制取得点云，与已有地图匹配定位；点云同时用于生成带障碍信息的代价地图。TimeTrap 使路径规划使用时间不匹配的代价地图而产生错误路径，最终碰撞。

**根因：不恰当的时间戳检查。** Navigation 有全局任务规划器和实时局部规划器。局部规划需要位姿与含静态、动态障碍物的代价地图；两者必须时间对齐，才能正确表示障碍位置。它们由不同线程更新，易出现时间偏移。

系统虽在全局规划器更新时检查代价地图新鲜度，但在同时使用位姿和代价地图时，没有检查二者的时间对齐。图6(b)的保护代码会在观测过期时告警并发布零速度；然而未覆盖上述失配。图6(a)中，机器人认为红色路径畅通，但真实世界中的蓝色轨迹撞向墙面。示例时间偏移为0.76秒。

**图6 图注：** Turtlebot3案例。(a)生成的代价地图与路径，红色为时间偏移下规划的路径，蓝色为物理世界轨迹；(b)检查观测缓冲是否为最新、否则发布零速度的保护代码。[原图与代码](./source_pages/page_08.png)

#### 案例 III：无人机

自建四旋翼采用 Raspberry Pi 3 Model B 与 Navio2，运行 Ardupilot[62] Copter-4.0。通过另一台主机的 Mavlink 消息分配任务。图7左上显示 TimeTrap 使无人机坠毁。

为收集详细数据，也采用仿真。Ardupilot 原生仅支持软件在环，物理仿真与控制任务位于同一周期循环中，因此插入延迟会转化为整个仿真的端到端变慢，不影响控制。概念验证中，我们将传感数据仿真移至独立任务，以接近真实飞行中传感器由不同任务读取的结构。

**方法与结果。** Ardupilot 任务分为I/O和控制。传感驱动、执行输出、远程消息各有优先级80的独立线程；处理传感数据与计算控制输出的任务集中在优先级60的线程，由内置用户态调度器执行。干扰线程优先级最低，为20。

任务设11个路点，TimeTrap 在一个急转弯路点启动。此前速度稳定，之后无人机失稳、坠毁；图7给出相对参考速度的偏差。

**根因：用户态调度器。** 控制任务集中于一个线程、传感任务独立。用户态调度高效灵活，却难以保证时序约束：内核不知道用户态优先级，内核线程切换也不会被用户态调度器正确计入。控制循环因此与传感数据循环失同步，速度明显振荡。TimeTrap 并非无差别阻塞全部线程的简单 DoS；软件本来能够承受一定频率下降，全部一起变慢时对控制的影响反而可能有限。

**图7 图注：** Ardupilot无人机案例：起飞、偏离、坠毁，以及传感任务与控制任务的优先级、截止时间和时间偏移关系。[原图](./source_pages/page_09.png)

### B．TimeTrap 有效性

实验评价策略及合成流程的必要性，并分析资源通道、实时优先级和预算。

#### 直接 DoS 并不有效

以耗尽缓存资源的直接 DoS[4]作比较。实验将 Turtlebot 放入 WashU Mini-City，一个约3000平方英尺、比例1:8、含街道、建筑、车辆与行人的城市模型。干扰任务使用80% CPU带宽和优先级40，明显拖慢其他任务；但机器人没有撞楼，而是检测到传感输入过度延迟后停车。Turtlebot3 实现七类保护条件，图6(b)为其中之一。

机械臂在直接 DoS 下控制偏差仅3.78厘米，TimeTrap 在图8(d)中可达30.1厘米，因为直接 DoS 未破坏此前案例中的定时器行为。另一组直接DoS保持优先级40但仅用20% CPU带宽：Turtlebot3因控制输出频率降低而减速，但仍沿原路径；机械臂时间偏移为0.23秒、控制偏差1.23厘米。

**图8 图注：** 控制偏差随资源通道、优先级、CPU预算变化。(a)磁盘I/O；(b)网络I/O；(c)缓存；(d)多资源组合。各图图例一致，T.D.指时间偏移。[原图](./source_pages/page_10.png)

**图9 图注：** 真实Turtlebot3上的直接DoS与TimeTrap比较，展示感知地图与运动轨迹。[原图](./source_pages/page_10.png)

#### 影响因素

分别针对缓存、网络与磁盘I/O优化单通道原语，并与多资源组合比较。CPU带宽设五档，范围1%–20%；优先级设低、较低、中、较高、高五档。“低”低于所有现有任务，“较低”与现有最低优先级相同，其余依次升高。平台是以 Raspberry Pi 3B 为计算单元的机械臂。

磁盘I/O与缓存比网络更有力，原因是该系统网络传输很少。SD卡机器人易受磁盘I/O干扰，SSD系统影响较小。缓存干扰高度依赖CPU预算，更多CPU时间意味着更多缓存驱逐。网络和I/O由专用硬件控制器处理，需较少CPU，但能造成的时间偏移也较有限。多资源组合能综合单通道优势；CPU带宽提高后，优先级影响更明显。

#### 不同物理场景

设置十个任务，其中一半为动态场景。机械臂随机放置两个边长3.5厘米的立方体作为目标；Turtlebot在含不同障碍物的十条随机室内轨迹中运动。每项任务评价十次。表II显示感知阶段CPU开销很小，静态和动态成功率均超过60%；动态场景要求更强时效性，成功率总体更高。

**表II：静态与动态场景中的 TimeTrap**

| 平台 | 方法 | 场景 | 感知开销% | 时间偏移s | 控制偏差cm | 成功率 |
|---|---|---|---:|---:|---:|---:|
|机械臂|TimeTrap|静态|0.18|1.6|22.1|72%|
|机械臂|TimeTrap|动态|0.22|1.9|25.7|86%|
|机械臂|直接DoS|合并|—|5.3|1.78|0%|
|Turtlebot3|TimeTrap|静态|0.19|0.93|13.2|61%|
|Turtlebot3|TimeTrap|动态|0.32|0.81|14.5|81%|
|Turtlebot3|直接DoS|合并|—|3.5|6.3|24%|

直接DoS静态／动态结果按原文合并；该对照中干扰任务具有较高优先级并占80%CPU。虽然造成较大延迟，控制偏离仍有限。

> 译注：表II与图8属于不同实验，不应混用其中数值。

### C．泛化性

除上述三个案例，本文共测试 OpenManipulator X、Turtlebot3、Jackal UGV、Ardupilot、PX4、ROBOTIS OP3、Autoware.Auto 和 Baidu Apollo 八个平台。表III列出官方及实验平台、软件、调度与脆弱模块。采用真实环境或官方仿真以保证实用性。

**表III：平台与脆弱模块**

| 名称 | 类型 | 软件栈 | 官方计算平台 | 实验计算平台 | 测试调度 | 问题数：感知/定位/规划/控制 | 直接DoS | TimeTrap |
|---|---|---|---|---|---|---|---|---|
|Turtlebot3†|UGV|Navigation|Raspberry Pi 4b|Raspberry Pi 4b|CFS/RR/EDF＋ROS|—/2/2/—|—|✓|
|Jackal|UGV|Cartographer|Intel i3-4330TE|Intel i3-8100|CFS/RR/EDF＋ROS|—/3/—/—|—|✓|
|Ardupilot|无人机|Ardupilot|Navio2（RPi3）|Navio2（RPi3b）|内置调度|—/—/—/1|✓|✓|
|PX4|无人机|PX4 Autopilot|Pixhawk|Pixhawk|Nuttx|—/—/—/1|—|✓*|
|Apollo|自动驾驶车|Apollo全栈|Neousys 6108GC|Ryzen7 1700X|CFS＋CyberRT|1/2/1/—|—|✓|
|Autoware|自动驾驶车|Autoware全栈|8核CPU|Ryzen7 1700X|CFS＋ROS2|1/3/1/1|—|✓|
|OP3|人形机器人|OP3 controllers|Intel i3双核|Jetson Nano|CFS/RR/EDF＋ROS|—/—/—/2|—|✓|
|OpenM. X†|机械臂|MoveIt|RPi3b|RPi3b|CFS/RR/EDF＋ROS|—/—/1/1|—|✓|

†为真实物理评价，*为远程方式；RAM亦按官方要求设置。空白表示原表未列问题或成功标记，不代表不存在问题。[原表](./source_pages/page_12.png)

> 译注：正文机械臂案例写优先级80、表述较早段落使用RPi3B；泛化实验的RR统一设目标60、干扰20。Turtlebot案例与表III也出现平台描述差异。应分别按对应实验理解，不能自行合并成唯一配置。

#### 调度机制配置

PX4使用Nuttx实时操作系统，其余运行Linux。Autoware与Apollo分别集成ROS2与Cyber-RT。默认CFS的平台加入PREEMPT_RT补丁后，也在Linux RR与EDF下测试。RR中目标优先级60（最高99），干扰为20；任务周期按输入确定。EDF截止时间与传感输入频率对齐，保证没有输入丢弃。

#### 单核资源竞争较弱

单核平台也有可被干扰任务污染的共享有状态资源，但延迟效果有限。基于单核Cortex-M7的Pixhawk PX4没有因资源竞争坠毁。不过我们发现可远程触发的优先级继承问题，见第七节。

#### 触发条件

直接DoS往往不能保证碰撞／坠毁，无人机因飞行特性构成例外。其一，直接DoS需要很大CPU预算才形成时间偏移；其二，关键组件大延迟会触发保护。TimeTrap若选准时刻，小幅时序变化也可能造成严重控制退化。

第二节的多数时序问题并不能通过性能干扰可预测地触发，但仍可能由负载变化[67]、系统或硬件故障[68]触发。TimeTrap第一阶段的时间偏移发现仍能识别它们。

#### 多个流水线模块均脆弱

表III报告识别出的问题数量。定位模块更易出现问题，因为它常涉及更多线程，并发正确性更难推理。我们检查了各平台易受影响的软件模式与调度机制。

#### 多核内置调度缓解有限

原因之一是ROS2、Cyber-RT等数据驱动中间件未将资源分区纳入设计；另一原因是Nuttx等实时调度机制主要考虑CPU使用，而网络、I/O等栈中的资源竞争或阻塞同样可能造成时间偏移[9]。

#### 静态时序策略不足

复杂自主系统主要使用静态优先级和硬编码新鲜度阈值，某些场景中阈值过宽。任务执行时序因输入等因素显著变化[69]、[70]，与动态环境交互的自主系统需要自适应动态时序策略[69]、[71]。

## VII．局限与讨论

### 结果依赖物理环境

CPS攻击的独特性在于运动后果。后果取决于物理状态：地面静止无人机遭DoS，实际影响可能很小；物理断开的发电系统被注入假数据也可能无后果。尽管TimeTrap结果受物理状态强烈影响，本文研究显示它能持续破坏目标CPS；失稳所需时间不同，有时需数秒。

### 远程执行 TimeTrap

除本地性能干扰、攻击电压配置[72]外，也探索网络环境中的时序影响。向PX4发送特定地面站消息，可引起优先级反转并延迟任务。

PX4日志I/O开销较大，因此平时由低优先级线程（`SCHED_PRIORITY_DEFAULT - 40`）异步处理，并通过 `_log_interval` 限速，避免短时突发。但地面站Mavlink消息由高优先级线程处理，其中日志请求处理函数 `MavlinkLogHandler()` 也继承高优先级。重复日志请求可使无人机偏离任务路径或坠毁。

问题在于Mavlink处理器调用函数时保留高优先级，使日志功能不恰当地继承。缓解方法是为该函数指定独立优先级，例如将优先级随请求传播[73]。

本文多数时序违规假设本地进程感知并产生干扰；该案例表明，远程暴露API也可能调用出干扰负载。

**图10 图注：** PX4远程恶意请求；绿色为任务航线，红色为实际航线，标记请求启动点与路点。[原图](./source_pages/page_12.png)

## VIII．相关工作

### 基于性能干扰的拒绝服务

过去二十年广泛研究共享资源DoS，主要刻画最大干扰或减速。通道包括缓存[4]、[12]、[26]、[27]、[74]、[75]、行缓冲[27]、内存总线[30]、网络栈[28]、I/O[29]、GPU[10]，也有多通道组合[8]、[9]、[11]、[76]。TimeTrap基于这些工作，进一步合成适当负载以触发时序问题，而不是只最大化干扰。

### 实时软件的时序安全

输入／输出抖动导致控制退化已有研究[77]–[79]；智能电网同步攻击[80]通过伪造GPS时间戳使相量测量单元失同步；蝴蝶攻击[81]假设存在可由恶意输入触发的软件特性，以增大控制抖动并导致失稳，[24]、[82]讨论缓解。

这些工作主要讨论时序与控制模型的关系，较少涉及软件实现。本文进一步分析内部软件实现导致的时序问题。[83]研究增强现实应用的控制性能，与之类似，但TimeTrap覆盖自主系统全栈。

## IX．结论

本文实证研究共享资源性能干扰如何触发有害任务违约模式，并使CPS控制性能退化。分析多个自主平台，将原因归结为关键数据时间偏移。

为自动化分析，提出TimeTrap以研究目标平台性能干扰的端到端影响。它识别由软件实现缺陷引起的有害执行模式，并合成负载触发这些模式。八个真实或仿真自主系统的实验表明，方法适用于多种控制流水线阶段。

## 致谢

感谢审稿人的反馈。本工作获得美国NSF项目CNS-1916926、CNS-1932530、CNS-2038995、CNS-2154930、CNS-2141256、CNS-2238635、CPS-2229290，ARO项目W911NF2010141，以及圣路易斯华盛顿大学和Intel的部分支持。

## 补充案例研究

本部分通过硬件在环案例进一步说明TimeTrap如何造成时间偏移及控制偏差。

### 案例 IV：Autoware.Auto

Autoware.Auto[66]是用于自动驾驶研究开发的开源全栈，含检测、定位、规划、控制并支持不同场景。使用1.0.0版本，按官方8核、32GB建议在AMD Ryzen7 1700X、32GB RAM运行。车辆模型为Lexus 2016 RX Hybrid，场景是官方自主代客泊车[53]。LG-SVL[84]在另一台配RTX2070S的PC运行，通过以太网连接。

**结果。** 图11(b)为行驶路径，星号处启动TimeTrap并周期竞争资源。在之后路径中，两段出现明显时间偏移。第一段直行时没有明显控制偏差；第二段车辆完全失控并撞到相邻建筑。

**根因。** 定位模块错误估计车辆位置。Autoware.Auto使用正态分布变换（NDT）匹配[85]估计位姿；软件将其建成最大后验（MAP）优化问题，需要初值加快求解。

图11(a)中输出 `pose_out` 依赖 `initial_guess`；后者通过查询变换树（第65行）或外推（第71行）得到。这一推断默认 `tf_graph` 与 `target_frame` 同步。变换图更新延迟会在目标坐标系中产生时间偏移，使 `initial_guess` 错误；进一步使 `register_measurement()` 陷入局部极小，产生错误 `pose_out`。

图11(d)显示，两段的初值错误程度类似，第一段控制受影响较小。直行时相邻点云帧仍共享较多特征，即使初值不准，NDT也能收敛。图11(c)中第一段定位未偏离参考路径；第二段定位任意跳动。因此后果取决于受扰系统物理状态。非脆弱状态下，产生显著控制影响可能需要更多CPU预算或更高优先级。

**不同仿真世界。** 表IV报告多场景结果。

| 地图 | 场景 | 感知开销% | 时间偏移s | 控制偏差m | 成功率 |
|---|---|---:|---:|---:|---:|
|Parking Lot|静态|0.17|2.0|3.6|72%|
|Parking Lot|动态|0.21|2.3|3.9|56%|
|Borregas Avenue|静态|0.18|2.2|1.8|77%|
|Borregas Avenue|动态|0.36|2.3|1.7|61%|
|GoMentum Station|静态|0.17|2.3|2.4|65%|
|GoMentum Station|动态|0.25|1.9|2.2|52%|
|San Francisco|静态|0.19|2.7|4.8|74%|
|San Francisco|动态|0.34|2.3|5.4|58%|
|Shalun|静态|0.17|2.4|2.1|64%|
|Shalun|动态|0.23|2.9|2.6|51%|

动态场景感知误差较大：随机交通参与者会引起减速、停车等不确定事件，使TimeTrap感知更困难；过滤干扰也需更多时间。整体感知有效，最高开销0.36%CPU。Borregas Avenue地图较简单，控制影响最小，但即使最小1.7米偏差也足以撞上路缘。

**图11 图注：** Autoware.Auto案例。(a)时间偏移发生的代码；(b)全图与路径；(c)放大路径及高时间偏移片段；(d)`initial_guess`、`pose_out`与时间偏移的关系。[原图与代码](./source_pages/page_16.png)

**图12 图注：** Autoware.Auto硬件在环仿真的数字孪生环境：Parking Lot、Borregas Avenue、GoMentum Station、San Francisco、Shalun，均基于真实世界建模。[原图](./source_pages/page_16.png)

### 案例 V：ROBOTIS OP3 人形机器人

OP3[64]有20个活动关节，各配传感模块与控制模块。传感模块获取关节速度等状态，控制模块基于PID生成各关节力矩，协作完成握手、下蹲、站立、行走等动作。

软件栈运行于Nvidia Jetson Nano，Gazebo在另一PC模拟。预生成多项任务逐一发送；OP3接收后执行，忙时忽略新请求。TimeTrap在不同任务中随机启动。

**结果。** 多数动作下难以破坏稳定性，但行走等特定动作可被破坏，使机器人摔倒。图13(a)显示正常关节运动相似、周期稳定；干扰后部分关节异常，细小错误破坏协同。当CPU预算超过5%时可出现图13的后果。

**根因。** 每关节有串接的动作控制器和力矩控制器。前者计算该周期目标位置，后者结合目标与IMU传感估计计算舵机所需作用。由于输入来自上层控制器及惯性传感器两条来源，力矩控制器内部可出现时间偏移。

无干扰时时间偏移约0，关节协调稳定；干扰后偏移可增至30毫秒，力矩命令开始振荡。右踝关节位置异常破坏关节间协调，使机器人倒下。

**图13 图注：** OP3右踝俯仰控制器案例：关节动作、控制命令、右踝位置与时间偏移；虚线标示受干扰区间。[原图](./source_pages/page_17.png)

### 案例 VI：Jackal UGV

Jackal[65]为室内外均可工作的无人地面车。Gazebo模拟四轮车和SICK LMS111激光雷达，软件运行于Intel i3-8100。定位采用Google Cartographer[40]、[86]，控制采用纯追踪算法[87]。预先定义若干办公环境长路径，车辆跟踪参考路径。

**结果与根因。** 图14显示TimeTrap启动后车辆跟踪失败、撞上桌子，原因是定位错误。Cartographer有后台非周期优化任务，用于修正导航累计漂移，预期每处理十次激光扫描释放一次。

优化完成会调整定位值，令车辆估计位置短距离跳变。若任务按隐含预期频率执行（未指定明确截止时间），该变化通常在控制器容忍范围内。TimeTrap持续拖延优化任务，打破隐含截止时间；任务不能及时结束，工作量继续积累并反过来增加执行时间。最终定位跳变过大，控制器无法继续跟踪参考路径，车辆撞桌。

**图14 图注：** Jackal UGV案例：任务路径、实际行驶路径、起点、干扰启动点与撞桌结果。[原图](./source_pages/page_17.png)

## 原文脚注链接

- Apollo 时间检查案例：https://github.com/ApolloAuto/apollo/pull/14461/files
- Cartographer 时间粒度案例：https://github.com/cartographer-project/cartographer/issues/600
- ROS2 并发案例：https://github.com/ros2/rclcpp/issues/2012
- ROS2 定时器案例：https://github.com/ros2/rclpy/issues/1016
- ROS2 时钟格式案例：https://github.com/ros2/rcl/issues/947
- Cartographer 抖动案例：https://github.com/cartographer-project/cartographer/issues/242



## 参考文献（保留英文原文）

保留作者、英文题名、出处和原编号，便于检索；PDF文字层中的断行已合并。排版与拼写以原PDF第13–14页为准。

[1] M. Andreozzi, G. Gabrielli, B. V enu, and G. Travaglini, “Industrial challenge 2022: a high-performance real-time case study on arm,” in 34th Euromicro Conference on Real-Time Systems (ECRTS 2022) , 2022.

[2] K. Nagar and Y . Srikant, “Precise shared cache analysis using optimal interference placement,” in 2014 IEEE 19th Real-Time and Embedded Technology and Applications Symposium (RTAS) , pp. 125–134, IEEE, 2014.

[3] R. Pellizzoni, A. Schranzhofer, J.-J. Chen, M. Caccamo, and L. Thiele, “Worst case delay analysis for memory interference in multicore sys- tems,” in 2010 Design, Automation & Test in Europe Conference & Exhibition (DATE 2010) , pp. 741–746, IEEE, 2010.

[4] M. Bechtel and H. Y un, “Denial-of-service attacks on shared cache in multicore: Analysis and prevention,” in 2019 IEEE Real-Time and Embedded Technology and Applications Symposium (RTAS) , pp. 357– 367, IEEE, 2019.

[5] J. Giesen, P . Benedicte, E. Mezzetti, J. Abella, and F. J. Cazorla, “Mod- eling contention interference in crossbar-based systems via sequence- aware pairing (seap),” in 2020 IEEE Real-Time and Embedded Technol- ogy and Applications Symposium (RTAS) , pp. 253–266, IEEE, 2020.

[6] M. Hassan and R. Pellizzoni, “Bounding dram interference in cots heterogeneous mpsocs for mixed criticality systems,” IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems , vol. 37, no. 11, pp. 2323–2336, 2018.

[7] D. Casini, A. Biondi, G. Nelissen, and G. Buttazzo, “A holistic mem- ory contention analysis for parallel real-time tasks under partitioned scheduling,” in 2020 IEEE Real-Time and Embedded Technology and Applications Symposium (RTAS) , pp. 239–252, IEEE, 2020.

[8] D. Iorga, T. Sorensen, J. Wickerson, and A. F. Donaldson, “Slow and steady: Measuring and tuning multicore interference,” in 2020 IEEE Real-Time and Embedded Technology and Applications Symposium (RTAS), pp. 200–212, IEEE, 2020.

[9] A. Li, M. Sudvarg, H. Liu, Z. Y u, C. Gill, and N. Zhang, “Polyrhythm: Adaptive tuning of a multi-channel attack template for timing interfer- ence,” in 2022 IEEE Real-Time Systems Symposium (RTSS) , pp. 225– 239, IEEE, 2022.

[10] T. Y androfski, J. Chen, N. Otterness, J. H. Anderson, and F. D. Smith, “Making powerful enemies on nvidia gpus,” in 2022 IEEE Real-Time Systems Symposium (RTSS) , pp. 383–395, IEEE, 2022.

[11] N. Singh, K. Renganathan, C. Rebeiro, J. Jose, and R. Mader, “Kryp- tonite: Worst-case program interference estimation on multi-core em- bedded systems,” ACM Transactions on Embedded Computing Systems , vol. 22, no. 5s, pp. 1–23, 2023.

[12] M. Bechtel and H. Y un, “Cache bank-aware denial-of-service attacks on multicore arm processors,” in 2023 IEEE 29th Real-Time and Embedded Technology and Applications Symposium (RTAS) , pp. 198–208, IEEE, 2023.

[13] N. Feiertag, K. Richter, J. Nordlander, and J. Jonsson, “A compositional framework for end-to-end path delay calculation of automotive systems under different path semantics,” in IEEE Real-Time Systems Symposium: 30/11/2009-03/12/2009, IEEE Communications Society, 2009.

[14] P . Gohari, M. Nasri, and J. V oeten, “Data-age analysis for multi- rate task chains under timing uncertainty,” in Proceedings of the 30th International Conference on Real-Time Networks and Systems , pp. 24– 35, 2022.

[15] P . Pazzaglia and M. Maggio, “Characterizing the effect of deadline misses on time-triggered task chains,” IEEE Transactions on Computer- Aided Design of Integrated Circuits and Systems , vol. 41, no. 11, pp. 3957–3968, 2022.

[16] A. Davare, Q. Zhu, M. Di Natale, C. Pinello, S. Kanajan, and A. Sangiovanni-Vincentelli, “Period optimization for hard real-time distributed automotive systems,” in Proceedings of the 44th annual Design Automation Conference , pp. 278–283, 2007.

[17] Y . Zhao, V . Gala, and H. Zeng, “A unified framework for period and priority optimization in distributed hard real-time systems,” IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems, vol. 37, no. 11, pp. 2188–2199, 2018.

[18] T. Klaus, M. Becker, W. Schr ̈oder-Preikschat, and P . Ulbrich, “Con- strained data-age with job-level dependencies: How to reconcile tight bounds and overheads,” in 2021 IEEE 27th Real-Time and Embedded Technology and Applications Symposium (RTAS) , pp. 66–79, IEEE, 2021.

[19] M. G ̈unzel, K.-H. Chen, N. Ueter, G. von der Br ̈uggen, M. D ̈urr, and J.-J. Chen, “Timing analysis of asynchronized distributed cause-effect chains,” in 2021 IEEE 27th Real-Time and Embedded Technology and Applications Symposium (RTAS) , pp. 40–52, IEEE, 2021.

[20] N. Vreman, A. Cervin, and M. Maggio, “Stability and performance analysis of control systems subject to bursts of deadline misses,” in 33rd Euromicro Conference on Real-Time Systems (ECRTS 2021) , Schloss Dagstuhl-Leibniz-Zentrum f ̈ur Informatik, 2021.

[21] A. Gujarati, M. Nasri, and B. B. Brandenburg, “Quantifying the re- siliency of fail-operational real-time networked control systems,” in 30th Euromicro Conference on Real-Time Systems (ECRTS 2018) , Schloss Dagstuhl-Leibniz-Zentrum fuer Informatik, 2018.

[22] M. Maggio, A. Hamann, E. Mayer-John, and D. Ziegenbein, “Control- system stability under consecutive deadline misses constraints,” in 32nd euromicro conference on real-time systems (ECRTS 2020) , Schloss Dagstuhl-Leibniz-Zentrum f ̈ur Informatik, 2020.

[23] N. Vreman and M. Maggio, “Stochastic analysis of control systems subject to communication and computation faults,” ACM Transactions on Embedded Computing Systems , vol. 22, no. 5s, pp. 1–25, 2023.

[24] S. Baruah, P . Ekberg, M. Hosseinzadeh, A. Li, B. Ward, and N. Zhang, “Who’s afraid of butterflies? a close examination of the butterfly attack,” in 2023 IEEE Real-Time Systems Symposium (RTSS) , pp. 53–63, IEEE, 2023.

[25] J. M. V oas and G. McGraw, Software fault injection: inoculating programs against errors . John Wiley & Sons, Inc., 1997.

[26] D. H. Woo and H. Lee, “Analyzing performance vulnerability due to resource denial of service attack on chip multiprocessors,” in Workshop on Chip Multiprocessor Memory Systems and Interconnects , 2007.

[27] T. M. O. Mutlu, “Memory performance attacks: Denial of memory service in multi-core systems,” in USENIX security , 2007.

[28] H. S. Bedi and S. Shiva, “Securing cloud infrastructure against co- resident dos attacks using game theoretic defense mechanisms,” in ICACCI, 2012.

[29] Z. Y ang, H. Fang, Y . Wu, C. Li, B. Zhao, and H. H. Huang, “Under- standing the effects of hypervisor i/o scheduling for virtual machine performance interference,” in 4th IEEE International Conference on Cloud Computing Technology and Science Proceedings , pp. 34–41, IEEE, 2012.

[30] M. S. Inci, T. Eisenbarth, and B. Sunar, “Hit by the bus: Qos degradation attack on android,” in Proceedings of the 2017 ACM on Asia Conference on Computer and Communications Security , pp. 716–727, 2017.

[31] T. Zhang, Y . Zhang, and R. B. Lee, “Dos attacks on your memory in cloud,” in Proceedings of the 2017 ACM on Asia Conference on Computer and Communications Security , pp. 253–265, 2017.

[32] V . V aradarajan, T. Kooburat, B. Farley, T. Ristenpart, and M. M. Swift, “Resource-freeing attacks: improve your cloud performance (at your neighbor’s expense),” in Proceedings of the 2012 ACM conference on Computer and communications security , pp. 281–292, 2012.

[33] ROBOTIS, “Openmanipulator x.” https://emanual.robotis.com/docs/en/ platform/openmanipulator x/overview/. Accessed: 2022-9-07.

[34] “Turtlebot3.” https://emanual.robotis.com/docs/en/platform/turtlebot3/ overview/. Accessed: 2022-01-10.

[35] R. Mur-Artal, J. M. M. Montiel, and J. D. Tardos, “Orb-slam: a versatile and accurate monocular slam system,” IEEE transactions on robotics , vol. 31, no. 5, pp. 1147–1163, 2015.

[36] C. Campos, R. Elvira, J. J. G. Rodr ́ıguez, J. M. Montiel, and J. D. Tard ́os, “Orb-slam3: An accurate open-source library for visual, visual– inertial, and multimap slam,” IEEE Transactions on Robotics , vol. 37, no. 6, pp. 1874–1890, 2021.

[37] A. Geiger, P . Lenz, and R. Urtasun, “Are we ready for autonomous driving? the kitti vision benchmark suite,” in 2012 IEEE conference on computer vision and pattern recognition , pp. 3354–3361, IEEE, 2012.

[38] “Autoware auto gitlab.” https://gitlab.com/autowarefoundation/autoware. auto. Accessed: 2022-12-12.

[39] “Moveit.” https://moveit.ros.org/. Accessed: 2022-10-23.

[40] Google, “Google cartographer.” https://google-cartographer.readthedocs. io. Accessed: 2022-03-29.

[41] “Baidu apollo open-source self-driving project.” https://apollo.auto/ platform/hardware.html. Accessed: 2023-08-15.

[42] “Orb-slam2 github.” https://github.com/raulmur/ORB SLAM2. Ac- cessed: 2022-01-07.

[43] “Orb-slam3 github.” https://github.com/UZ-SLAMLab/ORB SLAM3. Accessed: 2022-01-07.

[44] “Ros navigation github.” https://github.com/ros-planning/navigation. Ac- cessed: 2022-01-01.

[45] “Ros2 rcl rclcpp rclpy libraries.” https://github.com/orgs/ros2/ repositories. Accessed: 2022-11-19.

[46] S. Lu, S. Park, E. Seo, and Y . Zhou, “Learning from mistakes: a comprehensive study on real world concurrency bug characteristics,” in Proceedings of the 13th international conference on Architectural support for programming languages and operating systems , pp. 329– 339, 2008.

[47] G. Li, S. Lu, M. Musuvathi, S. Nath, and R. Padhye, “Efficient scal- able thread-safety-violation detection: finding thousands of concurrency bugs during testing,” in Proceedings of the 27th ACM Symposium on Operating Systems Principles , pp. 162–180, 2019.

[48] Y . Sui and J. Xue, “Svf: interprocedural static value-flow analysis in llvm,” in Proceedings of the 25th international conference on compiler construction, pp. 265–266, 2016.

[49] G. Bernat, A. Burns, and A. Liamosi, “Weakly hard real-time systems,” IEEE transactions on Computers , vol. 50, no. 4, pp. 308–321, 2001.

[50] N. Vreman, R. Pates, and M. Maggio, “Weaklyhard. jl: Scalable analysis of weakly-hard constraints,” in 2022 IEEE 28th Real-Time and Em- bedded Technology and Applications Symposium (RTAS) , pp. 228–240, IEEE, 2022.

[51] T. Sherwood, E. Perelman, G. Hamerly, and B. Calder, “Automatically characterizing large scale program behavior,” in Proceedings of the 10th International Conference on Architectural Support for Programming Languages and Operating Systems , ASPLOS X, (New Y ork, NY , USA), p. 45–57, Association for Computing Machinery, 2002.

[52] J. Mars, L. Tang, R. Hundt, K. Skadron, and M. L. Soffa, “Bubble- up: Increasing utilization in modern warehouse scale computers via sensible co-locations,” in Proceedings of the 44th annual IEEE/ACM International Symposium on Microarchitecture , pp. 248–259, 2011.

[53] “Autonomous valet parking demo 2020.” https://www.autoware.org/post/ autonomous-valet-parking-2020. Accessed: 2022-12-12.

[54] C. Lattner and V . Adve, “Llvm: A compilation framework for lifelong program analysis & transformation,” in International symposium on code generation and optimization, 2004. CGO 2004. , pp. 75–86, IEEE, 2004.

[55] S. S. Banerjee, S. Jha, Z. Kalbarczyk, and R. K. Iyer, “Bayesperf: minimizing performance monitoring errors using bayesian statistics,” in Proceedings of the 26th ACM International Conference on Architectural Support for Programming Languages and Operating Systems , pp. 832– 844, 2021.

[56] “Ros-industrial applications of moveit.” https://moveit.ros.org/robots/. Accessed: 2022-10-23.

[57] “Picknik robotics wins space force, nasa contracts.” https://www. therobotreport.com/picknik-robotics-wins-space-force-nasa-contracts/. Accessed: 2022-10-23.

[58] X. Shi, L. Cao, D. Wang, L. Liu, G. Y ou, S. Liu, and C. Wang, “Hero: Accelerating autonomous robotic tasks with fpga,” in 2018 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS) , pp. 7766–7772, IEEE, 2018.

[59] C. Wang, J. Bingham, and M. Tomizuka, “Trajectory splitting: A distributed formulation for collision avoiding trajectory optimization,” in 2021 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS) , pp. 8113–8120, IEEE, 2021.

[60] S. Kohn, A. Blank, D. Puljiz, L. Zenkel, O. Bieber, B. Hein, and J. Franke, “Towards a real-time environment reconstruction for vr- based teleoperation through model segmentation,” in 2018 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS) , pp. 1–9, IEEE, 2018.

[61] M.-Y . Wang, A. A. Kogkas, A. Darzi, and G. P . Mylonas, “Free-view, 3d gaze-guided, assistive robotic system for activities of daily living,” in 2018 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS) , pp. 2355–2361, IEEE, 2018.

[62] “Ardupilot project.” https://ardupilot.org/. Accessed: 2022-10-02.

[63] L. Meier, D. Honegger, and M. Pollefeys, “Px4: A node-based mul- tithreaded open source robotics framework for deeply embedded plat- forms,” in 2015 IEEE international conference on robotics and automa- tion (ICRA) , pp. 6235–6240, IEEE, 2015.

[64] “Robotis op3.” https://emanual.robotis.com/docs/en/platform/op3/ introduction/. Accessed: 2021-08-15.

[65] “Jackal ugv.” https://clearpathrobotics.com/ jackal-small-unmanned-ground-vehicle/. Accessed: 2021-07-30.

[66] S. Kato, S. Tokunaga, Y . Maruyama, S. Maeda, M. Hirabayashi, Y . Kit- sukawa, A. Monrroy, T. Ando, Y . Fujii, and T. Azumi, “Autoware on board: Enabling autonomous vehicles with embedded systems,” in 2018 ACM/IEEE 9th International Conference on Cyber-Physical Systems (ICCPS), pp. 287–296, IEEE, 2018.

[67] M. Alcon, H. Tabani, L. Kosmidis, E. Mezzetti, J. Abella, and F. J. Cazorla, “Timing of autonomous driving software: Problem analysis and prospects for future solutions,” in 2020 IEEE Real-Time and Embedded Technology and Applications Symposium (RTAS) , pp. 267–280, IEEE, 2020.

[68] P . R. Nikiema, A. Kritikakou, M. Traiola, and O. Sentieys, “Impact of transient faults on timing behavior and mitigation with near-zero wcet overhead,” in 35th Euromicro Conference on Real-Time Systems (ECRTS 2023), Schloss Dagstuhl-Leibniz-Zentrum f ̈ur Informatik, 2023.

[69] I. Gog, S. Kalra, P . Schafhalter, J. E. Gonzalez, and I. Stoica, “D3: a dynamic deadline-driven approach for building autonomous vehicles,” in Proceedings of the Seventeenth European Conference on Computer Systems, pp. 453–471, 2022.

[70] Y . Wang, A. Li, J. Wang, S. Baruah, and N. Zhang, “Opportunistic data flow integrity for real-time cyber-physical systems using worst case execution time reservation,” in USENIX Security Symposium , 2024.

[71] M. Sudvarg, A. Li, D. Wang, S. Baruah, J. Buhler, C. Gill, N. Zhang, and P . Ekberg, “Elastic scheduling for harmonic task systems,” in 2024 Real- Time and Embedded Technology and Applications Symposium (RTAS) , IEEE, 2024.

[72] J. Wang, A. Li, H. Li, C. Lu, and N. Zhang, “Rt-tee: Real-time system availability for cyber-physical systems using arm trustzone,” in 2022 IEEE Symposium on Security and Privacy (SP) , pp. 352–369, IEEE, 2022.

[73] M. Sudvarg and C. Gill, “A concurrency framework for priority-aware intercomponent requests in camkes on sel4,” in 2022 IEEE 28th Inter- national Conference on Embedded and Real-Time Computing Systems and Applications (RTCSA) , pp. 1–10, IEEE, 2022.

[74] D. Grunwald and S. Ghiasi, “Microarchitectural denial of service: Insuring microarchitectural fairness,” in MICRO, IEEE, 2002.

[75] J. Hasan, A. Jalote, T. Vijaykumar, and C. E. Brodley, “Heat stroke: power-density-based denial of service in smt,” in 11th International Symposium on High-Performance Computer Architecture , pp. 166–177, IEEE, 2005.

[76] F. Zhou, M. Goel, P . Desnoyers, and R. Sundaram, “Scheduler vul- nerabilities and coordinated attacks in cloud computing,” Journal of Computer Security , vol. 21, no. 4, pp. 533–559, 2013.

[77] B. Wittenmark, J. Nilsson, and M. Torngren, “Timing problems in real-time control systems,” in Proceedings of 1995 American Control Conference-ACC’95, vol. 3, pp. 2000–2004, IEEE, 1995.

[78] J. Nilsson, B. Bernhardsson, and B. Wittenmark, “Stochastic analysis and control of real-time systems with random time delays,” Automatica, vol. 34, no. 1, pp. 57–64, 1998.

[79] A. Cervin, “Stability and worst-case performance analysis of sampled- data control systems with input and output jitter,” in ACC, IEEE, 2012.

[80] Z. Zhang, S. Gong, A. D. Dimitrovski, and H. Li, “Time synchronization attack in smart grid: Impact and analysis,” IEEE Transactions on Smart Grid, vol. 4, no. 1, pp. 87–98, 2013.

[81] R. Mahfouzi, A. Aminifar, S. Samii, M. Payer, P . Eles, and Z. Peng, “Butterfly attack: Adversarial manipulation of temporal properties of cyber-physical systems,” in 2019 IEEE Real-Time Systems Symposium (RTSS), pp. 93–106, IEEE, 2019.

[82] J. Wang, Y . Wang, A. Li, Y . Xiao, R. Zhang, W. Lou, Y . T. Hou, and N. Zhang, “ {ARI}: Attestation of real-time mission execution integrity,” in 32nd USENIX Security Symposium (USENIX Security 23) , pp. 2761– 2778, 2023.

[83] M. Bechtel and H. Y un, “Analysis and mitigation of shared resource contention on heterogeneous multicore: An industrial case study,” arXiv preprint arXiv:2304.13110 , 2023.

[84] G. Rong et al. , “Lgsvl simulator: A high fidelity simulator for au- tonomous driving,” in 2020 IEEE 23rd International Conference on Intelligent Transportation Systems (ITSC) , pp. 1–6, IEEE, 2020.

[85] P . Biber and W. Straßer, “The normal distributions transform: A new approach to laser scan matching,” in Proceedings 2003 IEEE/RSJ Inter- national Conference on Intelligent Robots and Systems (IROS 2003)(Cat. No. 03CH37453) , vol. 3, pp. 2743–2748, IEEE, 2003.

[86] W. Hess et al., “Real-time loop closure in 2d lidar slam,” in ICRA, IEEE, 2016.

[87] R. C. Coulter, “Implementation of the pure pursuit path tracking algo- rithm,” tech. rep., Carnegie-Mellon UNIV Pittsburgh PA Robotics INST, 1992.

## 原PDF逐页图像

原图、图内代码、符号和文献排版可在以下图像逐页对照。

- [第01页](./source_pages/page_01.png)
- [第02页](./source_pages/page_02.png)
- [第03页](./source_pages/page_03.png)
- [第04页](./source_pages/page_04.png)
- [第05页](./source_pages/page_05.png)
- [第06页](./source_pages/page_06.png)
- [第07页](./source_pages/page_07.png)
- [第08页](./source_pages/page_08.png)
- [第09页](./source_pages/page_09.png)
- [第10页](./source_pages/page_10.png)
- [第11页](./source_pages/page_11.png)
- [第12页](./source_pages/page_12.png)
- [第13页](./source_pages/page_13.png)
- [第14页](./source_pages/page_14.png)
- [第15页](./source_pages/page_15.png)
- [第16页](./source_pages/page_16.png)
- [第17页](./source_pages/page_17.png)
