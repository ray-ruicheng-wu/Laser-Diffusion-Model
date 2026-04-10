# 公式与引用文献总表

## 使用规则

这份表是当前项目的统一公式台账。以后遵守下面三条：

1. 任何真正进入代码或分析结论的数学模型，都要先在这里登记。
2. 每条公式都必须写明状态：
   - `adopted`：已经进入模型或已作为当前分析口径
   - `candidate`：文书老哥找到、但还没正式采用
   - `rejected`：查过但当前不采用
3. 每完成一个阶段，都要回到这里更新：
   - 新增采用的公式
   - 新增参考文献
   - 修改状态

## 公式台账

| ID | Stage | Status | 模型/公式 | 当前写法 | 用途 | 主要来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `F-001` | Phase 1 | `adopted` | 1D 热传导方程 | `rho * cp_eff * dT/dt = d/dz(k dT/dz) + Q_laser` | 计算瞬态温度场 | [Crank 1975](https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf), [MDPI 2021](https://www.mdpi.com/1996-1944/14/9/2322) |
| `F-002` | Phase 1 | `adopted` | Beer-Lambert 体热源 | `Q_laser(z,t) ~ A * I(t) * exp(-z / delta)` | 激光能量随深度沉积 | [Green 2008](https://subversion.xray.aps.anl.gov/AGIPD_TCAD/PyTCADTools/Attenuation/Silicon_absorption_coeff_visible_photon.pdf), [MDPI 2021](https://www.mdpi.com/1996-1944/14/9/2322) |
| `F-003` | Phase 1 | `adopted` | 焓法/表观热容相变 | `cp_eff = cp + latent_heat_term` | 不显式追踪固液界面，处理熔化/凝固 | [MDPI 2021](https://www.mdpi.com/1996-1944/14/9/2322) |
| `F-004` | Phase 1 | `adopted` | 液相分数平滑 | `f_l(T)` 在熔点附近用窄 mushy zone 平滑 | 把相变映射为可求解的连续场 | [MDPI 2021](https://www.mdpi.com/1996-1944/14/9/2322) |
| `F-005` | Phase 2 | `adopted` | 1D Fick 扩散 | `∂C/∂t = ∂/∂z [ D(T, f_l) ∂C/∂z ]` | 计算 P 在 Si 中的时空分布 | [Crank 1975](https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf), [MDPI 2021](https://www.mdpi.com/1996-1944/14/9/2322) |
| `F-006` | Phase 2 | `adopted` | 固/液相混合扩散率 | `D_eff = D_solid * (1 - f_l) + D_liquid(T) * f_l` | 体现熔化后扩散系数激增 | [MDPI 2021](https://www.mdpi.com/1996-1944/14/9/2322), [OSTI 2015](https://www.osti.gov/biblio/22402853) |
| `F-007` | Phase 2 | `adopted` | 液相 P 扩散 Arrhenius 式 | `D_l = D0 * exp(-Ea / (k_B T))` | 液相 P 扩散系数 | [OSTI 2015](https://www.osti.gov/biblio/22402853) |
| `F-008` | Phase 2 | `adopted` | PSG 有限库存 source | `Gamma_src(0) = C_src * h_src` | 以面库存近似 PSG 供源 | [Fraunhofer 1991](https://publica.fraunhofer.de/entities/publication/bf765ea3-bd57-4a9a-b8ff-c27be293d951), [MDPI 2021](https://www.mdpi.com/1996-1944/14/9/2322) |
| `F-009` | Phase 2 | `adopted` | Robin 界面传质边界 | `-D ∂C/∂z = h_m (C_eq,src - C_surf)` | 替代非物理硬 Dirichlet 表面浓度 | [Crank 1975](https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf) |
| `F-010` | Phase 2 | `adopted` | 总量守恒库存更新 | `Gamma_src(t) = Gamma_src(0) - Integral C(z,t) dz` | 保证 source + Si 总量守恒 | 当前项目守恒实现，基于零底部通量假设 |
| `F-011` | Phase 2 | `candidate` | 移动界面溶质守恒 | `J_l - J_s = v_i (C_l* - C_s*)` | 处理再凝固界面溶质平衡 | [OSTI 2015](https://www.osti.gov/biblio/22402853), [MDPI 2021](https://www.mdpi.com/1996-1944/14/9/2322) |
| `F-012` | Phase 2+ | `candidate` | 分配系数/俘获模型 | `C_s* = k C_l*` 或 `k_eff(v)` | 再凝固分凝与 solute trapping | [Aziz 1988](https://doi.org/10.1016/0001-6160(88)90333-1) |
| `F-013` | Phase 3 | `candidate` | 液相对流-扩散 | `∂C/∂t + u ∂C/∂z = ∂/∂z(D ∂C/∂z)` | 若考虑熔池流动的溶质输运 | [OSTI 2015](https://www.osti.gov/biblio/22402853), [MDPI 2021](https://www.mdpi.com/1996-1944/14/9/2322) |
| `F-014` | Phase 3 | `adopted` | PSG/Si 双层热学 | `rho_j c_{p,j}(T) dT_j/dt = d/dz [ k_j(T) dT_j/dz ] + Q_j(z,t)` | 处理 PSG 覆层对光吸收和热扩散的影响 | [Crank 1975](https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf), [MDPI 2021](https://www.mdpi.com/1996-1944/14/9/2322) |
| `F-015` | Phase 4 | `rejected` | 多脉冲热积累 | `T_{n+1}` 由前脉冲残余热场延续 | 当前项目范围暂不采用 | 当前用户范围约束：不做多次脉冲热积累 |
| `F-016` | Phase 3 | `adopted` | 双层光学热源最小近似 | `Q_psg ~ (1-R) I exp(-z/delta_psg)`, `Q_si ~ (1-R) I exp(-h_psg/delta_psg) T_int exp(-(z-h_psg)/delta_si)` | 把表面反射、PSG 衰减和 Si 衰减串起来 | [Green 2008](https://subversion.xray.aps.anl.gov/AGIPD_TCAD/PyTCADTools/Attenuation/Silicon_absorption_coeff_visible_photon.pdf), [MDPI 2021](https://www.mdpi.com/1996-1944/14/9/2322) |
| `F-017` | Phase 3 | `adopted` | 功率到单脉冲能量与 fluence 换算 | `E_pulse = P_avg / f`, `F = E_pulse / A_spot` | 把 `30 W @ 500 kHz` 转成模型输入单脉冲口径 | 能量守恒与几何定义 |
| `F-018` | Phase 3 | `adopted` | PSG 有效材料闭合 | `PSG ~= P2O5-SiO2 glass ~= P-rich SiO2 layer` | 在当前最小模型里把 PSG 视为高磷 SiO2 层，并把可能存在的超薄 SiO2 夹层先并入有效玻璃层 | [PNNL 2012](https://www.pnnl.gov/publications/model-phosphosilicate-glass-deposition-pocl3-control-phosphorus-dose-si), [Fraunhofer 2017](https://www.ise.fraunhofer.de/content/dam/ise/de/documents/publications/conference-paper/33-eupvsec-2017/Werner_2AV214.pdf) |
| `F-019` | Phase 2/3 | `adopted` | 固相 P 在 Si 中的 Arrhenius 扩散 | `D_s = D0_s exp(-E_a,s / (k_B T))` | 让非融化条件下仍存在固态 P 扩散，而不再被强制压成零 | [Christensen 2003 DOI](https://doi.org/10.1063/1.1566464), [Cerofolini 1982](https://www.sciencedirect.com/science/article/pii/0040609082902905) |
| `F-020` | Phase 2/3 | `adopted` | 固/液统一 Robin 注入边界 | `-D ∂C/∂z = h_m (C_eq,src - C_surf)` 在固态和液态都可用，液态因 `D` 增大而自然更强 | 允许非融化条件下仍有从 PSG 向 Si 的有限通量注入 | [Crank 1975](https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf), [Velichko 2019](https://arxiv.org/abs/1905.10667) |
| `F-021` | Phase 2/3 | `adopted` | 预扩散 emitter 初始轮廓 | `C_init(z) = C_s erfc(z / (2L))`, with `C_init(x_j)=C_bg` | 用一个可调的 `erfc` 型初始 P 轮廓近似 `POCl3` 基础发射极 | [MIT diffusion notes](https://ocw.mit.edu/courses/6-152j-micro-nano-processing-technology-fall-2005/fa6170fba10bd1341251791563a18fc2_lecture6.pdf), [Fraunhofer 2018 APCVD PSG selective emitter](https://publica.fraunhofer.de/entities/publication/c86c1559-3002-44d0-b9a8-e316b9d77be2) |
| `F-026` | Phase 2/3 | `adopted` | Si 内累计 P 剂量 / 净施主剂量 | `Q_P(z) = Integral_0^z C_P(x) dx`, `Q_net(z) = Integral_0^z max(C_P(x) - C_Ga, 0) dx` | 把 Si 内 P 轮廓直接转换成可用于片电阻分析的累计剂量曲线与表格 | [Crank 1975](https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf), [MIT diffusion notes](https://ocw.mit.edu/courses/6-152j-micro-nano-processing-technology-fall-2005/fa6170fba10bd1341251791563a18fc2_lecture6.pdf) |
| `F-027` | Phase 2/3 | `adopted` | 初始未激活表面 P 层 | `C_inactive(z, 0) = C_inactive,0` for `0 <= z <= h_inactive`, else `0` | 表示前序工序残留在 Si 表层的化学 P 库存，并在初始片电阻分析中与 active emitter 分开记账 | [Velichko 2019](https://arxiv.org/abs/1905.10667), [Fraunhofer SoLMat inactive P reference](https://publica-rest.fraunhofer.de/server/api/core/bitstreams/c0f04abd-0e41-401a-9542-af4e836e5717/content) |

## 文献台账

| Ref ID | 文献 | 主题 | 当前用途 |
| --- | --- | --- | --- |
| `R-001` | [Crank, *The Mathematics of Diffusion*](https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf) | Fick 扩散、边界条件、移动边界数学框架 | Phase 1/2 的基础 PDE 和边界条件参考 |
| `R-002` | [Green 2008 optical parameters of intrinsic silicon](https://subversion.xray.aps.anl.gov/AGIPD_TCAD/PyTCADTools/Attenuation/Silicon_absorption_coeff_visible_photon.pdf) | Si 光学参数 | `532 nm` 吸收深度/吸收率复核 |
| `R-003` | [CERN Silicon General Properties](https://ssd-rd.web.cern.ch/Data/Si-General.html) | Si 常用热物性 | 热模型参数与量级检查 |
| `R-004` | [MDPI 2021: Unified Model for Laser Doping of Silicon from Doping Precursor Layers](https://www.mdpi.com/1996-1944/14/9/2322) | 激光掺杂统一模型 | 项目总体建模框架参考 |
| `R-005` | [OSTI / J. Appl. Phys. 2015: Phosphorus out-diffusion in laser molten silicon](https://www.osti.gov/biblio/22402853) | 液相 P 扩散与再凝固相关模型 | Phase 2 扩散系数和后续 moving interface 候选 |
| `R-006` | [Fraunhofer 1991: Shallow p-n junctions produced by laser doping with PSG](https://publica.fraunhofer.de/entities/publication/bf765ea3-bd57-4a9a-b8ff-c27be293d951) | PSG 激光掺杂 | PSG 供源和浓度量级参考 |
| `R-007` | [Fraunhofer 2011: Visible pulsed laser doping using PSG](https://publica.fraunhofer.de/entities/publication/a5194b29-eaed-452c-af70-a00a67bdb073) | 可见光激光 + PSG 掺杂 | `532 nm + PSG` 工艺背景参考 |
| `R-008` | [Aziz & Kaplan 1988](https://doi.org/10.1016/0001-6160(88)90333-1) | 快速凝固下分配系数 `k(v)` | 后续再凝固/俘获模型候选 |
| `R-009` | [PNNL 2012: A model of phosphosilicate glass deposition by POCl3 to control phosphorus dose in Si](https://www.pnnl.gov/publications/model-phosphosilicate-glass-deposition-pocl3-control-phosphorus-dose-si) | PSG 组成、厚度与 `PSG/SiO2/Si` 界面 | 把 PSG 视为 P-rich SiO2 层、并记住其下常有薄 SiO2 夹层 |
| `R-010` | [Fraunhofer 2017: Suitability of industrial POCl3 tube furnace diffusion processes for laser doping applications](https://www.ise.fraunhofer.de/content/dam/ise/de/documents/publications/conference-paper/33-eupvsec-2017/Werner_2AV214.pdf) | `PSG/SiO2` 堆栈厚度与磷剂量 | 激光掺杂前驱体层的现实堆栈口径参考 |
| `R-011` | [Christensen 2003: Phosphorus and boron diffusion in silicon under equilibrium conditions](https://doi.org/10.1063/1.1566464) | 固相 P/B 在 Si 中的 Arrhenius 扩散 | 固相 `D_s(T)` 口径参考 |
| `R-012` | [Cerofolini et al. 1982: Phosphorus diffusion into silicon from chemically vapour-deposited phosphosilicate glass](https://www.sciencedirect.com/science/article/pii/0040609082902905) | 从 PSG 向 Si 的固态扩散 | 支撑“非融化也存在 P 注入/扩散” |
| `R-013` | [Velichko 2019: A comprehensive model of high-concentration phosphorus diffusion in silicon](https://arxiv.org/abs/1905.10667) | PSG 常量源固态扩散建模 | 支撑 PSG 常量源/固态扩散建模框架 |
| `R-014` | [MIT 6.152J diffusion lecture notes](https://ocw.mit.edu/courses/6-152j-micro-nano-processing-technology-fall-2005/fa6170fba10bd1341251791563a18fc2_lecture6.pdf) | `erfc` 常源扩散解 | 预扩散 emitter 初始轮廓近似 |
| `R-015` | [MDPI 2020: Effects of Laser Doping on the Formation of the Selective Emitter of a c-Si Solar Cell](https://www.mdpi.com/2076-3417/10/13/4554) | 已扩散 emitter 上的激光再掺杂 | 支撑“已有 P 轮廓 + PSG 额外注入”工艺图像 |

## 阶段更新记录

### Phase 1

- 新增 `F-001` 到 `F-004`
- 新增 `R-001` 到 `R-004`

### Phase 2

- 新增 `F-005` 到 `F-010`
- 新增候选模型 `F-011` 到 `F-013`
- 新增 `R-005` 到 `R-008`
- 修正说明：
  - 删除了旧的硬 Dirichlet 表面 source 口径
  - 当前 Phase 2 正式口径改为有限 source + Robin 边界 + 总量守恒

### Phase 3

- `F-014` 从 `candidate` 提升为 `adopted`
- 新增 `F-016` 作为当前双层光学热源的最小实现
- 新增 `F-017` 作为平均功率到单脉冲输入的换算关系
- 新增 `F-018` 作为 PSG 的有效材料闭合：当前按 `P2O5-SiO2` 高磷 SiO2 层处理
- 新增 `F-019` 作为固相 P 在 Si 中的 Arrhenius 扩散
- 新增 `F-020` 作为固/液统一 Robin 注入边界
- 新增 `F-021` 作为 `POCl3` 基础发射极的 `erfc` 初始轮廓近似
- 新增 `F-026` 作为 Si 内累计 P 剂量 / 净施主剂量输出，用于后续片电阻分析
- 新增 `F-027` 作为初始未激活表面 P 层，用于表示前序残留化学 P 库存
- 新增说明：
  - 当前采用的是最小 `PSG/Si` 双层热模型
  - 其中 `PSG` 现在明确解释为 `phosphosilicate glass = P2O5-SiO2 glass`，并在当前实现里按高磷 SiO2 层近似
  - 当前扩散模型不再把“未熔化”强行等价为“零注入”
  - 当前也允许先给定一个基础 emitter，再叠加激光期间的再分布和 PSG 注入
  - 还没有采用完整 `PSG/SiO2/Si` TMM
  - `F-015` 多脉冲热积累已明确不在当前范围内

## 下一次阶段结束时的必做项

1. 检查本阶段新增了哪些公式进入代码或分析。
2. 给每条新公式分配 `F-ID`。
3. 补齐引用文献。
4. 标注状态是 `adopted`、`candidate` 还是 `rejected`。
5. 在“阶段更新记录”里写一段这次更新了什么。

## Boundary Review Addendum

### 新增候选公式

| ID | Stage | Status | 模型/公式 | 当前写法 | 用途 | 主要来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `F-022` | Boundary review | `adopted` | 显式 precursor/source 单元 | 在 Si 表面外再设一个 source control volume，并与第一层 Si 单元交换通量 | 更接近激光前驱体层在熔化阶段的真实供源方式 | [Lill 2017](https://www.mdpi.com/1996-1944/10/2/189), [MDPI 2021](https://www.mdpi.com/1996-1944/14/9/2322) |
| `F-023` | Boundary review | `candidate` | 表面 out-diffusion / evaporation 通量 | `J_out ~ v_out * C_surface` 或其他表面流失闭合 | 处理激光熔融期间的表面失质，不再把所有表面行为都揉进单个 Robin 注入项 | [OSTI 2015](https://www.osti.gov/biblio/22402853), [MDPI 2021](https://www.mdpi.com/1996-1944/14/9/2322) |
| `F-024` | Boundary review | `candidate` | `PSG/SiO2/Si` 有效界面透过边界 | `J_int = h_int(T, t_ox) * (C_src,eq - C_surf)` | 把薄 `SiO2` 阻挡从现有 lumped `L_tr` 中单独拿出来建模 | [PNNL 2012](https://www.pnnl.gov/publications/model-phosphosilicate-glass-deposition-pocl3-control-phosphorus-dose-si), [Fraunhofer 2017](https://www.ise.fraunhofer.de/content/dam/ise/de/documents/publications/conference-paper/33-eupvsec-2017/Werner_2AV214.pdf) |
| `F-025` | Boundary review | `adopted` | 熔融窗口 gated source 注入 | `J_in = H(f_l - f_th) h_m max(0, C_src,cell - C_surf)` | 把“额外 PSG 注入主要发生在熔融窗口内”的主流激光前驱体建模口径写进当前实现 | [Lill 2017](https://www.mdpi.com/1996-1944/10/2/189), [Fell 2008 Fraunhofer](https://publica-rest.fraunhofer.de/server/api/core/bitstreams/a4616ec1-fd19-426e-b904-4f6920a07805/content), [MDPI 2021](https://www.mdpi.com/1996-1944/14/9/2322) |

### 新增参考文献

| Ref ID | 文献 | 主题 | 当前用途 |
| --- | --- | --- | --- |
| `R-016` | [Lill et al. 2017: Influence of precursor layer ablation on laser doping and laser fired contact formation](https://www.mdpi.com/1996-1944/10/2/189) | 显式 precursor/source 单元与分配系数 | 作为 Robin 之外的激光掺杂边界处理参考 |

### 复核结论

1. 当前 `F-020` Robin 边界仍可保留，作为“有效界面传质”的降阶闭合。
2. 若要升级到更接近激光重熔物理的边界，优先级应是：
   - `F-022` 显式 source cell
   - `F-024` 独立氧化层/界面阻挡
   - `F-023` 表面 out-diffusion / evaporation
3. 2026-04-08 起，当前代码主线已把 `F-022` 和 `F-025` 落地为默认设置：
   - `boundary_model = finite_source_cell`
   - `source_exchange_mode = melt_only`

| `F-027` | Phase 3 | `adopted` | 初始未激活表面 P 层 / 残留 P 记账 | `C_init(z) = C_residual(z) + C_active(z)`，片电阻分析中将 residual P 与 active emitter 分开记账 | 用于描述前序工序残留 P，例如 `30 nm / 5e20 cm^-3`，并与 active emitter 的初始片电阻输入分开记录 | 项目当前归档口径 |

## Texture Enhancement Addendum

### 新增公式

| ID | Stage | Status | 模型/公式 | 当前写法 | 用途 | 主要来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `F-028` | Phase 3 texture | `adopted` | texture 光学逃逸反射降阶闭合 | `R_eff = k_tex * R_flat`, with `0 < k_tex <= 1` for enhancement | 把制绒金字塔的多次反射 / 光陷折算成 1D 模型可用的有效反射率 | [Campbell & Green 1987](https://www.osti.gov/biblio/6560834), [Baker-Finch & McIntosh 2011 reflectance](https://researchportalplus.anu.edu.au/en/publications/reflection-of-normally-incident-light-from-silicon-solar-cells-wi/), [McIntosh & Baker-Finch OPAL2](https://www2.pvlighthouse.com.au/calculators/opal%202/McIntosh%20and%20Baker-Finch%20-%20paper%20on%20OPAL2%20for%2038th%20IEEE.pdf) |
| `F-029` | Phase 3 texture | `adopted` | texture 真实 / 投影界面面积因子 | `A_factor = A_real / A_proj`, ideal square pyramids: `A_factor = sec(theta)` | 把制绒表面的额外界面面积折算回 1D 投影面积口径 | [Baker-Finch & McIntosh 2011 area](https://researchportalplus.anu.edu.au/en/publications/the-contribution-of-planes-vertices-and-edges-to-recombination-at/), [Baker-Finch & McIntosh 2011 reflectance](https://researchportalplus.anu.edu.au/en/publications/reflection-of-normally-incident-light-from-silicon-solar-cells-wi/) |
| `F-030` | Phase 3 texture | `adopted` | conformal PSG 覆盖下的 projected-area source 库存放大 | `Gamma_src,proj = A_factor * C_src * h_src` | 在投影面积口径下，表示制绒导致的实际 PSG 供源体积增加 | [Baker-Finch & McIntosh 2011 area](https://researchportalplus.anu.edu.au/en/publications/the-contribution-of-planes-vertices-and-edges-to-recombination-at/) |
| `F-031` | Phase 3 texture | `adopted` | projected-area 界面注入通量放大 | `J_in,proj = A_factor * h_m * max(0, C_src - C_surf)` | 在 melt-gated 前驱体注入口径里，把界面面积增加折算成投影面积下的通量增强 | [Lill 2017](https://www.mdpi.com/1996-1944/10/2/189), [Baker-Finch & McIntosh 2011 area](https://researchportalplus.anu.edu.au/en/publications/the-contribution-of-planes-vertices-and-edges-to-recombination-at/) |

### 新增引用文献

| Ref ID | 文献 | 主题 | 当前用途 |
| --- | --- | --- | --- |
| `R-017` | [Campbell & Green 1987: Light trapping properties of pyramidally textured surfaces](https://www.osti.gov/biblio/6560834) | 金字塔纹理的光陷与反射降低 | texture 光学逃逸反射闭合 |
| `R-018` | [Baker-Finch & McIntosh 2011: Reflection of normally incident light from silicon solar cells with pyramidal texture](https://researchportalplus.anu.edu.au/en/publications/reflection-of-normally-incident-light-from-silicon-solar-cells-wi/) | 制绒表面的正入射反射路径与 `R_eff` | texture 光学降阶标定 |
| `R-019` | [Baker-Finch & McIntosh 2011: The contribution of planes, vertices, and edges to recombination at pyramidally textured surfaces](https://researchportalplus.anu.edu.au/en/publications/the-contribution-of-planes-vertices-and-edges-to-recombination-at/) | 制绒表面的 `sqrt(3)` 面积增加口径 | texture 界面面积因子 |
| `R-020` | [McIntosh & Baker-Finch OPAL2 paper](https://www2.pvlighthouse.com.au/calculators/opal%202/McIntosh%20and%20Baker-Finch%20-%20paper%20on%20OPAL2%20for%2038th%20IEEE.pdf) | 制绒表面的射线追踪 / 反射分布 | texture `R_eff` 标定和后续参数化 |

### 更新记录

1. 2026-04-08 起，texture enhancement 已作为 Phase 3 的第一版降阶模型进入主线。
2. 当前并入的只有两类 texture 效应：
   - 光学上用 `R_eff = k_tex R_flat`
   - 界面上用 `A_factor = A_real / A_proj`
3. 当前还没有把“局部光斑重分布 / 局部熔化阈值分布 / 棱边优先熔化”显式并入求解器，这部分仍属后续工作。

## Sheet Resistance Addendum

### 新增公式

| ID | Stage | Status | 模型/公式 | 当前写法 | 用途 | 主要来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `F-032` | Phase 3 post-processing | `adopted` | 片电阻的一维面电导积分 | `Rsh = 1 / \int sigma(z) dz` | 把深度方向的导电率剖面积分成 `ohm/sq` 口径，用于比较激光前后发射极导电能力 | 基础半导体输运关系；当前项目中作为片电阻后处理主公式 |
| `F-033` | Phase 3 post-processing | `adopted` | 单晶硅电子迁移率 `Masetti` 模型 | `sigma(z) = q * mu_n(N_ion) * n(z)`，其中 `mu_n` 由 `Masetti 1983 @ 300 K` 给出 | 把 `active donor profile` 转为深度相关导电率，用于 `Rsh` 计算 | [Masetti 1983](https://doi.org/10.1109/T-ED.1983.21207) |
| `F-034` | Phase 3 post-processing | `adopted` | 薄 inactive 表面 P 层的电学折减 | `N_D,act = N_D,active_component + f_inactive * N_D,inactive_component + f_inj * N_D,injected_component` | 在片电阻分析里，把化学上存在但未完全电活化的薄表面 P 库存和激光后注入分开记账 | 当前项目电学后处理假设；不同场景可切换 `f_inactive` / `f_inj`，measured 对照当前重点比较 `f_inactive = 0` 与 `1` 的 laser 后记账边界 |
| `F-035` | Phase 3 post-processing | `adopted` | 分段经验 non-active pool 活化模型 | `N_D,act,final = N_D,active_component + f_pool(P_laser) * (N_D,inactive_component + N_D,injected_component)` | 用实验 `power -> Rsh` 锚点，把 laser 后“非活化池”统一折算成有效施主，用于 measured-profile 驱动的经验电学校准 | 当前项目 empirical electrical calibration layer；支撑点来自 `24–60 W` 实验片阻数据与 measured initial profile 的联合标定 |
| `F-036` | Phase 3 post-processing | `adopted` | 双通道活化闭合 | `N_D,act,final = N_D,active_component + eta_inactive(P) * N_D,inactive_component + eta_inj(P) * N_D,injected_component` | 把“初始 inactive 再激活”和“PSG 注入 P 活化”分开记账，并用 measured `Rsh` 做分段校准 | 当前项目 dual-channel electrical calibration layer；见 `run_dual_channel_activation_calibration.py` 与 measured `24–60 W` 片阻数据 |

### 新增参考文献

| Ref ID | 文献 | 主题 | 当前用途 |
| --- | --- | --- | --- |
| `R-021` | [Masetti et al. 1983: Modeling of carrier mobility against carrier concentration in arsenic-, phosphorus-, and boron-doped silicon](https://doi.org/10.1109/T-ED.1983.21207) | 单晶硅重掺杂迁移率模型 | 作为 `Rsh` 后处理中的电子迁移率闭合 |

### 更新记录

1. 2026-04-09 起，项目新增 `sheet resistance` 后处理模块。
2. 当前 `Rsh` 主线口径是：
   - `Masetti @ 300 K`
   - 初始 active emitter 视为 fully active
   - 薄 inactive 表面 P 层按设定活化率折减
   - 激光后若有 source 注入，当前先按 fully active 计入 `Rsh_af`
3. 当前 `Rsh` 结果应读成“电学估计值”，不是最终四探针实测替代；后续仍可再加入更细的 activation / mobility 标定。
4. 2026-04-09 的 measured-profile / `Rsh` 对照补充把 `measured inactive` 口径更新为 `max(SIMS - ECV, 0)`，并要求 `final total` 始终包含 `PSG` 注入项。
5. measured-driven `Rsh` 当前默认保留两套后处理边界：
   - `Case A`：laser 后 initial inactive 仍不计 active
   - `Case B`：laser 后 initial inactive 全计 active
6. 因此 `F-034` 当前应读成“可切换的 activation bookkeeping closure”，而不是唯一固定的单参数假设。
7. 2026-04-09 的 `PSG = surface SIMS` 低功率校准补充采用：
   - `source_dopant_concentration_cm3 = 4.5913166904198945e21 cm^-3`
   - `initial inactive baseline activation = 0.04448923256987511`，对应 `Rsh_init = 180 ohm/sq`
   - `low-power post-laser inactive activation = 0.38734199240748757`，对应 `30W -> 110 ohm/sq`
   - `27–36W` 当前按 `injected_activation_fraction = 0.0` 读取
8. 因为这段扫描在当前 summary 下仍是 `no melt / no injection`，所以这组低功率 `Rsh` 结果应首先读成 calibration bookkeeping，而不是新的注入物理证据。
9. 2026-04-09 后续又新增一轮“基于实验趋势”的低功率经验校准：
   - 统一 `initial inactive activation = 0.06447924522684517`，对应平均 `Rsh_init = 169.893775 ohm/sq`
   - 逐点 `final inactive activation` 分别为：
     - `24W = 0.08211699366064995`
     - `27W = 0.1271423637719521`
     - `30W = 0.15120848835373957`
     - `33W = 0.3210707049033614`
10. 这组逐点 activation 参数的定位仍是 empirical electrical calibration layer；因为 `24–36W` 在当前 `PSG = surface SIMS + melt_only` 热/扩散结果下仍然是 `no melt / no injection`，所以不能把它们写成热扩散层的新 adopted physics。
11. 2026-04-09 的 `6W` 间隔经验外推补充只应读成 calibration extrapolation：
    - `24W -> 164.17`
    - `30W -> 138.10`
    - `36W -> 105.17`
12. `42W` 起 raw `final inactive activation` 已大于 `1`，因此原始经验律继续外推已失去物理可接受性；当前仅可把对应 `clamped` 结果当作辅助边界参考。
13. `54W` 起热模型已进入 `partial melt / injection` 过渡区，所以不能再把纯低功率经验激活律当作主口径向上裸外推。
14. 2026-04-09 新增 `F-035`：把 measured-profile 驱动的 `Rsh` 后处理升级为“分段经验 non-active pool activation model”。
15. 这套新口径使用：
    - `initial inactive activation = 0.06447924522684517`
    - `final non-active pool activation` 由 `inputs/activation_models/segmented_nonactive_pool_empirical_24_60w.csv` 提供
16. 该模型把 `final inactive component + final injected component` 合并成一个 `non-active pool`，用实验片阻点做经验标定；应读成 post-processing electrical closure，而不是新的扩散主方程。
17. 2026-04-09 新增 `F-036`：把 laser 后有效施主拆成三部分：
    - 原本已 active 的重分布分量
    - 初始 inactive 的再激活分量
    - `PSG` 注入分量
18. 双通道标定当前采用 measured `24–60 W` 片阻数据，并设定：
    - `initial inactive activation = 0.06447924522684517`
    - 低注入段 `24–48 W` 先拟合 `eta_inactive(P)`
    - 高注入段 `54–60 W` 再反求 `eta_inj(P)`
19. 当前最关键的新结论不是“高功率区已经完全分离成功”，而是：
    - 低功率区 `eta_inactive(P)` 可以稳定标定
    - 但把这条低功率 `eta_inactive(P)` 直接外推到 `54/60 W` 会把 `Rsh` 预测得过低
    - 因而高功率区存在新的 regime change，不能继续沿用同一条 inactive 再激活律
