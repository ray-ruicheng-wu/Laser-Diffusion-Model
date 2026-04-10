# Phase 3 原理分析、可靠性分析与参数表

## 1. 本阶段目标

Phase 3 的目标不是马上把最终掺杂结果做对，而是先把热模型从“单层 Si 演示模型”升级成“最小可实现的 `PSG/Si` 双层热模型”，然后再用这条新的热历史重驱动现有扩散模块。

本轮之后，`PSG` 的项目口径进一步统一为：

- `PSG = phosphosilicate glass`
- 组成上可近似理解为 `P2O5-SiO2 glass`
- 在当前最小模型里，把它视为“一层高磷 `SiO2`”
- 若现实工艺里存在超薄 `SiO2` 夹层，当前先并入这层有效玻璃层，不单独离散

这一步主要回答两个问题：

1. 在 `PSG/Si` 双层和 `532 nm` 基线吸收深度下，单脉冲是否足以让 Si 熔化？
2. 如果热模型本身不熔化，当前扩散结果是不是应该只剩极弱的固态注入，而不是被强行压成零？

## 2. 当前采用的模型

### 2.0 当前对 PSG 的材料解释

公开资料表明，`POCl3` 预沉积后表面形成的前驱层更接近“磷进入 `SiO2` 网络后的玻璃层”，并且现实工艺表征里常能看到 `PSG/SiO2/Si` 堆栈，而不是简单的 `PSG` 直接贴 `Si`。

因此当前 Phase 3 采用的材料闭合是：

- 热学上：把 `PSG` 看成具有 `SiO2` 量级热物性的高磷玻璃层
- 光学上：把 `PSG` 看成 `532 nm` 下弱吸收、主要影响界面反射/透射和前驱层厚度的覆盖层
- 掺杂上：把它看成 `P` 的有限供源

这一步是“更贴近文献的最小闭合”，还不是完整 `PSG/SiO2/Si` 三层显式模型。

### 2.1 双层热传导

对 `PSG` 和 `Si` 两层统一求解：

`rho_j * cp_j(T) * dT_j/dt = d/dz [ k_j(T) * dT_j/dz ] + Q_j(z,t)`

其中：

- `j = PSG` 时采用常数热物性
- `j = Si` 时采用带相变的表观热容写法

### 2.2 双层光学热源的最小近似

这一步没有上完整 TMM，而是采用“表面反射 + PSG Beer-Lambert 衰减 + 界面透射 + Si Beer-Lambert 衰减”的最小模型：

- 进入堆栈的入射功率：`(1 - R_surface) * I(t)`
- PSG 内热源：`Q_psg ~ exp(-z / delta_psg)`
- 到达 Si 的界面通量：`I_si,0 = (1 - R_surface) * I(t) * exp(-h_psg / delta_psg) * T_interface`
- Si 内热源：`Q_si ~ exp(-(z - h_psg) / delta_si)`

这不是最终研究级光学模型，但足够做第一版双层热基线。

### 2.3 Si 熔化与后续扩散

Si 的液相分数仍然沿用焓法 / 表观热容法。随后把双层热结果裁成“只含 Si 子域”的热历史，再交给现有 Phase 2 扩散模块。

## 3. 当前默认参数口径

| 类别 | 参数 | 默认值 | 单位 | 说明 |
| --- | --- | ---: | --- | --- |
| optics | `surface_reflectance` | `0.09` | `-` | air/PSG 顶面当前默认反射近似 |
| optics | `interface_transmission` | `0.68` | `-` | PSG/Si 界面最小透射近似 |
| optics | `psg_absorption_depth` | `50` | `um` | PSG 弱吸收占位值 |
| optics | `si_absorption_depth` | `1274` | `nm` | `532 nm` 裸 Si 基线吸收深度 |
| stack | `psg_thickness` | `150` | `nm` | PSG 有效厚度占位值 |
| thermal | `psg_k` | `1.4` | `W/m/K` | 高磷 `SiO2` 层导热率占位值 |
| thermal | `psg_cp` | `730` | `J/kg/K` | 高磷 `SiO2` 层比热占位值 |
| thermal | `psg_rho` | `2200` | `kg/m^3` | 高磷 `SiO2` 层密度占位值 |
| laser | `average_power` | `30` | `W` | 当前平均功率输入 |
| laser | `repetition_rate` | `500` | `kHz` | 当前频率输入 |
| laser | `pulse_energy` | `60` | `uJ` | 由 `30 W / 500 kHz` 得到 |
| laser | `spot_shape` | `square_flat_top` | `-` | 当前横向光斑口径 |
| laser | `square_side` | `95` | `um` | flat-top 正方形边长 |
| pulse | `fluence` | `0.665` | `J/cm^2` | 由 `60 uJ / (95 um)^2` 换算得到 |
| pulse | `pulse_fwhm` | `10` | `ns` | 当前默认时间脉宽 |
| pulse | `peak_time` | `30` | `ns` | 当前默认脉冲峰时刻 |

## 4. 当前结果

输出目录：

- `outputs/phase3/default_run/thermal`
- `outputs/phase3/default_run/diffusion`
- `outputs/phase3/default_run/summary.json`

当前默认结果：

- 峰值 stack 表面温度：`1132.5 K`
- 峰值 Si 表面温度：`1360.8 K`
- 最大 Si 熔深：`0 nm`
- 最终峰值 `P` 浓度：`1.11e11 cm^-3`
- 最终结深：`0 nm`

光学预算估算：

- 顶面反射：`9%`
- PSG 吸收：约 `0.27%`
- 进入并在 Si 计算域内吸收：约 `61.58%`
- 未在当前域内吸收：约 `29.15%`

## 5. 可靠性分析

### 5.1 成立的结论

1. 双层热模型和现有扩散模块已经能串起来运行。
2. 在当前最小 `PSG/Si` 基线下，单脉冲不会让 Si 熔化。
3. 在把固态扩散并进去之后，非融化条件下不再是“严格零掺杂”，而是“存在极弱固态注入，但不足以形成结深”。

### 5.2 这一步最重要的物理含义

这一步把问题进一步缩小了：

- 不是“扩散模块又乱注入了 P”
- 而是“当前双层热基线本身就没有给出熔化，而固态扩散在纳秒尺度上又非常弱”

这意味着，如果要逼近文献中的 `0.5–0.7 um` 掺杂轮廓，下一步更应该补：

1. 更真实的 `PSG/SiO2/Si` 光学堆栈
2. 在已测 `95 um square flat-top` 下，不同平均功率工作点对应的局部单脉冲 `fluence`
3. moving interface 与 `k(v)`

### 5.3 当前还不够可靠的地方

1. `PSG` 光学参数目前仍是占位近似，不是完整文献标定值。
2. 当前虽然已把 `PSG` 明确解释成高磷 `SiO2` 层，但还没有显式把超薄 `SiO2` 夹层独立成层。
3. 当前光学模型不是 TMM，而是最小分层 Beer-Lambert 近似。
4. 当前仍然是单脉冲固定点，`500 kHz` 只用于功率到单脉冲能量的换算，不参与热积累。
5. 当前虽然已经允许固态注入，但还没有把预扩散发射极或初始 P 轮廓并进来。

## 6. 与论文结果的关系

和当前文献对照笔记一致，这一步说明：

1. 只把模型从“单层 Si”改成“最小 PSG/Si 双层”，还不足以解释文献里的深掺杂结果。
2. 文献里常见的较深轮廓，极可能依赖更完整的堆栈光学、不同的局部 fluence 分布、预扩散初始 P 轮廓，以及后续再凝固物理。

## 7. 当前结论

### 已经能说的

1. Phase 3 已经建立了 `PSG/Si` 双层热模型的第一版。
2. 当前基线下，热模型不给出熔化；但在 `all_states + 无初始 emitter` 的默认口径下，仍会允许非常弱的固态界面注入。
3. 这一步帮助我们确认：下一轮重点应该转向在已测 `500 kHz / 95 um square flat-top` 口径下标定不同平均功率工作点的 `fluence`、更真实的光学堆栈、以及可能存在的预扩散初始 P 轮廓，而不是继续只调单脉冲扩散参数。

### 还不能说满的

1. 当前 Phase 3 已经把 `PSG` 口径收紧为高磷 `SiO2` 层，但还不是完整的 `PSG/SiO2/Si` 光学热模型。
2. 当前结果不能直接当作真实工艺预测值。
3. 当前对文献差距的解释仍需要更真实的堆栈光学 / 局部 `fluence` 标定和 moving interface 模型进一步验证。

## 8. 本轮口径依据

当前这条“`PSG = P2O5-SiO2 glass ~= P-rich SiO2 layer`”的项目口径，主要依据：

1. `POCl3` 扩散相关建模文献把 `PSG` 作为磷进入 `SiO2` 网络后的玻璃层处理，并指出它与 Si 之间常隔着薄 `SiO2`。
2. Fraunhofer 的激光掺杂相关工艺表征把表面前驱体写成 `PSG/SiO2` 堆栈，而不是单纯“PSG 直接接触 Si”。
3. 前驱层激光掺杂统一模型常把薄前驱体层视作弱吸收/近透明层，并把主要 `532 nm` 吸收留在 Si 内部。

## 9. 参考入口

1. [PNNL 2012: A model of phosphosilicate glass deposition by POCl3 to control phosphorus dose in Si](https://www.pnnl.gov/publications/model-phosphosilicate-glass-deposition-pocl3-control-phosphorus-dose-si)
2. [Fraunhofer 2017: Suitability of industrial POCl3 tube furnace diffusion processes for laser doping applications](https://www.ise.fraunhofer.de/content/dam/ise/de/documents/publications/conference-paper/33-eupvsec-2017/Werner_2AV214.pdf)
3. [Fraunhofer 2011: Visible pulsed laser doping using phosphosilicate glass](https://publica.fraunhofer.de/entities/publication/a5194b29-eaed-452c-af70-a00a67bdb073)
4. [MDPI 2021: Unified Model for Laser Doping of Silicon from Doping Precursor Layers](https://www.mdpi.com/1996-1944/14/9/2322)
5. [Christensen 2003: Phosphorus and boron diffusion in silicon under equilibrium conditions](https://doi.org/10.1063/1.1566464)
6. [Velichko 2019: A comprehensive model of high-concentration phosphorus diffusion in silicon](https://arxiv.org/abs/1905.10667)

## 13. Texture Enhancement 第一版

### 13.1 这一步做了什么

在当前 `1D depth-only` 主线里，纹理表面还不能直接显式画成 2D/3D 金字塔，所以这一步先并入了两个降阶项：

1. 有效光学增强  
   `R_eff = k_tex * R_flat`
2. 有效界面面积增强  
   `A_factor = A_real / A_proj`

当前代码入口：

- [phase3_stack_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py)
- [phase2_diffusion.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py)
- [run_phase3.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3.py)

当前采用的文献和步骤映射已经单独记录到：

- [literature-usage-register.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/literature-usage-register.md)

### 13.2 当前采用的物理口径

#### 光学增强

制绒金字塔最直接的作用，不是“显著降低 Si 的平衡熔点”，而是：

1. 降低逃逸反射
2. 提高等效吸收
3. 提高跨熔化阈值的概率

所以当前第一版只把它折成 `R_eff`，不直接改 `T_m`。

但这一步现在要加一个正式口径说明：

1. 如果 `surface_reflectance` 是平面占位值，那么可以再用 `k_tex < 1` 去折纹理光学增强
2. 如果 `surface_reflectance` 是已经包含纹理效应的实测值，就不能再额外乘一次 `k_tex`

当前项目已经按用户最新说明，把 `9%` 解释为实测纹理表面反射率。
因此当前正式展示口径是：

- `surface_reflectance = 0.09`
- `texture_reflectance_multiplier = 1.0`

也就是说，现阶段 texture 主线只看有效面积增强，不再把光学增强重复算进去。

#### 界面面积增强

对于 conformal PSG 覆盖，制绒会让同一投影面积下的：

1. 实际接触面积更大
2. 实际前驱体体积更大

所以当前把 `A_factor` 同时用于：

1. projected-area 下的 source inventory 记账
2. projected-area 下的界面 exchange velocity / 注入通量放大

审查线结论是：在“所有量都按投影面积记账”的口径下，这样做目前是自洽的，不算重复计数。

### 13.3 60W 拆解结果

结果目录：

- [texture_cases_60w](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_60w)

四组对照的核心结果：

| Case | `R_eff` | `A_factor` | `T_peak,Si` | `melt depth` | `peak P` | `junction depth` | `cumulative injected dose` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| flat | `0.090` | `1.000` | `1677.0 K` | `0 nm` | `7.986e20 cm^-3` | `302.7 nm` | `0 cm^-2` |
| optical only | `0.045` | `1.000` | `1678.0 K` | `0 nm` | `8.094e20 cm^-3` | `305.4 nm` | `2.69e13 cm^-2` |
| area only | `0.090` | `1.732` | `1677.0 K` | `0 nm` | `7.986e20 cm^-3` | `302.7 nm` | `0 cm^-2` |
| both | `0.045` | `1.732` | `1678.0 K` | `0 nm` | `8.344e20 cm^-3` | `305.4 nm` | `4.61e13 cm^-2` |

这组结果最重要的物理含义是：

1. `60W` 下 `area-only` 几乎不生效
2. 原因不是面积因子没接进去，而是那一批 texture 敏感性算例当时使用的是 `melt_only` 边界
3. 在这组算例里，flat 和 area-only 都没有真正打开界面注入门
4. optical-only 轻微降低了有效反射，因此把系统推到“门刚好打开一点”的区间

但按最新正式口径，这一组里真正应作为主线读取的是：

- `flat`
- `area only`

其中 `optical only` 和 `both` 现在保留为敏感性测试，不再作为主展示结果。

### 13.4 90W 拆解结果

结果目录：

- [texture_cases_90w](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_90w)

四组对照的核心结果：

| Case | `R_eff` | `A_factor` | `T_peak,Si` | `melt depth` | `peak P` | `junction depth` | `cumulative injected dose` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| flat | `0.090` | `1.000` | `1687.6 K` | `299.0 nm` | `8.213e20 cm^-3` | `366.7 nm` | `2.277e15 cm^-2` |
| optical only | `0.045` | `1.000` | `1692.9 K` | `421.5 nm` | `8.625e20 cm^-3` | `394.4 nm` | `3.783e15 cm^-2` |
| area only | `0.090` | `1.732` | `1687.6 K` | `299.0 nm` | `1.134e21 cm^-3` | `366.7 nm` | `3.584e15 cm^-2` |
| both | `0.045` | `1.732` | `1692.9 K` | `421.5 nm` | `1.263e21 cm^-3` | `394.4 nm` | `6.045e15 cm^-2` |

这组结果说明：

1. optical-only 主要改变热预算、液相分数和熔深
2. area-only 主要改变近表面 `P` 库存与注入强度
3. both 叠加后最强，说明这两类 texture 效应在当前模型里分工明确

但按最新正式口径，这一组真正应作为主线读取的是：

- `flat`
- `area only`

也就是说，在 `90W` 下，当前正式可讲的 texture 结论是：

1. 在保持实测 `9%` 反射率不变的前提下
2. 只加入有效面积增强 `A_factor = 1.732`
3. 峰值 `P` 从约 `8.213e20 cm^-3` 升到约 `1.134e21 cm^-3`
4. 结深基本保持在约 `366.7 nm`

这说明有效面积增强目前更像是“提高近表面供源和注入强度”，而不是单独把结深明显推深。

### 13.5 研究线与审查线结论

研究线当前结论：

1. 这组趋势整体合理
2. `60W` 下 `area-only` 基本无效，符合 melt-gated 注入物理
3. `90W` 下 optical 通道主导热 / 熔化，area 通道主导传质强度，这和文献直觉一致

审查线当前结论：

1. 这版 texture enhancement `通过（带注记）`
2. 没有发现硬性重复计数
3. `source + Si` 总量守恒仍然成立
4. 当前最值得继续补的诊断量，是表面液相分数和累计注入量 / source depletion 的一致性健康度

### 13.6 当前局限

1. `k_tex = 0.5` 目前只保留为历史敏感性测试值，不再是当前正式口径
2. `A_factor = sec(theta)` 目前也是理想金字塔的第一版近似
3. `area-only` 里把界面面积和 conformal source volume 一起折进 projected-area 口径，虽然守恒上自洽，但还值得继续拆成：
   - 只放大 `h_m`
   - 只放大 `Gamma_src,0`
4. 当前仍然是 1D 有效参数化，不是显式 3D 几何热-传质模型

### 13.7 Redistribution 主线口径

用户已确认：对于带超高初始 inactive 表面 P 层的情形，当前更关心的是

1. 激光加热后表面高浓度 P 如何在 Si 内重新分布
2. 这种重分布如何改变近表面 profile、结深和后续片电阻相关量

因此这条线当前正式解释为：

- `redistribution-dominated regime`

而不是：

- `PSG reinjection-dominated regime`

当前已确认的代表算例是：

1. [60W redistribution case](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_60w_area_only_init1e20_inactive1e22/summary.json)
2. [90W redistribution case](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_90w_area_only_init1e20_inactive1e22/summary.json)

这两组的共同特征是：

1. `peak_surface_injection_flux = 0`
2. `cumulative_injected_dose = 0`
3. `source_depletion_fraction` 接近 `0`

所以当前变化主要来自：

- 初始高表面 P 库存的热驱动重分布

而不是：

- PSG source 再次向 Si 注入

### 13.8 当前 redistribution 研究入口

如果继续沿这条线往下做，最值得盯的量是：

1. `final_p_profile.png`
2. `junction_depth_vs_time.png`
3. `silicon_p_profile_sheet_analysis.png`
4. `cumulative_p_dose_vs_depth.png`

这条线更适合回答：

1. 高表面 P 在不同热预算下会被推到多深
2. 表面尖峰会不会被摊平
3. 近表面累计剂量和净施主剂量怎样变化
4. 哪些变化可能对应片电阻改善

### 13.7 参考入口

1. [Campbell & Green 1987](https://www.osti.gov/biblio/6560834)
2. [Baker-Finch & McIntosh 2011 reflectance](https://researchportalplus.anu.edu.au/en/publications/reflection-of-normally-incident-light-from-silicon-solar-cells-wi/)
3. [Baker-Finch & McIntosh 2011 area](https://researchportalplus.anu.edu.au/en/publications/the-contribution-of-planes-vertices-and-edges-to-recombination-at/)
4. [McIntosh & Baker-Finch OPAL2](https://www2.pvlighthouse.com.au/calculators/opal%202/McIntosh%20and%20Baker-Finch%20-%20paper%20on%20OPAL2%20for%2038th%20IEEE.pdf)
5. [Lill 2017](https://www.mdpi.com/1996-1944/10/2/189)
## 10. 60W 主流模型重跑对标

对 `outputs/phase3/p60w_mainstream_default_source/summary.json` 和 `outputs/phase3/p60w_mainstream_default_source_nz1200/summary.json` 的归档结论：

1. 两组均已通过审查线。
2. 两组均已完成研究线对标，当前读法回落到 `300 nm` 基础 emitter。
3. `nz1200` 只是更稳定的展示形式，不改变物理判断：`60W` 仍然是接近阈值但未发生有效重熔驱入。

## 11. Si 内 P Profile 与片电阻分析输出

即使当前 `60W` 没有把结深明显继续推深，Si 内部的 `P` 轮廓本身仍然是重要输出，因为它直接决定：

1. 表层导电能力如何分布
2. 累计掺杂剂量有多少留在 Si 内
3. 后续片电阻模型该从哪里取输入

当前扩散模块已新增三类面向片电阻分析的输出：

1. `silicon_p_profile_sheet_analysis.png`
   - 同时画出 `Initial/Final total P`
   - 同时画出 `Initial/Final net donor (P - Ga)`
2. `cumulative_p_dose_vs_depth.png`
   - 画出从真实表面 `z=0` 积分到任意深度的累计 `P` 剂量
   - 以及扣除 `Ga` 背景后的累计净施主剂量
3. `silicon_profile_analysis.csv`
   - 导出深度、初始/最终 `P`、初始/最终净施主浓度
   - 以及对应的累计总剂量和累计净施主剂量

说明：这里的 `sheet dose` 统一按真实表面 `z=0` 起积分，不再用表观顶部或网格首点代替。

如果存在初始未激活表面 `P` 层，则初始片电阻分析要把它和 `active emitter` 分开记账，前者按前序工序残留 `P` 处理。

对 `outputs/phase3/p60w_mainstream_default_source_nz1200/diffusion/summary.json`，当前关键量是：

1. `initial_sheet_dose_cm2 ≈ 1.9958e15`
2. `final_sheet_dose_cm2 ≈ 1.9958e15`
3. `initial_net_donor_sheet_dose_cm2 ≈ 1.9954e15`
4. `final_net_donor_sheet_dose_cm2 ≈ 1.9954e15`

这进一步支持当前判断：`60W` 下没有明显新增激光驱入，但已有基础 emitter 的 `P` profile 仍然足够作为后续片电阻研究输入。

## 12. 初始未激活表面 P 层

当前模型已支持在 Si 表面额外放置一层“化学上存在、但初始电学上不计入活化施主”的 `P` 层，用来表示前序工序残留 P。

当前测试口径：

1. 厚度：`30 nm`
2. 浓度：`5e20 cm^-3`
3. 与基础 emitter 并存，但在初始片电阻分析中单独记账，不并入 `initial_active_donor`

对 `outputs/phase3/p60w_mainstream_with_inactive_surface_p_nz1200/diffusion/summary.json`，当前关键量是：

1. `initial_sheet_dose_cm2 ≈ 3.5022e15`
2. `initial_active_sheet_dose_cm2 ≈ 1.9958e15`
3. `initial_inactive_sheet_dose_cm2 ≈ 1.5065e15`
4. `initial_net_donor_sheet_dose_cm2 ≈ 1.9954e15`
5. `final_peak_p_concentration_cm3 ≈ 8.2534e20`
6. `final_junction_depth_m ≈ 3.0023e-7`

这一轮的物理读法是：

1. 表面总 `P` 库存明显增加了
2. 但 `60W` 下依然没有有效重熔驱入
3. 所以当前更像是“更高的化学表面库存”，而不是“更深的激光增强结”
4. 这套 active / inactive 分解已经可以直接作为后续片电阻模型输入基线
5. 但 `final_net_donor_sheet_dose_cm2` 目前仍只能读成“化学上限”，不能直接当最终活化载流子剂量

## 13. 60-90W 功率扫描

这轮新增了 `60-90 W` 的功率扫描，当前正式口径采用：

- `outputs/phase3/power_scan_60_90w_dt01`

而不是更早的：

- `outputs/phase3/power_scan_60_90w`

原因是 `dt = 0.2 ns` 版本在高功率区出现了不合理的 `85W/90W` 倒挂，已经被判定为时间步敏感，不再作为正式展示口径。

`dt = 0.1 ns` 版本的核心结果是：

1. `60-85 W`：没有正式非零熔深，但结深从约 `302 nm` 缓慢增加到约 `345 nm`
2. `90 W`：首次出现明确熔深，约 `346 nm`
3. 当前可把阈值读成：明显重熔增强大致落在 `85-90 W` 之间

这轮扫描的关键风险也要一起记住：

1. 对采用 `melt_only` 的那批算例来说，注入判据与 `melt_depth` 统计判据还不完全是同一个阈值
2. 所以 `60-85 W` 区间目前应读成“接近阈值、存在准熔化注入”，而不是“已经形成明确液相熔深”
3. 后续最值得补的是 `85-90 W` 的更细步长扫描和更细 `dt` 收敛检查
