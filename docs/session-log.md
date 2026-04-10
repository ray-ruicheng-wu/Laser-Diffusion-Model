# 会话记录

## 2026-04-07

### 当前目标

从零开始规划一个“激光诱导硅表面掺杂”的模拟项目，并优先从“表面有一层 source”的模型起步。

### 本次达成的结论

1. 这是一个强瞬态、带相变的热-质传输问题。
2. 第一版最适合先做 `1D 深度方向模型`，而不是直接做完整 2D/3D。
3. 相变推荐先用 `焓法`，这样不必一开始就显式追踪熔融界面。
4. 掺杂扩散推荐采用 `D(T, f_l)` 的相依赖模型，利用液相高扩散系数来体现快速掺杂。
5. 表面 source 层第一版推荐建成 `有限库存 reservoir`，比固定表面浓度更真实，也比显式薄层更容易做。
6. 第一阶段先做热场与熔深，第二阶段再加掺杂扩散，属于更稳妥的开发顺序。

### 当前推荐路线

- `Step 1`: 1D 热传导 + 激光热源 + 相变
- `Step 2`: 在给定温度场上求解掺杂扩散
- `Step 3`: 加入 surface reservoir 质量守恒
- `Step 4`: 做可视化和参数扫描
- `Step 5`: 需要时升级到 2D 轴对称 FEM

### 近期待确认

1. 激光脉冲时间尺度
2. 激光空间分布是否先忽略横向
3. 掺杂元素类型
4. source 层是有限库存还是近似无限供给
5. 第一版最关心的输出量

### 续做入口

下一次如果要继续，优先读取：

- `docs/modeling-roadmap.md`
- `docs/session-log.md`

然后直接进入：

- 建立 `Milestone 1` 的 1D 热模型

### Phase 1 当前状态

`Milestone 1` 已完成第一版可运行实现，包含：

- `1D` 深度方向瞬态热传导
- 高斯脉冲 + Beer-Lambert 体热源
- 基于表观热容法的相变处理
- `T(z,t)`、`f_l(z,t)`、熔深曲线输出
- 命令行可调参数与图像输出

### Phase 1 默认算例结果

- 峰值表面温度约 `1807 K`
- 最大熔深约 `128 nm`
- 熔融窗口约 `31.2 ns` 到 `57.0 ns`

### 新确认的工艺前提

- 激光波长：`532 nm`
- 激光重复频率：`500 kHz`
- 掺杂元素：`P`
- 表面 source：`PSG`
- 新增可调输入：`PSG` 中 `P` 浓度、`Si` 基底中 `Ga` 浓度

### 当前默认浓度输入

- `PSG` 中 `P` 浓度默认：`2.0e21 cm^-3`
- `Si` 基底中 `Ga` 浓度默认：`1.0e16 cm^-3`

这两个值目前只是输入参数和元数据，尚未进入 Phase 1 热方程；但它们已经会被保存到输出摘要中，并会做基础的非物理上限检查。

### 基于 532 nm 的复核结论

按“裸硅表面”的公开光学参数近似，`532 nm` 下硅的吸收深度大约在 `1 um` 量级，而不是此前默认的 `80 nm`。在保持其他参数不变、仅把光学参数改成更接近 `532 nm` 的常数值后，当前单脉冲案例结果变为：

- 峰值表面温度约 `1157 K`
- 不发生熔化

因此，之前默认案例得到的熔化结果不能再直接当作 `532 nm` 裸硅的结果使用。

### 关于 500 kHz 的当前判断

`500 kHz` 对应脉冲间隔 `2 us`。单独知道重复频率还不足以确定单脉冲能量；还需要平均功率或光斑尺寸。按室温硅热扩散率估算，`2 us` 的热扩散长度量级约 `13.8 um`，说明若脉冲空间上不强重叠，则热积累未必显著。是否存在明显累计加热，需要结合光斑尺寸、扫描重叠和平均功率再判断。

### PSG 作为源层的最小接口更新

已经把 `PSG/P` 显式记录为 `surface_source` 元数据，但暂时不把 PSG 直接耦合进热方程。这是为了让 Phase 1 保持纯热求解，同时给 Phase 2 的扩散边界预留统一接口。公开资料显示 PSG 常由 POCl3 predeposition 形成，并可能在 SiO2-Si 界面积累 P，因此下一阶段更适合用“PSG 供源 + 界面库存”来建模，而不是继续按裸硅处理。

### Phase 1 过程中发现并修复的问题

早期版本把底部 `Dirichlet` 边界直接与内部未知量放在同一个大矩阵里，细网格下会导致稀疏求解器出现严重数值病态，表现为“零输入也自发升温”。现已改为边界消元形式，问题消失。

### Phase 1 交付物

本阶段已经补充以下说明文档：

- `docs/phase1-code-explained.md`
- `docs/phase1-analysis.md`

### Phase 2 当前状态

`Milestone 2` 已完成第一版实现，包含：

- 基于 Phase 1 温度场驱动的 `P` 扩散
- `PSG` 有限库存 reservoir 近似
- `Ga` 背景浓度输入
- `P(z,t)` 浓度热图
- 最终 `P(z)` 剖面
- 掺杂深度随时间变化图

### Phase 2 默认算例结果

- 最终峰值 `P` 浓度约 `1.40e21 cm^-3`
- 最终掺杂深度约 `144.3 nm`
- 最大掺杂深度约 `144.3 nm`

### Phase 2 对照结果

按 `532 nm` 裸硅基线光学参数运行时，若热模型不发生熔化，则 Phase 2 结果自然退化为：

- 最终峰值 `P` 浓度 `0`
- 掺杂深度 `0`

这与之前的热分析结论一致。

### Phase 2 交付物

本阶段已补充：

- `docs/phase2-code-explained.md`
- `docs/phase2-analysis.md`

### 下一次续做入口

下一次继续时优先读取：

- `docs/modeling-roadmap.md`
- `docs/session-log.md`
- `docs/phase1-code-explained.md`
- `docs/phase1-analysis.md`
- `docs/phase2-code-explained.md`
- `docs/phase2-analysis.md`

之后直接进入：

- `Milestone 3`：把热模型升级成 `PSG/Si` 双层，再重新驱动扩散

### Phase 2 公式复核与修正

用户指出当前掺杂结果不可信后，重新审查了 Phase 2 的基础公式和实现。复核结论是：

1. 旧版库存更新确实会破坏质量守恒。
2. 旧版表面边界把 PSG source 近似成了过强的硬 Dirichlet。
3. 旧版液/固界面扩散率采用算术平均，不适合高反差扩散问题。
4. 旧版结深读取存在明显网格量化误差。

已完成的修正：

- 表面边界改成 `有限库存 + Robin 通量/传质边界`
- PSG 库存改成按 `source + Si 总量守恒` 直接反算
- 网格界面扩散率改成谐和平均
- 结深读取改成浓度交点插值

修正后默认 Phase 2 结果：

- 最终峰值 `P` 浓度约 `5.162e20 cm^-3`
- 最终结深约 `143.7 nm`
- 质量守恒误差约 `-6.144e3 atoms/m^2`

新的判断：

- Phase 2 基础扩散公式已经比旧版自洽得多
- 当前结果的主要不确定性开始转移到 Phase 1 的热-相变收敛性
- 后续优先级应变成：
  先补 Phase 1 / `PSG/Si` 双层热模型收敛，再补移动界面掺杂模型

### 文书老哥专用记忆文件

为降低后续资料线的上下文负担，已新增：

- `docs/wenshu-laoge-memory.md`

用途：

1. 存放文书老哥当前应视为“已知”的模型骨架、参考入口、参数口径和待查优先级。
2. 后续再次调用文书老哥时，先让它阅读这份记忆文件，再继续查新资料。
3. 目前这是项目内局部记忆，不是全局自动记忆；若后续需要自动读取，还可以再接入全局 `AGENTS.md` 记忆入口。

### 公式与文献总表

为了满足“每个真正采用的数学模型都要记录下来并标注文献”的要求，已新增：

- `docs/formula-reference-register.md`

当前约定：

1. 任何进入代码或当前分析口径的公式，都要先登记到这里。
2. 每条公式都要标明 `adopted / candidate / rejected`。
3. 每完成一个阶段，必须更新：
   - 该阶段新增的公式
   - 对应文献
   - 阶段更新记录

### 日志和文档老哥

为了把“结果记录”和“资料搜索”彻底分开，新增了一个专门负责阶段总结和文档维护的角色：

- `docs/rizhi-wendang-laoge-memory.md`

它的职责是：

1. 维护阶段总结、结果摘要和续做入口
2. 保证 docs 内口径一致
3. 检查阶段文档是否同步了公式表和结果位置

它不负责查新文献，也不负责决定物理公式是否采用；那部分仍交给 `文书老哥`。

### 当前结果与论文差距

在等待文书老哥补齐缺失公式期间，先做了一轮“当前结果 vs 论文量级”的对照，整理在：

- `docs/literature-gap-analysis.md`

当前最重要的对照结论是：

1. 当前模型的最终进入 Si 的总 P 剂量约 `1.61e15 cm^-2`，和 Fraunhofer 2018 LDSE 工作中的 `~2e15 cm^-2` 已经比较接近。
2. 但当前峰值 `P` 浓度约 `5.16e20 cm^-3`，明显高于文献中常见的 `4e19–5e19 cm^-3`。
3. 当前结深约 `144 nm`，明显浅于 Fraunhofer 2018 中常见的 `0.5–0.7 um`。
4. 这说明当前问题更像是“轮廓过尖、过浅”，而不是“总剂量完全不对”。
5. 下一步优先级因此更明确地指向：
   - `PSG/Si` 双层热模型
   - 功率-光斑-fluence 一致性
   - moving interface + `k(v)`

### Phase 3 当前状态

Phase 3 第一轮已经完成，新增：

- `src/laser_doping_sim/phase3_stack_thermal.py`
- `run_phase3.py`
- `docs/phase3-analysis.md`
- `docs/phase3-code-explained.md`
- `docs/phase3-work-report.md`
- `docs/stage-report-template.md`

当前默认 Phase 3 结果：

- 峰值 Si 表面温度约 `1098.5 K`
- 最大 Si 熔深 `0`
- 重驱动扩散后最终 `P` 浓度 `0`
- 最终结深 `0`

当前解释：

1. 双层热模型第一版已经跑通。
2. 只补 `PSG/Si` 双层热学还不足以把结果推到文献中的重熔和深掺杂。

## 2026-04-09 Dual-Channel Activation Update

### 当前目标

把 measured 主线里的 laser 后电学活化从单一 `non-active pool` 拆成两条独立通道：

1. `initial inactive re-activation`
2. `injected P activation`

### 本次完成的内容

1. 新增双通道活化模型结构：
   - `src/laser_doping_sim/activation_models.py`
   - `run_sheet_resistance_cases.py`
2. 新增 measured `Rsh` 输入表：
   - `inputs/activation_models/measured_rsh_24_60w.csv`
3. 新增自动标定脚本：
   - `run_dual_channel_activation_calibration.py`
4. 新增方法说明文档：
   - `docs/dual-channel-activation-method.md`

### 当前双通道闭合

当前 laser 后有效施主写成：

- `active component`
- `eta_inactive(P) * inactive component`
- `eta_inj(P) * injected component`

也就是把“初始 inactive 再激活”和“PSG 注入活化”彻底分开记账。

### 标定流程

1. 先用实验前片阻的平均值标定统一的 `initial inactive activation`
2. 用低注入功率点 `24–48 W` 拟合 `eta_inactive(P)`，并暂定 `eta_inj = 0`
3. 再把低功率得到的 `eta_inactive(P)` 外推到 `54/60 W`
4. 在高功率点上反求 `eta_inj(P)`

### 当前输出

- `outputs/phase3/dual_channel_activation_calibration_24_60w/dual_channel_activation_model.csv`
- `outputs/phase3/dual_channel_activation_calibration_24_60w/calibration_summary.json`
- `outputs/phase3/dual_channel_activation_calibration_24_60w/measured_vs_modeled_rsh.csv`
- `outputs/phase3/sheet_resistance_dual_channel_activation_24_60w/sheet_resistance_summary.csv`

### 当前最重要的结论

1. 低功率段 `24–48 W` 可以只用 `initial inactive re-activation` 稳定贴住实验 `Rsh`
2. 但把这条低功率 `eta_inactive(P)` 直接外推到 `54/60 W` 后，模型即使令 `eta_inj = 0`，也已经把 `Rsh` 压得比实验更低
3. 这说明高功率区不能继续直接沿用低功率的 inactive 再激活规律
4. 因而“双通道模型”的第一轮最重要成果，是明确识别出了高功率区的 regime change

### 当前推荐的下一步

1. 给高功率区单独定义 `eta_inactive` 的 rollover / decrease
2. 或把 `eta_inj` 改成显式依赖 melt / resolidification 指标
3. 若后续能拿到 laser 后 `ECV`，优先用它帮助分离两条活化通道

### 24–60 W / 2 W 扫描补充

基于 measured 主线与 `PSG = surface SIMS`，又新增了一轮更细的功率扫描：

- `outputs/phase3/power_scan_24_60w_step2_measured_ctv_psg_eq_sims`

这轮设置是：

- `24–60 W`
- 步长 `2 W`
- measured initial profile
- `source_dopant_concentration_cm3 = 4.5913166904198945e21 cm^-3`
- `surface_reflectance = 0.09`
- `boundary_model = finite_source_cell`
- `source_exchange_mode = melt_only`

对应的双通道 `Rsh` 后处理也已生成：

- `outputs/phase3/sheet_resistance_dual_channel_step2_24_60w`

需要注意：

1. 这轮 `Rsh` 中，非锚点功率的活化率来自双通道标定表的分段线性插值，不是新一轮独立实验反标。
2. 低功率段 `24–48 W` 仍主要反映 `eta_inactive(P)` 插值后的经验电学校准。
3. `54 W+` 继续沿用当前高功率占位口径，因此该段结果应读成“当前双通道模型下的趋势预测”，不是高功率区最终 adopted 物理闭合。

### 界面模型文献补充

针对 `interfacial_transport_length_m` 又做了一轮专门的界面文献复核，并新增：

- `docs/interface-model-literature-notes.md`

这轮复核后的当前结论是：

1. 当前代码中的 `interfacial_transport_length_m` 应读成 **effective interface transport length**
2. 它是一个 lumped 界面阻力参数，不是实测真实氧化层厚度
3. 目前没有直接文献支持把 `100 nm` 解释为真实 `PSG/SiO2/Si` 中间层厚度
4. 文献更支持的下一代界面模型是：
   - 显式 `source cell`
   - 显式 `oxide barrier thickness`
   - `Si/SiO2` 界面的 segregation / pile-up

### 高功率段双通道重拟合

针对用户提出的“重新拟合后半段双通道”，已新增：

- `run_dual_channel_high_power_refit.py`
- `outputs/phase3/dual_channel_high_power_refit_48_60w`

这轮采用的最小闭合是：

1. `48 W` 作为低/高功率边界锚点
2. `eta_inactive(P)` 在 `48 -> 60 W` 之间线性回落
3. `eta_inj(P)` 在 `48 -> 60 W` 之间从 `0` 线性抬升
4. 用 `54 W` 与 `60 W` 的实验 `Rsh` 反求高功率端点

当前得到的关键参数是：

- `eta_inactive(60 W) = 0.1770096367257125`
- `eta_inj(60 W) = 0.013385385369170012`

这说明：

1. 高功率区若想贴住实验，`initial inactive` 通道必须较低功率外推明显回落
2. `injected P` 通道只需要较小但非零的活化比例
3. 当前最合理的读法是“高功率区出现 inactive rollover + 注入通道开始参与”

并且已基于这张新 activation 表重算：

- `outputs/phase3/sheet_resistance_dual_channel_step2_24_60w_refit_highpower`

对应新的 `24–60 W / 2 W` 片阻曲线。
3. 下一轮最该补的是：
   - `30 W @ 500 kHz` 到单脉冲 fluence 的一致性
   - 更真实的 `PSG/SiO2/Si` 光学堆栈
   - 然后再补 moving interface + `k(v)`

### 范围修正

用户已明确当前项目范围内：

1. 不需要做多次脉冲热积累。
2. 激光平均功率采用 `30 W`。

因此当前统一口径改为：

- `500 kHz` 只用于把平均功率换算成单脉冲能量
- `30 W / 500 kHz = 60 uJ per pulse`
- 当前默认横向光斑设为 `flat-top square`
- 正方形边长 `95 um`
- 对应单脉冲等效 fluence 约 `0.665 J/cm^2`

### 结果审查流程新增约束

用户已明确要求：以后每一次生成新结果之后，都必须先交给 `狗叫的` 审查一遍。

当前固定流程改为：

1. `臭写代码的` 或主线程生成结果
2. `狗叫的` 按公式、边界条件、守恒和量纲做审查
3. 审查结论写入阶段工作报告
4. `日志和文档老哥` 再做正式归档

已新增：

- `docs/gou-jiao-de-memory.md`
- `docs/stage-report-template.md` 中的 `狗叫的审查记录` 小节

### PSG 口径收紧

用户要求重新记住并统一 `PSG` 的物理解释。

当前项目口径改为：

1. `PSG = phosphosilicate glass`
2. 组成上近似按 `P2O5-SiO2 glass` 理解
3. 当前最小模型中，把它视为“一层高磷 SiO2”
4. 若现实工艺存在超薄 `SiO2` 夹层，当前先并入有效玻璃层，不单独离散

后续文献搜索优先关注：

1. 其他论文如何描述 `PSG` 的组成
2. 其他模型是否显式使用 `PSG/SiO2/Si`
3. 热学、光学和传质上各自如何简化

### 非融化固态扩散已并入

用户明确要求：即使 Si 不熔化，也要把固态扩散算进去，因为实验上仍会看到掺杂。

当前模型已改为：

1. 固相 `P in Si` 扩散采用 Arrhenius 形式
2. 表面 Robin 注入边界在固态和液态都允许存在
3. 因此“未熔化”不再自动等价于“零掺杂”

当前默认 `Phase 3` 在 `30 W / 500 kHz / 95 um square flat-top` 下的新结果是：

- 峰值 Si 表面温度约 `1360.8 K`
- 不熔化
- 最终峰值 `P` 浓度约 `0 cm^-3`
- 结深仍为 `0`

当前判断：

1. 固态扩散这层物理已经并进来
2. 但在纳秒级单脉冲热预算下，它仍然非常弱
3. 若实验里出现更明显的非融化掺杂，下一步应考虑：
   - 预扩散初始 `P` 轮廓
   - 更长单脉冲热尾
   - 更真实的 `PSG/SiO2/Si` 界面与 source 口径

狗叫的已复审这一轮结果，结论：`通过`。

唯一保留的轻微风险：

- `interface_liquid_threshold` 参数目前仍保留在输入里，但已不再决定边界是否开启，后续需要在参数文档里进一步去歧义。

### 高 source 扫描结论

为了测试“只提高表面 `P` 浓度和总量，能不能先保证形成 junction”，已新增两组探索结果：

- `outputs/phase3/high_source_sweep/sweep_summary.json`
- `outputs/phase3/transport_limit_sweep/sweep_summary.json`

当前固定条件：

- `30 W`
- `500 kHz`
- `95 um square flat-top`
- 单脉冲
- 非融化固态扩散模型

第一组结果说明：

1. 把 `source_concentration` 从 `2e21` 提到 `4e22 cm^-3`
2. 把 `source_effective_thickness` 从 `100 nm` 提到 `5000 nm`
3. 峰值 `P` 浓度虽然会上升到约 `6.65e11 cm^-3`
4. 但仍远低于 `Ga = 1e16 cm^-3`
5. 因此 `junction depth` 仍然始终为 `0`

这说明在当前模型下：

1. 单纯提高 source 总量几乎不改变结果
2. 当前处于“source 未耗尽、但固态扩散/界面通量受限”的区间

第二组结果说明：

1. 在极高 source (`4e22 cm^-3`, `5000 nm`) 下继续压低 `interfacial_transport_length`
2. 直到 `0.005 nm` 这种几乎不物理的长度量级，才勉强出现：
   - 峰值 `P` 约 `1.33e16 cm^-3`
   - 结深约 `16.7 nm`

当前判断：

1. 若要解释实验里“非融化也能形成明显 junction”，主缺口更像是：
   - 预扩散初始 `P` 轮廓
   - 更真实的 `PSG/SiO2/Si` 界面
   - 或比当前单脉冲热预算更长的有效热历程
2. 审查线已复核第一组高 source 扫描，结论：`通过`

### 文献对比与 60W 探索

本轮先查了公开文献，再把激光功率从 `30 W` 提到 `60 W` 做本地对照。

文献线当前给出的关键结论：

1. `PSG`/`P2O5-SiO2` 体系下，非融化条件并非绝对零掺杂；固态扩散和 drive-in 是真实存在的。
2. 但 ns 级激光若想显著再掺杂，很多结果仍依赖更高局部热预算，或依赖预先存在的炉管扩散发射极。
3. 文献里还明确支持：
   - `PSG/SiO2/Si` 界面会影响 P 注入
   - `SiO2` 可明显抑制由 `PSG` 向 Si 的进一步注入

相关参考入口：

1. [Fraunhofer ISE APCVD PSG + diffusion process](https://publica-rest.fraunhofer.de/server/api/core/bitstreams/d8804028-6aa5-426e-a32a-3ad82a20482a/content)
2. [Fraunhofer ISE APCVD PSG optimisation](https://publica-rest.fraunhofer.de/server/api/core/bitstreams/3fc603c7-9f5c-4373-b141-f5b3054ef2c5/content)
3. [Thin Solid Films 1982: phosphorus diffusion into silicon from CVD PSG](https://doi.org/10.1016/0040-6090(82)90290-5)
4. [PNNL/JAP 2012: model of PSG deposition by POCl3](https://www.pnnl.gov/publications/model-phosphosilicate-glass-deposition-pocl3-control-phosphorus-dose-si)
5. [Energy Procedia 2017: PSG/SiO2 stack and laser doping suitability](https://doi.org/10.1016/j.egypro.2017.09.280)

本地 `60 W` 探索结果：

1. `60 W / 500 kHz = 120 uJ per pulse`
2. 在 `95 um square flat-top` 下，对应 fluence 约 `1.33 J/cm^2`
3. 默认 source 结果在：
   - `outputs/phase3/p60w_default/summary.json`
   - 峰值 Si 表面温度约 `1681.1 K`
   - `max_melt_depth = 0`
   - 峰值 `P` 约 `2.64e20 cm^-3`
   - 结深约 `104.1 nm`
4. 高 source 结果在：
   - `outputs/phase3/p60w_high_source/summary.json`
   - 峰值 `P` 约 `5.34e21 cm^-3`
   - 结深约 `120.9 nm`

审查线结论：`通过`

但要记住一个重要口径：

1. 这两组 `60 W` 算例虽然 `max_melt_depth = 0`
2. 但 `max_liquid_fraction ≈ 0.284`
3. 所以它们并不是“纯固态扩散”极限，而是“接近熔化、已有部分液相权重参与的过渡区”

## 2026-04-08

### 工业基础 emitter 假设已并入

用户指出：工业实践里在激光掺杂前通常已有一道 `POCl3 diffusion`，因此激光时不应从“Si 内 P = 0”起算。

当前已新增可调初始轮廓：

- `initial_profile_kind = erfc_emitter`
- `initial_surface_p_concentration_cm3`
- `initial_junction_depth_nm`

当前口径：

1. 用 `erfc` 型初始 `P` 轮廓近似基础 emitter
2. 假设基础结深 `300 nm`
3. 假设表面 `P` 浓度接近工业发射极的高浓度端，当前测试值取 `3.5e20 cm^-3`

### 文献线当前结论

研究线补充了几条关键结论：

1. 基础 `POCl3` emitter 不会让 `PSG/SiO2` 界面抑制消失
2. 但它会显著降低“还需要从 PSG 再注入多少 P”这件事的重要性
3. 因而最终结深更可能由“已有 emitter + 激光再分布”主导，而不是完全由 `PSG` 额外注入主导

相关参考：

1. [Fraunhofer selective emitter via APCVD PSG deposition](https://publica.fraunhofer.de/entities/publication/c86c1559-3002-44d0-b9a8-e316b9d77be2)
2. [MDPI 2020: Effects of Laser Doping on the Formation of the Selective Emitter of a c-Si Solar Cell](https://www.mdpi.com/2076-3417/10/13/4554)
3. [Thin Solid Films 1982: PSG -> Si solid diffusion](https://doi.org/10.1016/0040-6090(82)90290-5)
4. [Energy Procedia 2017: PSG/SiO2 stack affects laser doping](https://doi.org/10.1016/j.egypro.2017.09.280)

### 60W 下加入基础 emitter 的结果

以 `60 W / 500 kHz / 95 um square flat-top` 为当前激光点，做了两组对照：

1. 只有基础 emitter：
   - `outputs/phase3/p60w_pre_emitter_only/summary.json`
   - 初始结深约 `300.4 nm`
   - 最终结深约 `300.4 nm`
   - 最终峰值 `P` 约 `2.16e20 cm^-3`
2. 基础 emitter + PSG source：
   - `outputs/phase3/p60w_pre_emitter_plus_psg/summary.json`
   - 初始结深约 `300.4 nm`
   - 最终结深约 `300.4 nm`
   - 最终峰值 `P` 约 `4.72e20 cm^-3`

当前判断：

1. 基础 emitter 一旦存在，结深会立刻由已有轮廓主导
2. 在当前 `60 W` 条件下，PSG 额外 source 主要抬高近表面浓度
3. 但并没有明显把 `300 nm` 的结深继续推深
4. 这支持“界面仍限制额外注入，但基础 emitter 已经显著减轻了它对最终结深的主导性”

### 审查线结论

审查线已复核这两组结果，结论：`通过`

同时指出两个口径注意点：

1. 初始峰值 `P` 略低于名义 `3.5e20 cm^-3`，因为当前第一个 Si 网格点不在严格表面，而在约 `13.27 nm`
2. `source=0` 那组里 `final_source_inventory` 字段存在命名口径歧义，更像是边界 sink accounting，而不应直觉理解为“真的长出了一个 source”

### 边界条件文献复核

本轮专门复核了 `PSG -> Si` 表面边界条件的文献口径，并形成了单独报告：

- `docs/boundary-condition-review.md`

当前判断：

1. 现有 Robin 边界不是错误建模，更像一个“有效界面传质”的降阶闭合
2. 它比硬表面浓度更合理，尤其适合有限库存 + 单脉冲 + 1D 扫描阶段
3. 但它还没有显式表示：
   - 前驱体层自身状态
   - `PSG/SiO2/Si` 阻挡
   - moving interface 溶质守恒
   - 表面 out-diffusion / evaporation
4. 因此后续如果要升级，应优先考虑：
   - 显式 source cell
   - 独立 `SiO2` 界面透过系数
   - moving interface + `k(v)` + `J_out`

### 90W 主流边界测试

本轮把扩散边界默认升级为更接近文献主流的口径：

1. `boundary_model = finite_source_cell`
2. `source_exchange_mode = melt_only`
3. 保留基础 emitter 的固态扩散，但把额外 `PSG -> Si` 注入主线收紧到熔融窗口
4. `run_phase3.py` 默认表面反射率同步改为 `9%`

本轮主算例：

- `outputs/phase3/p90w_mainstream_default_source/summary.json`

设定：

1. `90 W`
2. `500 kHz`
3. `95 um` square flat-top
4. `surface_reflectance = 0.09`
5. `300 nm` 基础 emitter
6. 默认 `PSG` source：`2e21 cm^-3`, `100 nm`

结果：

1. 单脉冲 fluence 约 `1.994 J/cm^2`
2. 峰值 Si 表面温度约 `2834.9 K`
3. 最大熔深约 `1115.4 nm`
4. 熔融结束约 `344.4 ns`
5. 最终峰值 `P` 浓度约 `7.882e20 cm^-3`
6. 最终结深约 `606.3 nm`
7. 质量守恒误差约 `8.192e5 atoms/m^2`，相对总库存仍处于浮点舍入量级

当前判断：

1. 在 `90 W / 9%` 这组条件下，模型已经明确进入重熔区
2. 相比 `60 W`，结深从约 `300 nm` 被继续推到约 `476 nm`
3. 这支持“熔融窗口内的额外 PSG 注入”在当前工艺点已经开始显著改变最终 junction
4. 当前正式口径使用 `t_end = 400 ns`，因为 `150 ns` 会截断在未完全凝固状态

### 新的固定流程：结果生成后的研究线对标

用户新增流程要求：

1. 以后每次生成新的模拟结果
2. 研究线都必须读取结果并与其他论文中的典型结果做对比
3. 研究线必须思考：
   - 有没有明显错误
   - 有没有更合理的物理解释
   - 有没有值得立刻尝试的改进项
4. 如果有可改进之处，研究线要先向主线程报告
5. 主线程再决定是否继续修改模型

这条流程已经写入：

- `docs/wenshu-laoge-memory.md`
- `docs/stage-report-template.md`
- `docs/rizhi-wendang-laoge-memory.md`

从这次之后，任何新结果如果没有：

1. 审查线复核
2. 研究线文献对标

都不应被视为完整阶段结果。
### 60W 主流模型重跑正式归档

本轮把 `60W` 两组主流结果正式归档：

1. `outputs/phase3/p60w_mainstream_default_source/summary.json`
2. `outputs/phase3/p60w_mainstream_default_source_nz1200/summary.json`

当前展示口径采用 `nz1200`，因为它在保持 `300 nm` 基础 emitter 的前提下更稳定。

归档结论：

1. 两组结果都已经经过审查线与研究线。
2. `60W` 单脉冲在当前模型下属于接近阈值，但没有发生有效重熔驱入。
3. 结深基本保持 `300 nm` 基础 emitter，不应被解读为显著新 junction。
4. 这轮结果可以正式归档，后续对外展示优先用 `nz1200` 口径。

### Si 内 P profile 片电阻分析输出已接入

本轮在扩散输出中新增了面向片电阻分析的三个标准产物：

1. `silicon_p_profile_sheet_analysis.png`
2. `cumulative_p_dose_vs_depth.png`
3. `silicon_profile_analysis.csv`

它们的作用是把“有没有继续推深 junction”之外的信息也保留下来，尤其是：

1. Si 内总 `P` 轮廓
2. 扣除 `Ga` 补偿后的净施主轮廓
3. 从表面到任意深度的累计剂量

当前 `60W / nz1200` 结果显示，虽然结深基本不变，但基础 emitter 的 Si 内 `P` profile 依然是有效研究对象，并且已经可以直接拿去做后续片电阻模型输入。

### 初始未激活表面 P 层已接入

本轮新增了一个可调初始条件：

1. `initial_inactive_surface_p_concentration_cm3`
2. `initial_inactive_surface_thickness_m`

用途是表示前序工序残留在 Si 表面的化学 `P` 库存，并在初始片电阻分析中与 active emitter 分开。

测试算例：

1. `30 nm`
2. `5e20 cm^-3`
3. 输出目录：`outputs/phase3/p60w_mainstream_with_inactive_surface_p_nz1200`

审查线结论：通过。  
研究线结论：这种建模合理；`initial_active_*` 与 `initial_inactive_*` 可作为后续片电阻研究输入；`final_net_donor_*` 仍应只读成化学上限。

### 初始未激活表面 P 层口径

当前模型支持初始未激活表面 `P` 层，例如 `30 nm / 5e20 cm^-3`。后续阶段归档时，这一层要作为前序工序残留 `P` 单独记账，并在初始片电阻分析里和 `active emitter` 分开记录。

### 研究线长时研究规则

用户已明确允许研究线做长时间持续研究。

从现在开始：

1. 研究线可以长期挂起并持续搜集资料、补充文献和反复对标。
2. 当主线程需要阶段结论时，可以直接中断研究线并要求立即汇报当前最佳结论。
3. 研究线在给出阶段结论后，默认继续之前的研究，而不是结束任务。
4. 后续如果主线程再次需要结论，可以重复采用“中断取结论，再继续研究”的模式。

### 60-90W 功率扫描已归档

本轮已完成 `60-90 W` 功率扫描，使用的当前工艺口径是：

1. `95 um` square flat-top
2. `9%` 反射率
3. `300 nm` 基础 active emitter
4. `30 nm / 5e20 cm^-3` 初始 inactive surface P 层

正式口径采用：

- `outputs/phase3/power_scan_60_90w_dt01`

不再采用：

- `outputs/phase3/power_scan_60_90w`

因为 `dt=0.2 ns` 版本暴露了高功率区时间步敏感性。

当前阶段结论：

1. `60-85 W` 属于接近阈值区
2. `90 W` 首次给出明确非零熔深
3. 当前明显重熔增强阈值大致落在 `85-90 W`
4. 下一轮最值得做的是 `85-90 W` 的更细功率步长扫描

### 60–90W 功率扫描待归档口径

当前这轮功率扫描先记为待归档候选，正式口径优先采用 `dt=0.1` 版本，目录为：

- `C:\Users\User\Desktop\Codex\Diffusion Simulation\outputs\phase3\power_scan_60_90w_dt01`

补充说明：`dt=0.2` 版本已经暴露出高功率时间步敏感性，因此后续正式报告不要把它当成主口径。

等审查线和研究线都回结论后，再写正式阶段报告。

### 主论文草稿入口更新

当前项目的论文式主文档入口已更新为 `docs/laser-psg-phosphorus-doping-paper-draft.md`。后续做阶段报告或总报告时，优先围绕这份草稿收口。

### 新的细时间步扫描待归档

新的细时间步扫描目录已完成：

- `outputs/phase3/power_scan_30_100w_dt005`

这轮先只记为中间状态，等主线程拿到审查线和研究线结论后，再整理正式报告。

### Texture Enhancement 第一版

本轮已把 texture enhancement 的第一版降阶模型并入 Phase 3 主线，目标是先把“制绒对热预算和界面传质的影响”接进 1D 模型，而不是一上来就改成显式 2D/3D 金字塔求解。

当前并入的两类 texture 效应是：

1. 有效光学增强：
   - `R_eff = k_tex * R_flat`
   - 用于把多次反射 / 光陷折成有效表面反射率
2. 有效界面面积增强：
   - `A_factor = A_real / A_proj`
   - 当前支持直接给定，或由理想金字塔侧壁角按 `sec(theta)` 反算

已更新的代码入口：

- `src/laser_doping_sim/phase3_stack_thermal.py`
- `src/laser_doping_sim/phase2_diffusion.py`
- `run_phase3.py`
- `run_phase3_power_scan.py`

已新增的文档入口：

- `docs/literature-usage-register.md`

本轮拆解结果：

1. `60W` 下：
   - `area-only` 基本不生效
   - `optical-only` 轻微降低有效反射后，可以把系统推到界面门刚开始开启的区域
2. `90W` 下：
   - `optical-only` 主要抬高温度与熔深
   - `area-only` 主要抬高近表面 `P` 浓度和累计注入量
   - `both` 最强

审查线结论：

- `通过（带注记）`
- 没发现硬性重复计数
- `source + Si` 继续守恒
- 建议额外输出：
  - `max_surface_liquid_fraction`
  - `cumulative_injected_vs_depletion_relative_error`

研究线结论：

- 当前趋势与文献支持的物理分工一致
- `60W area-only` 不显影是合理的，因为当前默认边界是 `melt_only`
- 下一步最值当的是拆分：
  - 只放大界面面积
  - 只放大 source inventory

本轮相关结果目录：

- `outputs/phase3/texture_cases_60w`
- `outputs/phase3/texture_cases_90w`

本轮相关文档：

- `docs/phase3-analysis.md`
- `docs/phase3-work-report.md`
- `docs/formula-reference-register.md`
- `docs/literature-usage-register.md`

### Texture 反射率口径修正

用户进一步确认：

- `surface_reflectance = 9%` 是实测值

因此后续主线口径改成：

1. 不再把 texture 光学增强额外乘到这 `9%` 上
2. `texture_reflectance_multiplier` 在正式结果里应取 `1.0`
3. 当前 texture 主线只看有效面积增强

这意味着当前正式 texture 结果是：

- `outputs/phase3/texture_cases_60w/area_only`
- `outputs/phase3/texture_cases_90w/area_only`

而 `optical_only` 与 `both` 只保留为敏感性测试目录，不再作为正式校准结果口径。

### Redistribution 研究线确认

用户进一步确认：带超高 inactive 表面 P 层的这组算例，虽然不代表 `PSG` 再注入，但和实验现象相似，因此保留为单独研究方向。

当前正式解释：

- 这是“高初始表面 P 库存的激光重分布”问题

不是：

- “PSG 再注入主导”的问题

当前代表目录：

- `outputs/phase3/texture_cases_60w_area_only_init1e20_inactive1e22`
- `outputs/phase3/texture_cases_90w_area_only_init1e20_inactive1e22`

当前读法要点：

1. `peak_surface_injection_flux = 0`
2. `cumulative_injected_dose = 0`
3. 结果变化来自初始高表面 P 的再分布
4. 这条线后续更适合拿来研究 profile 展宽、结深变化和片电阻相关量

### 30W/60W/90W redistribution 裁剪版 P profile 图

本轮新增了三组 redistribution case 的裁剪版 `P profile` 图，以及合并对比图：

- `outputs/phase3/p_profile_cropped_comparison_30_60_90w.png`

当前先作为待审查、待研究线回执的中间材料，不提前写入正式阶段报告。

### 30W/60W/90W 裁剪图回执补充

审查线结论：这轮 `30/60/90W` 裁剪图没有明显物理或逻辑错误，变化与 summary 一致。唯一提醒是裁剪到 `junction + 50nm` 会隐藏更深尾部剂量信息，必须和全深度图 / 累计剂量图配套解读。

研究线结论：这轮结果符合 redistribution 主线，`30W/60W` 基本不变，`90W` 主要表现为近表面峰值下降和深部展宽；同时要记住当前仍是 `PSG` 再注入几乎为零的 regime。

当前处理：把这条作为可引用的结果补充，但不升级成新 milestone。

### 30–100W / 2W step / dt=0.05ns 完整扫描待回执

本轮已完成新的细时间步完整扫描：

- `C:\Users\User\Desktop\Codex\Diffusion Simulation\outputs\phase3\power_scan_30_100w_step2_dt005_redistribution`

当前已补齐：

1. `30–100W`
2. `2W` 步长
3. `dt = 0.05 ns`
4. 完整总表
5. `json`
6. `manifest`
7. 趋势图

当前口径：先作为待审查线、待研究线简短回执的中间结果保存，不提前写成正式阶段补充。

### 2026-04-09：片电阻后处理首版

新增代码：

- `src/laser_doping_sim/sheet_resistance.py`
- `run_sheet_resistance_cases.py`

本轮目标：

1. 基于已有 `P profile` 结果给出 `Rsh init`
2. 给出激光后 `Rsh af`
3. 用电学上更保守的方式处理薄 inactive 表面 P 层

当前电学口径：

1. `Masetti @ 300 K` 单晶硅电子迁移率
2. 初始 active emitter 视为 fully active
3. 薄 inactive 表面 P 层按 `5%` 活化率计入
4. 激光后 `Rsh_af` 采用：
   - `active emitter redistributed component`
   - `5% * redistributed inactive component`
   - `100% * injected component`

当前输出目录：

- `outputs/phase3/sheet_resistance_inactive5pct_30_60_90`

当前已同步到公式/文献台账：

- `F-032`
- `F-033`
- `F-034`
- `R-021`

当前代表结果：

1. `30 W`: `Rsh_init ≈ 110.51 ohm/sq`, `Rsh_af ≈ 110.51 ohm/sq`
2. `60 W`: `Rsh_init ≈ 110.51 ohm/sq`, `Rsh_af ≈ 109.91 ohm/sq`
3. `90 W`: `Rsh_init ≈ 110.51 ohm/sq`, `Rsh_af ≈ 67.27 ohm/sq`

当前读法：

- `30–60 W` 基本仍是 redistribution 主导，片电阻变化很小
- `90 W` 已经出现明显电学增强，`Rsh` 明显下降
- 这组结果适合先作为“电学趋势估计”，后续仍可再加入更精细 activation / mobility 标定

当前处理：

- 先作为待审查线、待研究线简短回执的中间结果保存
- 等两条线都回结论后，再决定是否扩写成正式阶段补充

### 2026-04-09：measured-profile 导入与 measured-driven 扫描

新增代码：

- `src/laser_doping_sim/measured_profiles.py`
- `prepare_measured_initial_profile.py`

当前输入产物：

- `inputs/measured_profiles/ctv_measured_initial_profile.csv`
- `inputs/measured_profiles/ctv_measured_initial_profile.png`

当前已完成的 measured-driven 扫描目录：

- `outputs/phase3/power_scan_30_60_90w_measured_ctv`

当前处理：

- 先作为待回执的阶段补充保存
- 不提前升级成正式 milestone
- 等审查线和研究线给出简短回执后，再决定是否扩写到正式阶段补充

### 2026-04-09：measured 初始条件重构

本轮 measured 初始条件的核心变化是：

1. RAW 数据改为直接导入：
   - `CTV-ECV-RAW.csv`
   - `CTV-SIMS-RAW.xlsx`
2. `measured` 模式下，`initial total` 现在直接取 `SIMS total`
3. `initial inactive` 现在改为平滑的表面残差估计，不再影响 authoritative total
4. 基于这套新初始条件，`30/60/90W` 的 measured-driven 结果已经重跑

后续正式阶段补充的归档要点可按下面 4 条组织：

1. 输入来源从“已整理 profile”进一步回到原始 `ECV/SIMS RAW`
2. `initial total` 的 authoritative 口径收紧为 `SIMS total`
3. `inactive` 从“参与总量定义”改成“只作为表面残差估计的辅助层”
4. `30/60/90W` 新结果要统一按这套重构后的 measured 初始条件来解释

当前处理：

- 先按待正式归档的阶段补充保存
- 等你后续点名需要时，再扩写成正式阶段报告或正式阶段补充

### 2026-04-09：measured-profile 口径更新与 Rsh Case A/B 对照

本轮 measured-profile 与片电阻后处理的当前归档口径更新为：

1. `measured inactive` 恢复为 `max(SIMS - ECV, 0)`，覆盖上一轮“平滑表面残差估计”的临时口径。
2. `final total` 始终包含 `PSG injected component`，不再把激光后注入量排除在 authoritative final total 外。
3. measured-driven `Rsh` 当前保留两套后处理假设：
   - `Case A`：initial inactive 在 laser 后仍不计为 active，`final_inactive_activation_fraction = 0`
   - `Case B`：initial inactive 在 laser 后全部计为 active，`final_inactive_activation_fraction = 1`

当前输出目录：

- `outputs/phase3/sheet_resistance_measured_ctv_caseA_inactive_stays_inactive`
- `outputs/phase3/sheet_resistance_measured_ctv_caseB_inactive_fully_activated`

当前标准输出：

- `sheet_resistance_summary.json`
- `sheet_resistance_summary.csv`
- `sheet_resistance_bar_chart.png`

当前代表结果：

1. `Case A`：`Rsh_init ≈ 224.32 ohm/sq`；`30W ≈ 223.08`，`60W ≈ 39.67`，`90W ≈ 24.59`
2. `Case B`：`Rsh_init ≈ 224.32 ohm/sq`；`30W ≈ 71.22`，`60W ≈ 26.02`，`90W ≈ 18.60`

当前读法：

- `30W` 对“initial inactive 在 laser 后是否转为 active”最敏感，因为当前 `PSG` 注入仍很小。
- `60W/90W` 下两套假设都给出显著 `Rsh` 下降，但 `Case B` 更激进。
- 这组结果更适合读成 measured 初始条件下的 electrical bounding / sensitivity comparison，而不是唯一实测等效值。

当前处理：

- 先作为待审查线、待研究线简短回执的阶段补充保存
- 在两条线都给出结论之前，不升级成正式 milestone 或正式阶段补充

### 2026-04-09：PSG = surface SIMS 参数修正与 27–36W 低功率扫描

本轮 measured-driven 低功率口径进一步修正为：

1. `source_dopant_concentration_cm3` 提高到 measured surface `SIMS = 4.5913166904198945e21 cm^-3`
2. 初始 inactive baseline activation 取 `0.04448923256987511`，使 `Rsh_init = 180 ohm/sq`
3. 低功率 post-laser inactive activation 取 `0.38734199240748757`，使 `30W -> 110 ohm/sq`
4. 当前低功率 `Rsh` 对照按 `injected_activation_fraction = 0.0` 读取

当前输出目录：

- `outputs/phase3/power_scan_27_36w_measured_ctv_psg_eq_sims`
- `outputs/phase3/sheet_resistance_measured_ctv_psg_eq_sims_27_36_lowpower_calibrated_v2`

当前标准输出：

- `power_scan_summary.json`
- `power_scan_summary.csv`
- `scan_manifest.json`
- `sheet_resistance_summary.json`
- `sheet_resistance_summary.csv`
- `sheet_resistance_bar_chart.png`

当前结果摘要：

1. `27/30/33/36W` 全部满足：
   - `max_liquid_fraction = 0`
   - `max_melt_depth_nm = 0`
   - `cumulative_injected_dose_cm2 = 0`
   - `melt_gate_active_fraction = 0`
2. 这段功率下峰值表面温度约从 `1257 K` 升到 `1577 K`，但仍未进入熔化窗口。
3. `final_peak_p` 与 `junction depth` 基本不变，约为 `4.39e21 cm^-3` 与 `372.8 nm`
4. `Rsh_init = 180 ohm/sq`，`27/30/33/36W` 的 `Rsh_af` 都基本落在 `110 ohm/sq`

当前读法：

- 在当前模型下，`27–36W` 这一段仍是“无熔化、无有效注入”的低功率区间。
- 这组 `Rsh ≈ 110 ohm/sq` 的结果当前应读成低功率后处理激活口径标定值，而不是由熔化注入驱动出来的新 regime。
- 这轮更适合作为 measured-driven 低功率校准补充，而不是新的物理突破点。

当前处理：

- 先作为待审查线、待研究线回执的阶段补充保存
- 在两条线都给出结论之前，不升级成正式 milestone 或正式阶段补充

### 2026-04-09：6W 间隔经验外推补充

本轮已新增 `24–60W`、`6W` 步长的 measured-driven 外推目录：

- `outputs/phase3/power_scan_24_60w_step6_measured_ctv_psg_eq_sims`

当前经验外推表：

- `empirical_rsh_extrapolation_step6.csv`
- `empirical_rsh_extrapolation_step6_clamped.csv`

当前关键结果：

1. 原始经验外推：
   - `24W -> 164.17 ohm/sq`
   - `30W -> 138.10 ohm/sq`
   - `36W -> 105.17 ohm/sq`
2. `42W` 起 raw `final inactive activation > 1`，已明确属于不物理区间：
   - `42W raw f_final_inactive ≈ 1.022`
   - `48W raw f_final_inactive ≈ 2.398`
   - `54W raw f_final_inactive ≈ 5.627`
   - `60W raw f_final_inactive ≈ 13.201`
3. clamped 外推结果：
   - `42W -> 71.28 ohm/sq`
   - `48W -> 71.28 ohm/sq`
   - `54W -> 60.56 ohm/sq`
   - `60W -> 29.77 ohm/sq`

当前解释边界：

- 这组表本质上仍是经验性电学校准外推，不是热扩散层的新 adopted physics。
- `54W` 起热模型已经进入 `partial melt / injection` 过渡区，因此不宜继续用纯低功率经验律做裸外推。
- 后续若引用 `42–60W` 外推值，必须同时写明：
  - `42W` 起 raw activation 已越过物理上限
  - `54W+` 已不再属于单纯低功率、无熔化、无注入的经验校准区间

当前处理：

- 先作为待审查线、待研究线回执的阶段补充保存
- 在两条线都给出结论之前，不升级成正式 milestone 或正式阶段补充

### 2026-04-09：基于实验趋势的低功率经验电学校准

本轮把低功率 `Rsh` 口径进一步改成“按实验趋势拟合的经验性电学校准层”：

实验点为：

1. `24W`：`170.8851 -> 163.13 ohm/sq`
2. `27W`：`171.64 -> 150.38 ohm/sq`
3. `30W`：`175.79 -> 144.95 ohm/sq`
4. `33W`：`161.26 -> 117.588 ohm/sq`

统一 baseline calibration：

- `initial inactive activation = 0.06447924522684517`
- 对应平均 `Rsh_init = 169.893775 ohm/sq`

逐点 final inactive activation：

1. `24W`：`0.08211699366064995`
2. `27W`：`0.1271423637719521`
3. `30W`：`0.15120848835373957`
4. `33W`：`0.3210707049033614`

当前解释边界：

- 在当前 `PSG = surface SIMS + melt_only` 模型下，`24–36W` 的实际热/扩散 summary 仍应读成：
  - `no melt`
  - `no injection`
  - 没有新的热扩散驱动注入证据
- 因此这组低功率拟合参数应归档为“经验性电学校准层”，而不是“热扩散层”或“低功率注入层”。
- 后续如果引用这组参数，要明确它们是为贴近实验 `Rsh` 趋势而引入的 post-processing activation bookkeeping，不应反向解读成模型已经在 `24–36W` 复现了真实熔化/注入物理。

当前处理：

- 先作为待审查线、待研究线回执的阶段补充保存
- 在两条线都给出结论之前，不升级成正式 milestone 或正式阶段补充

### 2026-04-09：PSG 注入活化与初始 inactive 激活的文献笔记

新增文档：

- `docs/laser-activation-literature-notes.md`

本轮把与下列问题最相关的原始文献单独收拢：

1. 激光后 `SIMS total` 与 `ECV active` 的差异该如何理解；
2. 初始 inactive phosphorus 是否可能在激光后重新变成 electrically active；
3. PSG 注入的 phosphorus 是否应直接视为 fully active。

当前项目口径：

- 文献更支持“分桶建模 + 由实验标定活化率”，而不支持一个固定普适活化系数；
- 现阶段把：
  - `initial active`
  - `initial inactive`
  - `PSG injected`
  分别记账，再用 `Rsh`/`ECV`/`SIMS` 去标定各自激活率，是更稳的路线。

### 2026-04-09: 分段 empirical non-active pool activation model 正式接入

本轮实现：

- 新增 `src/laser_doping_sim/activation_models.py`
- `run_sheet_resistance_cases.py` 新增 `piecewise_nonactive_pool` 模式
- 新增参数表 `inputs/activation_models/segmented_nonactive_pool_empirical_24_60w.csv`

当前 adopted electrical-calibration 口径：

- `initial inactive activation = 0.06447924522684517`
- `final non-active pool activation = f_pool(power_w)`
- `final non-active pool = final inactive component + final injected component`

已生成结果：

- 锚点功率复现实验：
  - `outputs/phase3/sheet_resistance_segmented_nonactive_pool_anchor_24_60w/sheet_resistance_summary.csv`
- `6 W` 间隔扫描：
  - `outputs/phase3/sheet_resistance_segmented_nonactive_pool_step6_24_60w/sheet_resistance_summary.csv`
- 实验对照图：
  - `outputs/phase3/sheet_resistance_segmented_nonactive_pool_anchor_24_60w/experiment_comparison.csv`
  - `outputs/phase3/sheet_resistance_segmented_nonactive_pool_anchor_24_60w/experiment_comparison.png`

当前解释边界：

- 这套模型是 measured-profile 驱动的经验电学校准层
- `24–48 W` 主要用于贴合实验 `Rsh`
- `54–60 W` 已进入 partial melt / injection 过渡区，因此该模型应与热/扩散 summary 联合解读，不能单独当成第一性物理

### 2026-04-09: 当前模型总表与工作区文件索引整理完成

新增文档：

- `docs/current-model-summary.md`
- `docs/workspace-file-classification.md`

本轮整理内容：

- 把当前主线模型按“Phase 1 热 -> Phase 2 扩散 -> Phase 3 measured + PSG -> Rsh 后处理”重新总结成一份总表
- 明确区分：
  - 物理主模型
  - empirical electrical calibration layer
- 把工作区内的代码、输入、结果和文档按用途重新分组
- 明确了当前主线结果目录和历史/中间标定目录的区别

当前推荐入口：

- `docs/current-model-summary.md`
- `docs/workspace-file-classification.md`
- `outputs/phase3/power_scan_24_60w_step6_measured_ctv_psg_eq_sims`
- `outputs/phase3/sheet_resistance_segmented_nonactive_pool_anchor_24_60w`

### 2026-04-09: 项目总教程与当前模型总结合并为中英文双版本

本轮新增：

- `docs/project_model_walkthrough_zh.md`
- `docs/project_model_walkthrough_en.md`

本轮调整：

- `docs/project_total_walkthrough_obsidian.md` 改为总教程索引页
- `docs/current-model-summary.md` 改为当前模型索引页

当前推荐入口：

- 中文：
  - `docs/project_model_walkthrough_zh.md`
- English:
  - `docs/project_model_walkthrough_en.md`

合并原则：

- 把“教程型 walkthrough”
- 和“当前主线模型总结”

收成同一套主文档，避免内容继续分叉。

### 2026-04-09: 固相注入开启后的 measured 主线快速扫描

本轮背景：

- 用户已把界面 source exchange 口径改为 `all_states`
- 即 `source_exchange_mode = all_states`
- 这表示固相未融化时也允许发生 `PSG -> Si` 注入

本轮新增结果：

- 热/扩散扫描：
  - `outputs/phase3/power_scan_24_60w_step2_measured_ctv_psg_eq_sims_allstates/power_scan_summary.csv`
- `Rsh` 后处理：
  - `outputs/phase3/sheet_resistance_dual_channel_step2_24_60w_allstates/sheet_resistance_summary.csv`

本轮设置：

- measured initial profile:
  - `inputs/measured_profiles/ctv_measured_initial_profile.csv`
- `PSG` phosphorus concentration:
  - `4.5913166904198945e21 cm^-3`
- surface reflectance:
  - `0.09`
- boundary model:
  - `finite_source_cell`
- source exchange mode:
  - `all_states`
- grid:
  - `nz = 1200`
- time window:
  - `t_end = 400 ns`

关键结论：

- 与旧的 `melt_only` 版本相比，`24–52 W` 的 `cumulative_injected_dose_cm2` 从严格 `0` 变成了非零
- 但该非零注入仍然很小，量级约 `1e2–1e6 cm^-2`
- `54–60 W` 的热/扩散结果几乎不变，因为该区本来就已进入明显液相注入窗口
- 在当前双通道 activation 后处理下，`Rsh` 曲线与旧版本数值上保持一致

当前解释：

- 固相注入这次首先改变的是“化学注入账”
- 但由于低功率段的注入量极小，且当前 dual-channel activation table 在该段仍采用 `eta_inj = 0`
- 所以这轮 `Rsh` 结果没有被拉动

当前建议：

- 如果后续要让这次参数修改真正进入电学预测，应重标低功率段 `eta_inj(power)` 或建立新的 solid-state injection electrical-activation 假设

### 2026-04-09: 高功率段改用细时间步并重做单调经验闭合

问题背景：

- 用户指出 `54–60 W` 段的 `Rsh` 结果异常，不符合随功率升高而递减的直觉趋势
- 先前 `all_states` + `dt = 0.2 ns` 的结果在该段表现出明显非单调：
  - `54 W -> 82`
  - `56 W -> 55.67`
  - `58 W -> 65.53`
  - `60 W -> 69`

本轮诊断：

- 用 `dt = 0.05 ns` 重跑 `54–60 W`
- 结果显示先前 `dt = 0.2 ns` 在该段给出了明显不稳的热结果：
  - `56/58/60 W` 不再出现先前那样的大熔深
  - 细时间步下该段主要表现为 partial-liquid-fraction 上升，而非稳定的 fully molten 深熔

细时间步结果目录：

- `outputs/phase3/power_scan_54_60w_step2_dt005_measured_ctv_psg_eq_sims_allstates`
- `outputs/phase3/power_scan_48_60w_step2_dt005_measured_ctv_psg_eq_sims_allstates`

本轮新方法：

- 新增脚本：
  - `run_dual_channel_monotonic_segment_refit.py`
- 方法：
  - 使用 `48/54/60 W` 实验点作为锚点
  - 对 `50/52/56/58 W` 用线性插值得到单调下降的 target `Rsh`
  - 在 `48–60 W` 段只反解 `effective_final_inactive_activation_fraction`
  - `effective_final_injected_activation_fraction` 在该段固定为 `0`

新 refit 结果：

- activation table:
  - `outputs/phase3/dual_channel_monotonic_segment_refit_48_60w_dt005_allstates/dual_channel_activation_model_monotonic_segment_refit.csv`
- Rsh summary:
  - `outputs/phase3/sheet_resistance_dual_channel_48_60w_dt005_monotonic_segment_refit/sheet_resistance_summary.csv`

当前高功率段经验结果：

- `48 W -> 89`
- `50 W -> 86.67`
- `52 W -> 84.33`
- `54 W -> 82`
- `56 W -> 77.67`
- `58 W -> 73.33`
- `60 W -> 69`

当前解释：

- 这轮做的是“高功率段单调经验闭合”
- 它解决的是输出趋势异常问题
- 但它并不意味着 `48–60 W` 的真实活化物理已经完全确定
- 其中一个关键信号是：
  - `effective_final_inactive_activation_fraction`
  - 在 `58 W` 约 `0.943`
  - 到 `60 W` 回落到约 `0.868`

这表示：

- `Rsh` 趋势已经被修正为单调
- 但高功率段的“有效活化参数”仍在吸收未建模物理
- 后续仍应考虑：
  - 更物理的界面模型
  - 初始 inactive 再激活与 injected P 电活化的进一步分离
