# Phase 2 原理分析、公式复核与参数表

## 1. 这次复核改了什么

这次不是简单调参，而是把 Phase 2 里几条基础公式重新对齐了一遍。当前版本相对旧版，最重要的修正有四个：

1. 表面边界从“硬 Dirichlet 表面浓度”改成了“有限库存 + 通量/传质边界”。
2. PSG 库存不再按单步浓度增量截断扣减，而是按总量守恒直接反算。
3. 扩散系数在网格界面上的离散从算术平均改成了谐和平均，避免液/固扩散率跨很多数量级时出现假通量。
4. 结深从“最后一个高于背景的网格点”改成了“与背景浓度交点的线性插值”。

这四项里，前两项是直接 bug / 建模错误，第三项是高反差扩散问题里的基础离散修正，第四项是结果读取方式修正。

## 2. 当前采用的基础物理模型

### 2.1 控制方程

当前 Phase 2 仍然采用 1D 深度方向模型，并把液相流动忽略掉，也就是先取 `u = 0` 的极限。控制方程写成：

`∂C/∂t = ∂/∂z [ D(T, f_l) ∂C/∂z ]`

其中：

- `C` 是 Si 中的 P 浓度
- `D(T, f_l)` 是由温度和液相分数控制的有效扩散系数
- `f_l = 0` 时几乎是固相扩散
- `f_l = 1` 时接近液相扩散

这对应的是“先不做液相对流，只保留 Fick 扩散”的最小模型。

### 2.2 液相扩散系数

当前液相 P 扩散系数采用：

`D_l = D0 * exp(-Ea / (k_B T))`

默认参数是：

- `D0 = 1.4e-3 cm^2/s`
- `Ea = 0.183 eV`

在 Si 熔点附近，这会给出约 `4e-4 cm^2/s` 量级的液相扩散率。

### 2.3 表面边界条件

旧版做法是表面一旦熔化，就直接钉死 `C(0,t) = C_source`。这会带来两个问题：

1. `PSG -> molten Si` 的传质被假设成无限快。
2. 表面一旦需要回抽 P，会和库存更新发生冲突。

当前改成了 Robin 型边界：

`-D ∂C/∂z |_(z=0) = h_m (C_eq,src - C_surf)`

其中：

- `C_eq,src` 由当前剩余 PSG 库存和有效源层厚度换算而来
- `h_m = D_surface / L_tr`
- `L_tr` 是界面传质长度，当前作为可调参数 `interfacial_transport_length_m`

当前口径改为：只要 PSG 还有库存，这个 Robin 边界就存在；若表面未熔化，则它由固相扩散率控制，因此注入很弱但不再被人为设成零。

### 2.4 固相扩散

为了把“非融化条件下也存在扩散”这层物理并进去，当前固相 P in Si 扩散改成了 Arrhenius 形式：

`D_s = D0_s * exp(-Ea_s / (k_B T))`

默认口径是：

- `D0_s = 8.0e-4 cm^2/s`
- `Ea_s = 2.74 eV`

这一步的作用不是夸大亚熔化掺杂，而是避免把“未熔化”错误地强行等价成“零注入 + 零扩散”。

### 2.5 PSG 库存方程

PSG 当前仍然没有显式建成玻璃层网格，而是作为有限面库存：

`Gamma_src(t) = Gamma_src(0) - Integral C(z,t) dz`

这里的意思很直接：

- 初始时所有 P 都在 source 里
- 计算域底部没有通量流出
- 所以 “source 剩余量 + Si 中总量” 必须守恒

这比旧版那种按单步正增量扣库存的方法稳得多，也不会再出现“Si 里 P 变少了，但 source 不回补”的假失质量。

### 2.6 结深定义

当前掺杂深度定义为最终 `P(z)` 和基底 `Ga` 背景浓度的交点：

`C_P(z_j) = C_Ga,background`

实现上已经改成线性插值，所以不会再被单个网格步长直接锁死。

## 3. 这次复核确认的主要问题

### 3.1 旧版实现里确实存在的错误

1. 旧版库存更新使用了 `max(0, delta_inventory)`，会在某些时间步破坏质量守恒。
2. 旧版表面边界把 source 近似成了无限快平衡，物理上过强。
3. 旧版在液/固交界使用扩散系数算术平均，会高估跨界面通量。
4. 旧版结深直接取最后一个网格点，存在明显量化误差。

### 3.2 这次没有硬加进去、但必须记住的物理项

即使改完上面四项，当前模型仍不是研究最终版。它还没有显式包含：

1. 液相对流项 `u ∂C/∂z`
2. 固液移动界面的溶质守恒
3. 显式的 `partition coefficient k` 或 `k(v_i)` 再凝固模型

所以现在的 Phase 2 更准确的说法是：

- “无对流”
- “固定网格”
- “用温度历史控制扩散率”
- “默认接近完全俘获 / 不显式分凝”

如果后面要进一步逼近激光重熔再凝固，就该加上界面速度项和 `k(v_i)`。

## 4. 当前结果

### 4.1 修正后默认案例

输出目录：

- `outputs/phase2/default_run/`

当前默认结果：

- 最终峰值 `P` 浓度：`5.447e20 cm^-3`
- 最终结深：`143.9 nm`
- 最大结深：`143.9 nm`
- 最终质量守恒误差：`-1.434e4 atoms/m^2`

这个质量守恒误差相对初始 source 面库存 `2.0e20 atoms/m^2` 来说，已经是浮点舍入量级。

### 4.2 532 nm 裸硅对照

按 `532 nm` 裸硅基线参数：

- `absorptivity = 0.626`
- `absorption_depth = 1274 nm`

修正后的 Phase 2 对照结果现在变成：

- 最终峰值 `P` 浓度：`非零但极低`
- 结深：`0`

这和“未熔化时仍可能存在极弱的固态扩散，但不足以形成结深”的物理图像一致。

## 5. 可靠性分析

### 5.1 已经明显更可靠的地方

1. 质量守恒现在是成立的。
2. 表面 source 现在更接近“有限 source + 界面通量”而不是“无限快强制平衡”。
3. 液/固高对比扩散率下的界面通量离散更稳健。
4. 不熔化时模型不再被强行钉成零掺杂，而是会退化到极弱的固态注入。

### 5.2 仍然要谨慎的地方

当前结深对 `nz` 和 `dt` 仍然敏感，但这里已经能看出，问题不全在扩散模块本身，而是 Phase 1 的熔深也在跟着网格和时间步大幅变化。

当前几个敏感性结果：

| Case | Final xj |
| --- | ---: |
| default (`nz=500`, `dt=0.2 ns`) | `143.7 nm` |
| `nz=250` | `191.0 nm` |
| `nz=1000` | `169.3 nm` |
| `dt=0.1 ns` | `171.9 nm` |

对应的热模型最大熔深也在变化：

| Phase 1 case | Max melt depth |
| --- | ---: |
| default (`nz=500`, `dt=0.2 ns`) | `128.3 nm` |
| `nz=250` | `192.8 nm` |
| `nz=1000` | `176.2 nm` |
| `dt=0.1 ns` | `160.3 nm` |

所以现阶段最准确的判断是：

- Phase 2 的基础公式比之前对了很多
- 但整个耦合结果还没有收敛
- 当前的主要不确定性已经转移到 Phase 1 的热-相变收敛性上

## 6. 参数表

| 类别 | 参数 | 默认值 | 单位 | 说明 |
| --- | --- | ---: | --- | --- |
| source | `P in PSG` | `2.0e21` | `cm^-3` | PSG 中 P 浓度上限 |
| substrate | `Ga in Si` | `1.0e16` | `cm^-3` | 背景受主浓度 |
| diffusion | `D_solid_floor` | `0` | `m^2/s` | 固相扩散率下限；默认不再用常数占位 |
| diffusion | `D0_solid` | `8.0e-4` | `cm^2/s` | 固相 P in Si Arrhenius 前因子 |
| diffusion | `Ea_solid` | `2.74` | `eV` | 固相 P in Si Arrhenius 活化能 |
| diffusion | `D0_liquid` | `1.4e-3` | `cm^2/s` | 液相 P 扩散前因子 |
| diffusion | `Ea_liquid` | `0.183` | `eV` | 液相 P 扩散活化能 |
| source | `source_effective_thickness` | `100` | `nm` | PSG 有限库存等效厚度 |
| interface | `interfacial_transport_length` | `100` | `nm` | Robin 边界里的界面传质长度 |
| interface | `interface_liquid_threshold` | `0.5` | `-` | 当前保留作液相诊断阈值，不再决定 source 是否开启 |

## 7. 当前结论

### 已经能说的

1. 旧版 Phase 2 里确实有基础实现错误，特别是库存更新和表面边界。
2. 当前版本已经把 Phase 2 修到“基础扩散公式自洽、质量守恒成立、边界条件更合理”的状态。
3. 当前默认结果比旧版更保守，峰值 P 浓度明显下降。
4. 目前结果是否继续变化，更多取决于热模型是否收敛，而不是扩散模块还在明显造假。

### 还不能说满的

1. 当前结果还不是包含 `k(v)`、界面分凝和再凝固俘获的最终研究模型。
2. 当前 `interfacial_transport_length` 仍是待标定参数。
3. 如果要和真实工艺做更强对照，下一步优先级已经变成：
   先补热模型收敛 / `PSG/Si` 双层热学，再补移动界面掺杂模型。
4. 即使已经并入固态扩散，在当前纳秒级单脉冲热预算下，非融化注入仍可能非常弱；若实验里存在明显掺杂，还应考虑预扩散 P 初始轮廓或更长热预算。

## 8. 参考链接

- [Crank, The Mathematics of Diffusion](https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf)
- [OSTI: Phosphorus out-diffusion in laser molten silicon](https://www.osti.gov/biblio/22402853)
- [MDPI 2021: Unified Model for Laser Doping of Silicon from Doping Precursor Layers](https://www.mdpi.com/1996-1944/14/9/2322)
- [Fraunhofer 1991: Shallow p-n junctions produced by laser doping with PSG](https://publica.fraunhofer.de/entities/publication/bf765ea3-bd57-4a9a-b8ff-c27be293d951)
- [Fraunhofer 2011: Visible pulsed laser doping using PSG](https://publica.fraunhofer.de/entities/publication/a5194b29-eaed-452c-af70-a00a67bdb073)
- [Christensen 2003: Phosphorus and boron diffusion in silicon under equilibrium conditions](https://doi.org/10.1063/1.1566464)
- [Cerofolini et al. 1982: Phosphorus diffusion into silicon from chemically vapour-deposited phosphosilicate glass](https://www.sciencedirect.com/science/article/pii/0040609082902905)
- [Velichko 2019: A comprehensive model of high-concentration phosphorus diffusion in silicon](https://arxiv.org/abs/1905.10667)
