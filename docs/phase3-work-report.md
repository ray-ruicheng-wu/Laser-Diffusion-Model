# Phase 3 工作报告

## 1. 阶段信息

- 阶段名称：Phase 3 第一轮，`PSG/Si` 双层热模型基线
- 日期：`2026-04-07`
- 目标：
  1. 建立 `PSG/Si` 双层热模型
  2. 用这条热历史重驱动现有扩散模块
  3. 和文献量级做第一轮对照
- 关联输出目录：
  - `outputs/phase3/default_run/thermal`
  - `outputs/phase3/default_run/diffusion`

## 2. 本阶段实现内容

本阶段新增了：

1. `PSG/Si` 双层热模块 [phase3_stack_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py)
2. 运行入口 [run_phase3.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3.py)
3. 双层热结果到 Si 子域热历史的转换接口
4. 基于双层热历史的现有扩散重驱动
5. `PSG` 口径收紧为 `phosphosilicate glass = P2O5-SiO2 glass ~= 高磷 SiO2 层`
6. 非融化条件下加入固相 Arrhenius 扩散和固/液统一 Robin 注入边界

本阶段没有做：

1. 完整 `PSG/SiO2/Si` TMM 光学
2. moving interface 与 `k(v)` 再凝固模型
3. 功率-光斑-fluence 的实验标定反算

## 3. 生成结果与输出文件位置

关键结果：

1. 激光平均功率：`30 W`
2. 重复频率：`500 kHz`
3. 脉宽 FWHM：`10 ns`
4. 单脉冲能量：`60 uJ`
5. 当前光斑设定：`flat-top square`
6. 正方形边长：`95 um`
7. 当前等效 fluence：`0.665 J/cm^2`
8. 峰值 stack 表面温度：`1132.5 K`
9. 峰值 Si 表面温度：`1360.8 K`
10. 最大 Si 熔深：`0 nm`
11. 最终峰值 `P` 浓度：`1.11e11 cm^-3`
12. 最终结深：`0 nm`

关键输出文件：

1. [phase3 总摘要](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/default_run/summary.json)
2. [thermal 摘要](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/default_run/thermal/summary.json)
3. [diffusion 摘要](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/default_run/diffusion/summary.json)
4. [双层温度热图](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/default_run/thermal/temperature_heatmap.png)
5. [双层液相图](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/default_run/thermal/liquid_fraction_heatmap.png)
6. [熔深曲线](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/default_run/thermal/melt_depth_vs_time.png)
7. [扩散结果图](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/default_run/diffusion/final_p_profile.png)

## 4. 狗叫的审查记录

- 审查状态：`通过`
- 审查对象：
  - [run_phase3.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3.py)
  - [phase3_stack_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py)
  - [phase2_diffusion.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py)
  - [phase2 summary](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase2/default_run/summary.json)
  - [phase3 summary](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/default_run/summary.json)
- 重点检查项：
  1. `PSG` 新口径是否与代码和输出一致
  2. `F-019` / `F-020` 是否与代码实现一致
  3. 输入能量换算、边界条件、守恒和量纲是否一致
  4. 非融化弱注入与融化默认案例是否都自洽
- 审查结论摘要：
  1. `F-019` / `F-020` 与代码一致，固态和液态都允许 Robin 注入
  2. 非融化基线下即使改成 `all_states`，默认注入也应保持很弱；是否形成有效掺杂取决于固态界面交换与热历史强度
  3. 融化默认案例仍守恒，`mass_balance_error ≈ -1.43e4 atoms/m^2`，相对初始源量可忽略
  4. 轻微风险：`interface_liquid_threshold` 仍保留在参数表里，但当前不再决定边界是否开启，容易引起口径误读

## 5. 与文书老哥提供的参考文献对比

文书老哥当前给出的关键参考是：

1. 双层热学应采用分层热传导和分层光学热源
2. moving interface 与 `k(v)` 是后续高阶缺口
3. `30 W @ 500 kHz @ 95 um square flat-top` 已可直接换算成单脉冲 `fluence`
4. `PSG` 更合理的材料解释是 `P2O5-SiO2` 玻璃层，而现实样品中常见的是 `PSG/SiO2/Si` 堆栈
5. 非融化条件下不能把扩散和注入强行设成零；更合理的是保留固态扩散和有限通量边界

与文献典型结果对比：

| 量 | 当前 Phase 3 | 文献参考 |
| --- | ---: | ---: |
| Si 是否熔化 | `否` | 同类 LDSE 文献通常隐含存在局部重熔 |
| 结深 | `0 nm` | 常见 `0.5–0.7 um` |
| 峰值 `P` 浓度 | `1.11e11 cm^-3` | 常见 `4e19–5e19 cm^-3` |

这说明：

1. 当前最小 `PSG/Si` 双层基线本身仍不足以解释文献工艺。
2. 只补双层热学、但不补更真实光学堆栈和功率-光斑一致性，结果仍会明显偏冷。

## 6. 与现实/文献模型的误差分析

### 热历史误差

当前 Phase 3 仍然不给出熔化，这和文献里的深掺杂轮廓不兼容。最可能缺失的是：

1. 更真实的 `PSG/SiO2/Si` 光学堆栈
2. 当前 `30 W @ 500 kHz @ 95 um square flat-top` 下的局部有效 `fluence` 仍会受到堆栈光学和扫描重叠影响
3. 可能仍缺少界面光学/热阻细节

### 掺杂轮廓误差

因为当前不熔化，所以扩散直接归零。这个误差不是扩散公式单独造成的，而是热历史先把扩散通道关掉了。

### source 与边界误差

当前 source 仍然是有限库存近似，但在“不熔化”条件下，它不会真正参与注入，所以此时 source 模型不是主误差源。

### 模型阶次误差

当前还是：

- 单脉冲
- 固定点
- 最小双层 Beer-Lambert

与文献中真实扫描工艺之间还有明显阶次差距。

## 7. 每一步对应的物理公式

### PSG 材料闭合

- `F-018`：`PSG ~= P2O5-SiO2 glass ~= P-rich SiO2 layer`

### 固态扩散

- `F-019`：`D_s = D0_s exp(-E_a,s / (k_B T))`
- `F-020`：固/液统一 Robin 注入边界

### 热传导

- `F-014`：分层热传导
  `rho_j c_{p,j}(T) dT_j/dt = d/dz [ k_j(T) dT_j/dz ] + Q_j(z,t)`

### 双层光学热源

- `F-016`：分层 Beer-Lambert + 界面透射近似
  `Q_psg ~ (1 - R_surface) I(t) exp(-z / delta_psg)`
  `Q_si ~ (1 - R_surface) I(t) exp(-h_psg / delta_psg) T_interface exp(-(z-h_psg)/delta_si)`

### 输入能量换算

- `F-017`：平均功率到单脉冲能量与 fluence
  `E_pulse = P_avg / f`
  `F = E_pulse / A_spot`

### Si 相变

- `F-003` / `F-004`：焓法 / 液相分数平滑

### 掺杂扩散

- `F-005`：1D Fick 扩散
- `F-006`：固/液相混合扩散率
- `F-009`：Robin 界面传质边界
- `F-010`：总量守恒库存更新

## 8. 当前风险

1. `PSG` 光学参数仍是占位值。
2. `SiO2` 尚未显式入层。
3. 当前 `95 um` square flat-top 与 `500 kHz` 已按实测固定；剩余不确定性主要在堆栈光学和扫描重叠。
4. 当前没有 moving interface 和 `k(v)`。
5. 当前虽然已有极弱固态注入，但还没有把预扩散初始 P 轮廓并进来。
6. 当前结果不能直接当作真实工艺预测值。

## 9. 下一步

下一轮最值得做的是：

1. 在已确认 `500 kHz / 95 um square flat-top` 的前提下，继续标定不同平均功率工作点的单脉冲输入
2. 把 `PSG/SiO2/Si` 的光学堆栈再细化一层
3. 然后再回到 moving interface + `k(v)` 掺杂模型

原因很直接：

- 当前最大缺口首先是热历史不够强
- 不是扩散方程又坏了
## 10. 2026-04-08 60W 主流模型重跑归档

### 阶段信息

- 阶段名称：`60W` 主流模型重跑归档
- 日期：`2026-04-08`
- 目标：将两组 60W 结果归档到正式阶段报告
- 关联输出目录：
  - `outputs/phase3/p60w_mainstream_default_source/summary.json`
  - `outputs/phase3/p60w_mainstream_default_source_nz1200/summary.json`

### 本阶段实现内容

本次只做归档和口径对齐，没有修改求解器代码。

### 生成结果与输出文件位置

- `default_source`
  - peak Si surface temperature: `1676.7 K`
  - `max_liquid_fraction = 0.0509`
  - final junction depth: `300.4 nm`
  - final peak P: `2.99e20 cm^-3`
- `nz1200`
  - peak Si surface temperature: `1675.6 K`
  - `max_liquid_fraction = 0`
  - final junction depth: `300.2 nm`
  - final peak P: `3.25e20 cm^-3`

### 狗叫的审查记录

- 审查状态：`通过`
- 审查对象：
  - `outputs/phase3/p60w_mainstream_default_source/summary.json`
  - `outputs/phase3/p60w_mainstream_default_source_nz1200/summary.json`
- 结论：两组结果均已通过审查线，可正式归档。

### 与文书老哥提供的参考文献对比

文献对标结论与当前结果一致：60W 在当前 `PSG/Si` 最小模型下已经接近阈值，但尚未触发有效重熔驱入；结深基本保持在 `300 nm` 基础 emitter 附近。

### 与现实/文献模型的误差分析

- 当前差异主要来自模型仍缺少更真实的 `PSG/SiO2/Si` 光学堆栈和 moving interface。
- `nz1200` 主要改善数值收敛和展示稳定性，不改变物理判断。

### 每一步对应的物理公式

- `F-017`：`E_pulse = P_avg / f`, `F = E_pulse / A_spot`
- `F-018`：`PSG ~= P2O5-SiO2 glass ~= P-rich SiO2 layer`
- `F-014`：双层热传导
- `F-016`：双层光学热源最小近似
- `F-019`：固相 P 扩散 Arrhenius
- `F-020`：固/液统一 Robin 注入边界
- `F-021`：`erfc` 基线 emitter 初始轮廓

### 当前风险与下一步

1. `default_source` 与 `nz1200` 的差异主要是数值展示稳定性，不是物理结论差异。
2. 后续若要继续提升级别，应先补更真实的光学堆栈和 moving interface。
3. 展示口径优先使用 `nz1200`。

## 11. 2026-04-08 Texture Enhancement 第一版

### 阶段信息

- 阶段名称：`Phase 3 texture enhancement first pass`
- 日期：`2026-04-08`
- 目标：
  1. 评估 texture 对热预算和界面面积的影响
  2. 把 texture 对界面面积的影响折算进 `A_factor`
  3. 用 `60W` / `90W` 的拆解测试检查两类效应各自影响什么
- 关联输出目录：
  - [texture_cases_60w](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_60w)
  - [texture_cases_90w](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_90w)

### 本阶段实现内容

本阶段新增了：

1. 热模型中的 `texture_reflectance_multiplier`
2. 扩散边界中的 `texture_interface_area_factor`
3. 理想金字塔侧壁角到面积因子的换算：`A_factor = sec(theta)`
4. 新的诊断量：
   - `effective_surface_reflectance`
   - `cumulative_injected_dose_cm2`
   - `source_depletion_fraction`
   - `melt_gate_active_fraction`

关联代码：

1. [phase3_stack_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py)
2. [phase2_diffusion.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py)
3. [run_phase3.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3.py)
4. [run_phase3_power_scan.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3_power_scan.py)

### 生成结果与位置

#### `60W`

1. [flat summary](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_60w/flat/summary.json)
2. [optical_only summary](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_60w/optical_only/summary.json)
3. [area_only summary](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_60w/area_only/summary.json)
4. [both summary](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_60w/both/summary.json)

结论：

1. `area-only` 与 `flat` 基本重合
2. `optical-only` 把系统推到界面门开始微弱打开的区域
3. `both` 的累计注入量高于 `optical-only`
4. 但按用户后续澄清，`9%` 是实测纹理表面反射率，因此正式口径不再采用 `optical-only` / `both`

#### `90W`

1. [flat summary](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_90w/flat/summary.json)
2. [optical_only summary](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_90w/optical_only/summary.json)
3. [area_only summary](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_90w/area_only/summary.json)
4. [both summary](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_90w/both/summary.json)

结论：

1. `optical-only` 主要抬高温度与熔深
2. `area-only` 主要抬高近表面 `P` 浓度和累计注入量
3. `both` 同时推高热预算和注入强度
4. 正式展示口径现在改为只看 `area-only`，因为 `9%` 反射率已视为实测值

### 审查线记录

- 审查状态：`通过（带注记）`
- 审查结论：
  1. 未发现硬性重复计数
  2. `source + Si` 守恒继续成立
  3. `60W area-only` 基本不动是合理结果，因为 `melt_gate_active_fraction ≈ 0`
  4. 建议额外关注 `max_surface_liquid_fraction` 与 `cumulative_injected_vs_depletion_relative_error`

### 研究线记录

- 研究状态：`通过（带改进建议）`
- 研究结论：
  1. 当前趋势与文献支持的物理分工一致
  2. `60W` 下 area 通道不显影，说明当前瓶颈是热预算是否跨过熔融门
  3. `90W` 下 optical 通道主导熔深，area 通道主导传质增强
  4. 下一步最值得补的是：
     - 拆分“只放大界面面积”和“只放大 source inventory”
     - 给 `R_eff` 引入测量或 ray-tracing 标定

### 当前正式口径

用户已明确说明：`surface_reflectance = 0.09` 是实测值。  
因此从这一轮之后，主线口径改成：

1. `surface_reflectance = 0.09`
2. `texture_reflectance_multiplier = 1.0`
3. 只研究有效面积因子 `A_factor`

这意味着：

1. `optical-only` 和 `both` 仍保留为敏感性测试
2. 当前正式 texture 结果应读：
   - [60W area_only](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_60w/area_only/summary.json)
   - [90W area_only](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_90w/area_only/summary.json)

### 文献与公式归档

本阶段已同步更新：

1. [literature-usage-register.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/literature-usage-register.md)
2. [formula-reference-register.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/formula-reference-register.md)
3. [phase3-analysis.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/phase3-analysis.md)

新增并采用的 texture 公式：

1. `F-028`: `R_eff = k_tex * R_flat`
2. `F-029`: `A_factor = A_real / A_proj`
3. `F-030`: `Gamma_src,proj = A_factor * C_src * h_src`
4. `F-031`: `J_in,proj = A_factor * h_m * max(0, C_src - C_surf)`

### Redistribution 研究方向确认

用户已确认，带超高 inactive 表面层的这条线现在保留并作为单独研究方向：

- 不把它再解释成 `PSG` 再注入
- 专门把它解释成“高初始表面 P 库存的激光重分布”

当前代表算例：

1. [60W redistribution](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_60w_area_only_init1e20_inactive1e22/summary.json)
2. [90W redistribution](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/texture_cases_90w_area_only_init1e20_inactive1e22/summary.json)

当前统一读法：

1. `peak_surface_injection_flux = 0`
2. `cumulative_injected_dose = 0`
3. 所以 profile 变化来自初始高表面 P 的热驱动再分布
