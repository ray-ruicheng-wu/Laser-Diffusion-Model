# 从 PSG 前驱体层到硅中激光磷掺杂的 1D 瞬态模型
## 含基础发射极、未激活表面残留磷层与 60-90W 功率扫描的论文式草稿

## 摘要

本文建立了一套用于描述 `532 nm` 脉冲激光作用下 `PSG` 前驱体向硅中输运磷的 `1D` 瞬态模型。模型面向这样一个工艺场景：硅片在激光处理前已经具有一层由 `POCl3` 扩散形成的基础 `P` 发射极，同时表面还保留一层高浓度、但初始电学上不计入活化施主的残留 `P` 层；激光照射后，体系经历快速升温、接近熔化或局部熔化、以及随后的磷再分布过程。本文给出了热学、相变、界面供源和扩散的耦合方程，解释每条公式采用的原因、它们之间的逻辑关系以及在代码中的对应实现。

当前正式结果基于以下口径：

1. 波长 `532 nm`
2. 频率 `500 kHz`
3. 光斑 `95 um` square flat-top
4. 表面反射率 `9%`
5. 基础 active emitter：表面 `P = 3.5e20 cm^-3`，结深 `300 nm`
6. 初始 inactive surface P layer：厚度 `30 nm`，浓度 `5e20 cm^-3`
7. 时间步长 `dt = 0.1 ns`

在该口径下完成的 `60-90 W` 功率扫描显示：`60-85 W` 处于接近阈值区，结深由约 `302 nm` 缓慢增加至约 `345 nm`，但未出现按当前统计定义可分辨的非零熔深；到 `90 W` 时首次出现明确非零熔深，约 `346 nm`，最终结深约 `371 nm`。因此，在当前模型中，明显的重熔增强阈值大致位于 `85-90 W` 之间。

---

## 1. 研究背景与目标

激光掺杂并不是简单的“表面加热 + 立即形成深结”。真实工艺往往包含三个阶段的叠加：

1. 前序扩散工艺已经在硅中留下基础发射极
2. 表面前驱体层为激光过程提供额外磷源
3. 激光只在极短时间内改变热历史与局部输运能力

因此，若想得到对实验更有解释力的模型，至少要同时回答四个问题：

1. 激光功率如何转化成单脉冲 `fluence`
2. 这份能量如何在 `PSG/Si` 双层中沉积并形成瞬态温度场
3. 温度场是否足以让表面或次表层硅进入液相
4. 在固态、准熔化和熔化条件下，磷的再分布各由什么机制主导

本文的目标不是给出“最终发表版”的全物理模型，而是给出一份当前项目主线的、可以复现、可以继续扩展、并且能解释已有扫描结果的论文式说明。

---

## 2. 物理对象与建模范围

### 2.1 几何与层结构

当前模型只求解法向深度方向，因此是 `1D` 模型。层结构写成：

1. 顶部 `PSG` 有效层
2. 下方硅基底

其中 `PSG` 在当前阶段被近似为：

`PSG ≈ phosphosilicate glass ≈ P2O5-SiO2 glass ≈ phosphorus-rich SiO2 layer`

这样做的原因是：

1. 文献中 `POCl3` 扩散后形成的表层通常被描述为 `PSG`
2. `PSG` 的热学和光学量级更接近被磷改性的 `SiO2`
3. 这允许我们先保留“高浓度表面磷源”的本质，而不必一开始就引入完整 `PSG/SiO2/Si` 三层光学传输矩阵模型

### 2.2 初始掺杂状态

当前初始状态由两部分叠加：

1. `active emitter`
2. `inactive residual P`

前者代表前序扩散已经形成并参与初始片电阻的活化发射极；后者代表表面残留的化学磷库存，初始时不计入活化施主，但在后续激光热历史下可能重新参与输运。

### 2.3 当前模型显式包含的物理

本文所对应的主线模型显式包含：

1. 激光功率到单脉冲能量与 `fluence` 的换算
2. `PSG/Si` 双层瞬态热传导
3. `Si` 的焓法相变
4. 固态与液态磷扩散
5. 显式有限表面供源单元
6. 初始 active/inactive 磷分解
7. Si 内总剂量与净施主剂量输出

### 2.4 当前模型尚未包含的物理

为了避免过度解读，必须明确当前尚未包含：

1. `2D` 横向热扩散和正方形光斑边缘效应
2. 显式 `PSG/SiO2/Si` 三层独立界面阻挡
3. 液态对流
4. 表面蒸发 / out-diffusion / ablation
5. 再凝固分配系数 `k(v)` 与 solute trapping
6. 真正的电活化模型和迁移率模型

---

## 3. 测试方法

### 3.1 总体方法

测试方法由三部分组成：

1. 先求热场
2. 再用热场驱动掺杂扩散
3. 最后对不同功率做扫描

更具体地说，单个工况按如下流程进行：

1. 根据 `P_avg`、`f` 和光斑面积换算单脉冲能量与 `fluence`
2. 在 `PSG/Si` 双层上求解热传导和相变
3. 将双层热结果裁成“仅含 Si 子域”的时间-深度热历史
4. 用该热历史驱动 `P(z,t)` 扩散
5. 输出结深、峰值浓度、总剂量、累计剂量曲线和图表

### 3.2 数值求解

热学与扩散都采用隐式离散，原因是：

1. 纳秒时间尺度下热源变化很快
2. 相变和高浓度梯度会带来较强刚性
3. 显式方法在可接受时间步下会更不稳定

当前数值实现为：

1. 空间：均匀 `1D` 网格
2. 时间：隐式推进
3. 热学非线性：Picard 迭代
4. 扩散系数跨界面：谐和平均
5. 线性代数：稀疏三对角系统

### 3.3 正式结果的稳定性口径

本项目先前做过一轮 `dt = 0.2 ns` 的功率扫描，但高功率区出现了 `85 W` 与 `90 W` 的非物理倒挂。因此当前正式扫描改用 `dt = 0.1 ns`。这件事本身也属于测试方法的一部分，即：

1. 先跑粗时间步扫描
2. 发现异常后做时间步敏感性检查
3. 用更稳定的扫描作为正式结果

这也是本文为什么把 `dt = 0.1 ns` 扫描定义为正式读数的原因。

---

## 4. 控制方程与公式体系

这一节是全文核心。每条公式都说明三件事：

1. 它是什么
2. 为什么要用它
3. 它与前后公式的关系是什么

为便于追踪，下面保留项目内部的 `F-ID` 编号。

### 4.1 激光输入换算：功率到单脉冲 fluence

对应 `F-017`

\[
E_{\mathrm{pulse}}=\frac{P_{\mathrm{avg}}}{f}
\]

\[
F=\frac{E_{\mathrm{pulse}}}{A_{\mathrm{spot}}}
\]

其中：

1. \(P_{\mathrm{avg}}\) 是平均功率
2. \(f\) 是脉冲重复频率
3. \(A_{\mathrm{spot}}\) 是光斑面积
4. \(F\) 是单脉冲 `fluence`

使用原因：

1. 实验上最容易直接给出的是平均功率和频率
2. 热方程真正需要的不是平均功率，而是单脉冲沉积能量
3. 若没有这一步，热源项 \(Q(z,t)\) 没法正确标定

与其他公式的关系：

1. 它给出热源标定所需的总能量尺度
2. 直接进入时间高斯脉冲和空间吸收方程

在当前扫描中，`95 um` square flat-top 下：

1. `60 W` 对应 `1.330 J/cm^2`
2. `90 W` 对应 `1.994 J/cm^2`

### 4.2 时间脉冲包络

该部分在代码里由高斯脉冲实现，实际作用是把总能量沿时间分布开：

\[
I(t)=I_0 \exp\left(-\frac{(t-t_{\mathrm{peak}})^2}{2\sigma_t^2}\right)
\]

其中：

1. \(t_{\mathrm{peak}}\) 控制脉冲峰值在时间窗口中的位置
2. \(\sigma_t\) 由 `FWHM` 换算

使用原因：

1. 纳秒激光不是恒定热流
2. 热峰值、相变开始时间和扩散窗口长度都由时间包络决定

与其他公式的关系：

1. 它与 `fluence` 一起决定瞬时热流强度
2. 它直接进入空间热源 \(Q(z,t)\)

### 4.3 双层空间热源

对应 `F-002` 与 `F-016`

对 `PSG` 层：

\[
Q_{\mathrm{PSG}}(z,t)\propto (1-R) I(t)\exp\left(-\frac{z}{\delta_{\mathrm{PSG}}}\right)
\]

对 `Si` 层：

\[
Q_{\mathrm{Si}}(z,t)\propto (1-R)I(t)\exp\left(-\frac{h_{\mathrm{PSG}}}{\delta_{\mathrm{PSG}}}\right)
T_{\mathrm{int}}
\exp\left(-\frac{z-h_{\mathrm{PSG}}}{\delta_{\mathrm{Si}}}\right)
\]

其中：

1. \(R\) 是表面反射率
2. \(\delta_{\mathrm{PSG}}, \delta_{\mathrm{Si}}\) 分别是 `PSG` 和 `Si` 的吸收深度
3. \(h_{\mathrm{PSG}}\) 是 `PSG` 厚度
4. \(T_{\mathrm{int}}\) 是 `PSG/Si` 界面透过因子

使用原因：

1. 这是从实验参数到热沉积的最短路径
2. 当前阶段没有上完整 TMM，这个最小模型已经能表达“表面反射 + 层内衰减 + 界面透射”的主效应

与其他公式的关系：

1. 它是热方程中的 \(Q(z,t)\)
2. \(R\) 与光学预算直接影响温升上限
3. 吸收深度和 `PSG` 厚度共同决定能量更多落在 `PSG` 还是 `Si`

### 4.4 双层瞬态热传导方程

对应 `F-001` 和 `F-014`

\[
\rho_j c_{p,j}^{\mathrm{eff}}(T)\frac{\partial T_j}{\partial t}

=
\frac{\partial}{\partial z}
\left(
k_j(T)\frac{\partial T_j}{\partial z}
\right)
Q_j(z,t)
\]

其中：

1. \(j\) 表示 `PSG` 或 `Si`
2. \(\rho_j\) 是密度
3. \(c_{p,j}^{\mathrm{eff}}\) 是有效比热
4. \(k_j\) 是导热率

使用原因：

1. 这是所有后续过程的母方程
2. 掺杂扩散不直接看功率，而是看温度历史
3. 若热模型不可信，后续扩散和结深都没有物理基础

与其他公式的关系：

1. 左侧储热项由相变公式修正
2. 右侧热源来自上一节的激光吸收公式
3. 求得的 \(T(z,t)\) 又反过来驱动液相分数与扩散系数

### 4.5 焓法与表观热容

对应 `F-003`

\[
c_p^{\mathrm{eff}}(T)=c_p(T)+c_{\mathrm{latent}}(T)
\]

使用原因：

1. 若直接追踪固液界面，数值实现会更复杂
2. 焓法允许把潜热并入有效比热中
3. 对本项目当前的 `1D` 相变建模是一个稳妥选择

与其他公式的关系：

1. 它直接修改热方程左端储热能力
2. 因此会压住温度上升，形成熔点附近的潜热平台
3. 这一平台正是功率扫描中 `60-85 W` 接近阈值区的重要原因

### 4.6 液相分数

对应 `F-004`

\[
f_l(T)\in[0,1]
\]

并在熔点附近用窄的 `mushy zone` 平滑过渡。

使用原因：

1. 扩散系数不能用一个突变开关控制
2. 需要一个连续变量把“固态到液态”的输运增强平滑表达出来

与其他公式的关系：

1. 它来自温度场 \(T(z,t)\)
2. 又进入有效扩散系数 \(D_{\mathrm{eff}}\)
3. 还进入界面注入开关 \(H(f_l-f_{\mathrm{th}})\)

当前一个重要实现细节是：

1. `melt_depth` 的统计使用较严格的阈值：`f_l > 0.5`
2. `melt_only` 注入使用较宽松的阈值：`f_l > 0.01`

这就是为什么当前扫描中会出现：

1. `60-85 W` 没有正式非零熔深
2. 但仍然存在非零注入和结深增长

这是当前实现的一个物理上可解释、但命名上尚待统一的点。

### 4.7 磷扩散主方程

对应 `F-005`

\[
\frac{\partial C}{\partial t}
=
\frac{\partial}{\partial z}
\left[
D(T,f_l)\frac{\partial C}{\partial z}
\right]
\]

其中 \(C(z,t)\) 是 Si 中的总磷浓度。

使用原因：

1. 激光改变的是输运系数和时间窗口
2. 真正要输出的掺杂轮廓由这个方程决定

与其他公式的关系：

1. \(D\) 不再是常数，而由温度与液相分数控制
2. 表面边界通量由 source cell 与注入公式给定

### 4.8 固液统一有效扩散系数

对应 `F-006`

\[
D_{\mathrm{eff}}(T,f_l)=D_s(T)(1-f_l)+D_l(T)f_l
\]

使用原因：

1. 直接把固态和液态输运能力统一到一个公式里
2. 避免扩散系数在界面处发生数值不连续

与其他公式的关系：

1. 其中 \(D_s\) 与 \(D_l\) 分别由 Arrhenius 公式给出
2. \(f_l\) 完全由热模型提供
3. 所以这是热场与扩散场的核心耦合桥梁

### 4.9 固态 Arrhenius 扩散

对应 `F-019`

\[
D_s(T)=D_{0,s}\exp\left(-\frac{E_{a,s}}{k_B T}\right)
\]

使用原因：

1. 即使在未明显熔化时，基础 emitter 也会发生极弱重分布
2. 完全把固态扩散设成零，会误删真实物理

与其他公式的关系：

1. 它是 \(D_{\mathrm{eff}}\) 的固态端
2. 当 \(f_l\to 0\) 时，扩散主方程退化为纯固态扩散

但要强调：

1. 在纳秒尺度和当前温度下，固态扩散长度极小
2. 它更多决定“轮廓微调”，而不是大尺度结深推进

### 4.10 液态 Arrhenius 扩散

对应 `F-007`

\[
D_l(T)=D_{0,l}\exp\left(-\frac{E_{a,l}}{k_B T}\right)
\]

使用原因：

1. 一旦进入液相，磷输运能力会陡增
2. 激光掺杂之所以会在跨阈值后突然增强，正是因为这一项开始主导

与其他公式的关系：

1. 当 \(f_l\to 1\) 时，\(D_{\mathrm{eff}}\to D_l\)
2. 因此热模型一旦给出明确熔化，扩散场会迅速响应

### 4.11 有限表面供源单元

对应 `F-008` 与 `F-022`

\[
\Gamma_{\mathrm{src}}(0)=C_{\mathrm{src}} h_{\mathrm{src}}
\]

\[
C_{\mathrm{src,cell}}=
\min
\left(
C_{\mathrm{src,max}},
\frac{\Gamma_{\mathrm{src}}}{h_{\mathrm{src}}}
\right)
\]

其中：

1. \(\Gamma_{\mathrm{src}}\) 是单位面积源库存
2. \(h_{\mathrm{src}}\) 是等效 source thickness

使用原因：

1. 真正的 `PSG` 不是无限 reservoir
2. 若直接用固定表面浓度，会高估长期供源能力
3. 显式 source cell 更接近文献中的主流写法

与其他公式的关系：

1. 它决定界面通量公式中的供源浓度
2. 又通过质量守恒与 Si 内增加的总库存相耦合

### 4.12 熔化窗口控制的界面注入

对应 `F-025`

\[
J_{\mathrm{in}}
=
H(f_l-f_{\mathrm{th}})
h_m
\max(0,C_{\mathrm{src,cell}}-C_{\mathrm{surf}})
\]

\[
h_m=\frac{D_{\mathrm{surface}}}{L_{\mathrm{tr}}}
\]

其中：

1. \(H\) 是 Heaviside 型开关
2. \(f_{\mathrm{th}}\) 是界面注入阈值
3. \(L_{\mathrm{tr}}\) 是界面等效传质长度

使用原因：

1. 当前主线想表达的是“额外的 PSG 注入主要在熔化窗口内发生”
2. 它比硬 `Dirichlet` 表面浓度更稳健
3. 也比完全不考虑界面限制更接近实验直觉

与其他公式的关系：

1. \(D_{\mathrm{surface}}\) 来自 \(D_{\mathrm{eff}}\)
2. \(f_l\) 来自热模型
3. \(C_{\mathrm{src,cell}}\) 来自 source cell 库存
4. \(C_{\mathrm{surf}}\) 来自扩散场当前表面值

因此，这一条公式实际上是“热场、扩散场、供源场”三者的耦合交点。

### 4.13 基础发射极初始轮廓

对应 `F-021`

\[
C_{\mathrm{active}}(z,0)=C_s\,
\mathrm{erfc}\left(\frac{z}{2L}\right)
\]

并用

\[
C_{\mathrm{active}}(x_j,0)=C_{\mathrm{bg}}
\]

确定扩散长度 \(L\)。

使用原因：

1. `POCl3` 扩散的基础发射极在很多情况下可以先用常量源扩散解近似
2. 这使“激光前已有结深”可以明确写进初始条件

与其他公式的关系：

1. 它决定了激光前的 active donor 基线
2. 后续所有激光增强都应与这条基线对比，而不是与零掺杂对比

### 4.14 初始未激活表面磷层

对应 `F-027`

\[
C_{\mathrm{inactive}}(z,0)=
\begin{cases}
C_{\mathrm{inactive},0}, & 0\le z \le h_{\mathrm{inactive}} \\
0, & z > h_{\mathrm{inactive}}
\end{cases}
\]

总初始浓度写成：

\[
C(z,0)=C_{\mathrm{active}}(z,0)+C_{\mathrm{inactive}}(z,0)
\]

使用原因：

1. 实验前序工序可能在表面留下高浓度化学磷库存
2. 这些 P 不应自动计入初始片电阻
3. 但它们又不能在化学质量守恒中被忽略

与其他公式的关系：

1. 它增加总化学 `P profile`
2. 但初始 active donor 仍只由前一节的 emitter 给出
3. 这为后续片电阻模型提供“active / inactive 分账”

### 4.15 结深定义

当前结深以总磷浓度与背景 `Ga` 浓度的交点定义：

\[
C_P(x_j)=C_{\mathrm{Ga}}
\]

使用原因：

1. 它给出一个稳定、易比较的几何指标
2. 对不同功率点做扫描时，趋势清晰

与其他公式的关系：

1. 结深是扩散方程的后处理结果
2. 它不能代替剂量，也不能代替片电阻

### 4.16 累计剂量与净施主剂量

对应 `F-026`

\[
Q_P(z)=\int_0^z C_P(x)\,dx
\]

\[
Q_{\mathrm{net}}(z)=\int_0^z \max(C_P(x)-C_{\mathrm{Ga}},0)\,dx
\]

使用原因：

1. 仅看结深会丢失表层高浓度信息
2. 片电阻研究更关心整个导电层里的积分剂量
3. 因此必须显式输出累计剂量曲线

与其他公式的关系：

1. 它建立在扩散结果 \(C_P(z)\) 之上
2. 又为下一步片电阻积分模型提供输入

### 4.17 公式之间的总关系

如果把全模型压缩成一条耦合链，可以写成：

\[
(P_{\mathrm{avg}}, f, A_{\mathrm{spot}})
\rightarrow
F
\rightarrow
I(t)
\rightarrow
Q(z,t)
\rightarrow
T(z,t)
\rightarrow
f_l(T), D_s(T), D_l(T)
\rightarrow
D_{\mathrm{eff}}(T,f_l)
\]

\[
\bigl(C_{\mathrm{src,cell}}, f_l, C_{\mathrm{surf}}\bigr)
\rightarrow
J_{\mathrm{in}}
\]

\[
\bigl(C(z,0), D_{\mathrm{eff}}, J_{\mathrm{in}}\bigr)
\rightarrow
C(z,t)
\rightarrow
\{x_j, Q_P, Q_{\mathrm{net}}\}
\]

这条链正是当前代码里热、相变、供源和扩散的完整耦合逻辑。

---

## 5. 结果

### 5.1 当前正式功率扫描

正式扫描目录：

- [power_scan_60_90w_dt01](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_90w_dt01)

主表见：

- [power_scan_summary.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_90w_dt01/power_scan_summary.csv)

结果如下：

| Power | Fluence | Peak Si Surface T | Max Liquid Fraction | Max Melt Depth | Final Peak P | Final Junction Depth |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `60 W` | `1.330 J/cm^2` | `1678.6 K` | `0.161` | `0 nm` | `8.594e20 cm^-3` | `302.4 nm` |
| `65 W` | `1.440 J/cm^2` | `1678.1 K` | `0.145` | `0 nm` | `8.578e20 cm^-3` | `305.0 nm` |
| `70 W` | `1.551 J/cm^2` | `1681.0 K` | `0.265` | `0 nm` | `8.075e20 cm^-3` | `312.1 nm` |
| `75 W` | `1.662 J/cm^2` | `1682.2 K` | `0.317` | `0 nm` | `7.942e20 cm^-3` | `320.2 nm` |
| `80 W` | `1.773 J/cm^2` | `1683.2 K` | `0.364` | `0 nm` | `7.957e20 cm^-3` | `330.2 nm` |
| `85 W` | `1.884 J/cm^2` | `1685.1 K` | `0.453` | `0 nm` | `8.136e20 cm^-3` | `344.7 nm` |
| `90 W` | `1.994 J/cm^2` | `1690.1 K` | `0.700` | `346.2 nm` | `8.593e20 cm^-3` | `371.4 nm` |

### 5.2 结果图

当前正式图表包括：

1. [power_vs_peak_temperature.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_90w_dt01/power_vs_peak_temperature.png)
2. [power_vs_melt_depth.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_90w_dt01/power_vs_melt_depth.png)
3. [power_vs_junction_depth.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_90w_dt01/power_vs_junction_depth.png)
4. [power_vs_final_peak_p.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_90w_dt01/power_vs_final_peak_p.png)
5. [power_vs_final_net_donor_sheet_dose.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_90w_dt01/power_vs_final_net_donor_sheet_dose.png)

### 5.3 Si 内 P profile 与片电阻前置输入

以带 inactive surface P 的 `60 W` 基线为例：

- [summary.json](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/p60w_mainstream_with_inactive_surface_p_nz1200/diffusion/summary.json)
- [silicon_p_profile_sheet_analysis.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/p60w_mainstream_with_inactive_surface_p_nz1200/diffusion/silicon_p_profile_sheet_analysis.png)
- [cumulative_p_dose_vs_depth.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/p60w_mainstream_with_inactive_surface_p_nz1200/diffusion/cumulative_p_dose_vs_depth.png)
- [silicon_profile_analysis.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/p60w_mainstream_with_inactive_surface_p_nz1200/diffusion/silicon_profile_analysis.csv)

当前关键量为：

1. `initial_sheet_dose ≈ 3.5022e15 cm^-2`
2. `initial_active_sheet_dose ≈ 1.9958e15 cm^-2`
3. `initial_inactive_sheet_dose ≈ 1.5065e15 cm^-2`
4. `initial_net_donor_sheet_dose ≈ 1.9954e15 cm^-2`

因此，对片电阻研究来说，当前真正可直接拿来做输入的是：

1. `initial_active_*`
2. `initial_inactive_*`
3. `total P profile`
4. `cumulative dose`

而不是直接把最终化学总量当成电活化载流子。

---

## 6. 结果解释

### 6.1 为什么 60-85W 已有结深增长，但还没有正式熔深

原因不是单一的，而是当前模型定义共同决定的：

1. 温度已经逼近熔点
2. `liquid fraction` 在界面附近已非零
3. 界面注入开关使用的是 `f_l > 0.01`
4. 熔深统计使用的是更严格的 `f_l > 0.5`

所以在当前实现里，`60-85 W` 更合理的读法是：

1. 接近阈值
2. 存在“准熔化注入”
3. 但尚未形成按当前定义可统计的明确熔深

### 6.2 为什么 90W 才出现明显跨阈值响应

本质原因是潜热平台终于被跨过去了：

1. 当功率继续增加，热方程先被潜热“吃掉”一大段能量
2. 一旦表面温度稳定越过熔点并维持一段时间，液相扩散才真正进入主导
3. 这时 \(D_l\) 和 \(J_{\mathrm{in}}\) 同时增强，结深也开始明显增加

### 6.3 研究线与审查线对本轮结果的共同判断

当前正式结论是：

1. `dt = 0.1 ns` 的正式扫描整体趋势可信
2. 明显重熔增强阈值目前落在 `85-90 W`
3. 但 `melt depth` 和 `melt-only injection` 的判据还没有完全统一

因此，当前结果适合：

1. 趋势判断
2. 参数扫描
3. 阈值区间定位

但尚不适合被过度解读为“发表级最终定量值”。

---

## 7. 可复现方法

### 7.1 运行 60-90W 扫描

```powershell
cd "C:\Users\User\Desktop\Codex\Diffusion Simulation"
python .\run_phase3_power_scan.py --output-dir outputs/phase3/power_scan_60_90w_dt01 --dt-ns 0.1
```

### 7.2 运行单个带 inactive surface P 的 60W 工况

```powershell
python .\run_phase3.py `
  --output-dir outputs/phase3/p60w_mainstream_with_inactive_surface_p_nz1200 `
  --average-power-w 60 `
  --surface-reflectance 0.09 `
  --boundary-model finite_source_cell `
  --source-exchange-mode melt_only `
  --initial-profile-kind erfc_emitter `
  --initial-surface-p-concentration-cm3 3.5e20 `
  --initial-junction-depth-nm 300 `
  --initial-inactive-surface-p-concentration-cm3 5.0e20 `
  --initial-inactive-surface-thickness-nm 30 `
  --t-end-ns 400 `
  --nz 1200
```

### 7.3 运行单个 90W 工况

```powershell
python .\run_phase3.py `
  --output-dir outputs/phase3/p90w_mainstream_with_inactive_surface_p_nz1200_dt01 `
  --average-power-w 90 `
  --surface-reflectance 0.09 `
  --boundary-model finite_source_cell `
  --source-exchange-mode melt_only `
  --initial-profile-kind erfc_emitter `
  --initial-surface-p-concentration-cm3 3.5e20 `
  --initial-junction-depth-nm 300 `
  --initial-inactive-surface-p-concentration-cm3 5.0e20 `
  --initial-inactive-surface-thickness-nm 30 `
  --t-end-ns 400 `
  --nz 1200 `
  --dt-ns 0.1
```

---

## 8. 局限性与下一步

### 8.1 当前局限

本文模型仍有以下核心限制：

1. 仍是 `1D`
2. 尚未显式离散独立 `SiO2` 阻挡层
3. 尚未包含 `k(v)` 与 solute trapping
4. 尚未区分化学磷与电活化磷的动力学转化
5. 尚未引入迁移率模型，因此还不能直接给出最终可信 `Rsh`

### 8.2 最值得做的下一步

下一步最有价值的工作顺序是：

1. 在 `85-90 W` 做更细步长扫描，例如 `1-2 W`
2. 再做更细 `dt` 收敛检查，例如 `0.05 ns`
3. 统一“熔深统计判据”和“melt-only 注入判据”
4. 引入 `active donor + mobility` 片电阻模型
5. 之后再升级到显式 `PSG/SiO2/Si` 与 moving interface

---

## 9. 结论

本文给出的不是一个孤立公式集合，而是一条完整耦合链：

1. 激光功率决定单脉冲能量与 `fluence`
2. `fluence` 决定双层热源
3. 双层热源决定温度历史
4. 温度历史决定液相分数与扩散系数
5. 液相分数与 source cell 一起决定界面注入
6. 扩散方程最终决定 `P profile`、结深和累计剂量

在当前正式口径下，`60-85 W` 属于接近阈值区，而 `90 W` 首次给出明确非零熔深。结合当前功率扫描，明显的重熔增强阈值大致位于 `85-90 W` 之间。

同时，本文也强调了一个对实验很重要的结论：即使结深没有显著继续推深，`Si` 内部的 `P profile`、累计剂量和 active/inactive 分账仍然是有价值的输出，因为它们正是后续片电阻分析的基础输入。

---

## 参考文献

1. Crank, J. *The Mathematics of Diffusion*. [Link](https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf)
2. Green, M. A. Optical parameters of intrinsic silicon at 300 K. [Link](https://subversion.xray.aps.anl.gov/AGIPD_TCAD/PyTCADTools/Attenuation/Silicon_absorption_coeff_visible_photon.pdf)
3. Hassan, M. et al. Unified model for laser doping of silicon from precursor layers. [Link](https://www.mdpi.com/1996-1944/14/9/2322)
4. Fell, A. et al. Fraunhofer ISE finite-source laser doping modeling reference. [Link](https://publica-rest.fraunhofer.de/server/api/core/bitstreams/a4616ec1-fd19-426e-b904-4f6920a07805/content)
5. Lill, H. et al. Influence of precursor layer ablation on laser doping and contact formation. [Link](https://www.mdpi.com/1996-1944/10/2/189)
6. Werner, J. et al. Suitability of industrial POCl3 diffusion processes for laser doping applications. [Link](https://www.ise.fraunhofer.de/content/dam/ise/de/documents/publications/conference-paper/33-eupvsec-2017/Werner_2AV214.pdf)
7. Christensen, J. S. Phosphorus and boron diffusion in silicon under equilibrium conditions. [Link](https://doi.org/10.1063/1.1566464)
8. Cerofolini, G. F. et al. Phosphorus diffusion into silicon from CVD phosphosilicate glass. [Link](https://www.sciencedirect.com/science/article/pii/0040609082902905)
9. Velichko, O. A comprehensive model of high-concentration phosphorus diffusion in silicon. [Link](https://arxiv.org/abs/1905.10667)
10. MIT diffusion lecture notes. [Link](https://ocw.mit.edu/courses/6-152j-micro-nano-processing-technology-fall-2005/fa6170fba10bd1341251791563a18fc2_lecture6.pdf)
11. Fraunhofer inactive phosphorus / active fraction reference. [Link](https://publica-rest.fraunhofer.de/server/api/core/bitstreams/c0f04abd-0e41-401a-9542-af4e836e5717/content)
