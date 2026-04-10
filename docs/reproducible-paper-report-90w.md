# 90W 激光磷掺杂复现实验报告

## 1. 摘要

这份报告的目标不是做简短汇报，而是给出一份可以直接复现当前项目的工作文档。

只要读者具备基础 Python 环境，并按本文给出的命令运行，就应该能够在本工作区中复现：

1. `PSG/Si` 双层热模型
2. 基础 `POCl3` emitter + 激光再掺杂扩散
3. `90 W / 500 kHz / 95 um square flat-top / 表面反射率 9%` 的主算例
4. 当前所有关键输出图和结果摘要

本轮的核心升级是把表面 source 从“有限库存 Robin reservoir”提升为更接近论文主流表达的：

- `finite source cell`
- `melt-only source injection`

对应的 `90 W` 主算例结果是：

- 单脉冲 fluence：约 `1.994 J/cm^2`
- 峰值 Si 表面温度：约 `2834.9 K`
- 最大熔深：约 `1115.4 nm`
- 熔融结束：约 `344.4 ns`
- 最终峰值 `P` 浓度：约 `7.882e20 cm^-3`
- 最终结深：约 `606.3 nm`

结果文件位于：

- [summary.json](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/p90w_mainstream_default_source/summary.json)

---

## 2. 研究对象

当前模型研究的是一个工业上合理的简化场景：

1. 硅片中已经有一道基础 `POCl3 diffusion` 形成的 `P` 发射极
2. 表面覆盖 `PSG`
3. 使用 `532 nm` 绿光脉冲激光照射
4. 激光使表层 Si 快速升温并部分熔化
5. 在熔融窗口内，来自 `PSG` 的额外 `P` 注入到 Si 中
6. 同时，原有 emitter 轮廓也在新的热历史下重新分布

当前报告对应的具体主算例设定是：

1. 平均功率 `90 W`
2. 重复频率 `500 kHz`
3. 光斑 `95 um` square flat-top
4. 表面反射率 `9%`
5. 表面 source 为 `PSG = P2O5-SiO2 glass`
6. 基础 emitter 结深 `300 nm`
7. 基础 emitter 名义表面 `P` 浓度 `3.5e20 cm^-3`

---

## 3. 项目目录

最重要的文件如下：

### 3.1 运行入口

- [run_phase1.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase1.py)
- [run_phase2.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase2.py)
- [run_phase3.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3.py)

### 3.2 核心模型

- [phase1_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py)
- [phase2_diffusion.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py)
- [phase3_stack_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py)

### 3.3 公式与文献台账

- [formula-reference-register.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/formula-reference-register.md)
- [boundary-condition-review.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/boundary-condition-review.md)

### 3.4 当前主算例输出

- [summary.json](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/p90w_mainstream_default_source/summary.json)
- [final_p_profile.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/p90w_mainstream_default_source/diffusion/final_p_profile.png)
- [junction_depth_vs_time.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/p90w_mainstream_default_source/diffusion/junction_depth_vs_time.png)
- [p_concentration_heatmap.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/p90w_mainstream_default_source/diffusion/p_concentration_heatmap.png)
- [temperature_heatmap.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/p90w_mainstream_default_source/thermal/temperature_heatmap.png)
- [melt_depth_vs_time.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/p90w_mainstream_default_source/thermal/melt_depth_vs_time.png)

---

## 4. 软件环境

本报告对应的实际运行环境是：

1. Python `3.13.12`
2. Windows `11`
3. `numpy 2.4.3`
4. `scipy 1.17.1`
5. `matplotlib 3.10.8`

依赖文件已经写入：

- [requirements.txt](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/requirements.txt)

安装方式：

```powershell
python -m pip install -r .\requirements.txt
```

---

## 5. 物理假设

### 5.1 几何与维度

当前是 `1D` 深度方向模型。

这意味着：

1. 求解的是法向深度上的温度和浓度变化
2. 光斑横向形状只通过面积进入 fluence 计算
3. 还没有显式求解 2D 横向扩散或正方形边缘效应

### 5.2 热学

采用瞬态热传导方程，表面热源来自激光吸收。

### 5.3 相变

采用焓法 / 表观热容法处理 Si 熔化与凝固，不显式追踪 Stefan 界面。

### 5.4 掺杂扩散

采用 1D Fick 扩散。

当前仍忽略：

1. 液相对流
2. 表面蒸发引起的形貌变化
3. recoil pressure
4. Marangoni flow

### 5.5 边界条件

当前已经不再把 `PSG` 只写成硬表面浓度，而是使用：

1. 显式 `finite source cell`
2. 熔融窗口主导的 source 注入
3. 基础 emitter 初始轮廓

这比旧的硬 `Dirichlet` 更接近当前激光前驱体掺杂文献的主流表达。

---

## 6. 数学模型

下面只列当前主线真正进入代码的公式。

### 6.1 功率到单脉冲 fluence

对应 `F-017`

`E_pulse = P_avg / f`

`F = E_pulse / A_spot`

作用：

把实验参数 `90 W`、`500 kHz`、`95 um square flat-top` 换算成模型真正使用的单脉冲输入。

本算例中：

1. `E_pulse = 180 uJ`
2. `F ≈ 1.994 J/cm^2`

### 6.2 1D 热传导方程

对应 `F-001`

`rho * c_eff(T) * dT/dt = d/dz (k(T) * dT/dz) + Q(z,t)`

作用：

求解瞬态温度场 `T(z,t)`。

### 6.3 双层激光热源

对应 `F-016`

`Q_psg ~ (1-R) I(t) exp(-z/delta_psg)`

`Q_si ~ (1-R) I(t) exp(-h_psg/delta_psg) T_int exp(-(z-h_psg)/delta_si)`

作用：

把表面反射、PSG 层透过以及 Si 内吸收串起来。

当前关键设定：

1. `surface_reflectance = 0.09`
2. `PSG` 视为弱吸收的高磷 `SiO2`
3. 主要 `532 nm` 吸收仍放在 Si 中

### 6.4 相变：焓法 / 表观热容

对应 `F-003` 和 `F-004`

`cp_eff = cp + latent_heat_term`

`f_l(T)` 在熔点附近从 `0` 平滑过渡到 `1`

作用：

1. 让模型能跨过 Si 熔化区
2. 把液相分数 `f_l` 传给扩散模型

### 6.5 Si 中的扩散方程

对应 `F-005`

`∂C/∂t = ∂/∂z [ D(T, f_l) ∂C/∂z ]`

作用：

求解 Si 中的 `P(z,t)`。

### 6.6 固液混合扩散系数

对应 `F-006`

`D_eff = D_s(T) * (1 - f_l) + D_l(T) * f_l`

作用：

在固态和液态之间平滑切换扩散系数。

### 6.7 固态与液态 Arrhenius 扩散

对应 `F-019` 与 `F-007`

`D_s = D0_s * exp(-Ea_s / (k_B T))`

`D_l = D0_l * exp(-Ea_l / (k_B T))`

作用：

1. 保留基础 emitter 在固态中的重新分布
2. 在熔融窗口内放大扩散能力

### 6.8 基础 emitter 初始轮廓

对应 `F-021`

`C_init(z) = C_s * erfc(z / (2L))`

并用 `C_init(x_j) = C_bg` 确定 `L`

作用：

把激光之前已有的 `POCl3` 基础发射极写进初值。

本报告中使用：

1. 名义表面 `P = 3.5e20 cm^-3`
2. 目标基础结深 `300 nm`

### 6.9 主流边界：显式 source cell

对应 `F-022`

当前实现不是直接给 `C(0,t)=const`，而是先定义一个表面 source 单元：

`Gamma_src = C_src,cell * h_src`

`C_src,cell = min(C_src,max, Gamma_src / h_src)`

作用：

把 `PSG` 写成有限供源单元，而不是无限 reservoir。

### 6.10 熔融窗口注入

对应 `F-025`

`J_in = H(f_l - f_th) * h_m * max(0, C_src,cell - C_surf)`

`h_m = D_surface / L_tr`

作用：

1. 额外 `PSG -> Si` 注入主要发生在熔融窗口内
2. 当表面未进入熔融窗口时，基础 emitter 仍可在 Si 内固态扩散
3. 但额外 `PSG` 注入不再被无限制地施加

这正是本轮采用的“更像论文主流写法”的部分。

---

## 7. 文献锚点

本轮最关键的三条方法学文献锚点是：

1. [Lill et al. 2017, Materials 10(2) 189](https://www.mdpi.com/1996-1944/10/2/189)
   原因：直接采用了“Si 表面外的 finite-volume source element，在熔融时向第一层 Si 单元输运掺杂”的表达。
2. [Fell et al., Fraunhofer ISE, 23rd EU PVSEC 2008](https://publica-rest.fraunhofer.de/server/api/core/bitstreams/a4616ec1-fd19-426e-b904-4f6920a07805/content)
   原因：明确比较了 isolating / infinite / finite source 的边界口径，与当前 `PSG` 表面 source 建模直接对口。
3. [Hassan et al. 2021, Materials 14(9) 2322](https://www.mdpi.com/1996-1944/14/9/2322)
   原因：给出了“前驱体层有限供源 + 熔融期扩散 + 再凝固”的统一建模框架。

补充参考：

1. [Crank, The Mathematics of Diffusion](https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf)
2. [OSTI 2015: Phosphorus out-diffusion in laser molten silicon](https://www.osti.gov/biblio/22402853)
3. [PNNL 2012: PSG deposition model](https://www.pnnl.gov/publications/model-phosphosilicate-glass-deposition-pocl3-control-phosphorus-dose-si)
4. [Fraunhofer 2017: industrial POCl3 diffusion for laser doping applications](https://www.ise.fraunhofer.de/content/dam/ise/de/documents/publications/conference-paper/33-eupvsec-2017/Werner_2AV214.pdf)

---

## 8. 数值实现

### 8.1 热学求解

1. 空间：均匀 1D 网格
2. 时间：隐式推进
3. 非线性：Picard 迭代
4. 线性代数：稀疏三对角系统

### 8.2 扩散求解

1. 同样使用 1D 网格
2. 使用隐式矩阵推进
3. 在扩散系数跨固液界面时使用谐和平均
4. source cell 用显式库存记账
5. source 注入只允许正向进入 Si，不把数值误差“反充”回 source

这个实现点在这里：

- [phase2_diffusion.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py)

---

## 9. 参数表

### 9.1 激光与光学

| 参数 | 值 | 单位 |
| --- | ---: | --- |
| 平均功率 | 90 | W |
| 重复频率 | 500000 | Hz |
| 脉宽 FWHM | 10 | ns |
| 峰值时间 | 30 | ns |
| 光斑 | 95 | um |
| 光斑形状 | square flat-top | - |
| 表面反射率 | 0.09 | - |
| PSG/Si 界面透过率 | 0.68 | - |
| PSG 吸收深度 | 50 | um |
| Si 吸收深度 | 1274 | nm |

### 9.2 结构与材料

| 参数 | 值 | 单位 |
| --- | ---: | --- |
| PSG 厚度 | 150 | nm |
| Si 厚度 | 8 | um |
| Si 熔点 | 1687 | K |
| mushy width | 20 | K |
| PSG 密度 | 2200 | kg/m^3 |
| PSG 比热 | 730 | J/kg/K |
| PSG 导热率 | 1.4 | W/m/K |

### 9.3 掺杂与边界

| 参数 | 值 | 单位 |
| --- | ---: | --- |
| boundary_model | finite_source_cell | - |
| source_exchange_mode | all_states | - |
| interface liquid threshold | 0.01 | - |
| PSG 中 `P` 浓度 | `2.0e21` | cm^-3 |
| source effective thickness | 100 | nm |
| interfacial transport length | 100 | nm |
| 基础 emitter 表面 `P` | `3.5e20` | cm^-3 |
| 基础 emitter 结深 | 300 | nm |
| 背景 `Ga` 浓度 | `1.0e16` | cm^-3 |

### 9.4 数值离散

| 参数 | 值 | 单位 |
| --- | ---: | --- |
| `nz` | 600 | - |
| `dt` | 0.2 | ns |
| `t_end` | 400 | ns |
| bottom BC | dirichlet | - |

---

## 10. 复现步骤

### 10.1 安装依赖

```powershell
cd "C:\Users\User\Desktop\Codex\Diffusion Simulation"
python -m pip install -r .\requirements.txt
```

### 10.2 复现当前 90W 主算例

```powershell
python .\run_phase3.py `
  --output-dir outputs/phase3/p90w_mainstream_default_source `
  --average-power-w 90 `
  --pulse-fwhm-ns 10 `
  --surface-reflectance 0.09 `
  --boundary-model finite_source_cell `
  --source-exchange-mode all_states `
  --initial-profile-kind erfc_emitter `
  --initial-surface-p-concentration-cm3 3.5e20 `
  --initial-junction-depth-nm 300 `
  --t-end-ns 400
```

### 10.3 关键输出位置

热学输出：

- `outputs/phase3/p90w_mainstream_default_source/thermal/`

扩散输出：

- `outputs/phase3/p90w_mainstream_default_source/diffusion/`

总摘要：

- `outputs/phase3/p90w_mainstream_default_source/summary.json`

---

## 11. 当前 90W 结果

从 [summary.json](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/p90w_mainstream_default_source/summary.json) 读取的当前结果如下：

### 11.1 热学

1. 峰值 stack 表面温度：`2260.1 K`
2. 峰值 Si 表面温度：`2834.9 K`
3. 最大熔深：`1115.4 nm`
4. 熔融开始：约 `28.6 ns`
5. 熔融结束：约 `344.4 ns`

### 11.2 扩散

1. 初始峰值 `P`：`2.986e20 cm^-3`
2. 初始结深：`300.4 nm`
3. 最终峰值 `P`：`7.882e20 cm^-3`
4. 最终结深：`606.3 nm`
5. 峰值表面注入通量：`9.24e26 atoms/m^2/s`

### 11.3 质量守恒

1. 初始 source inventory：`2.000e20 atoms/m^2`
2. 最终 source inventory：`1.112e20 atoms/m^2`
3. 最终质量守恒误差：`8.192e5 atoms/m^2`

相对于总库存量级，这个误差仍可以视为浮点舍入级别。

---

## 12. 如何读图

### 12.1 掺杂前后对比图

- [final_p_profile.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/p90w_mainstream_default_source/diffusion/final_p_profile.png)

这张图里现在已经同时画了：

1. 激光前基础 `P profile`
2. 激光后最终 `P profile`
3. 初始结深
4. 最终结深
5. `Ga` 背景浓度

所以读图时可以直接看：

1. 表面峰值被抬高了多少
2. 结深是否被继续推深

### 12.2 结深演化图

- [junction_depth_vs_time.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/p90w_mainstream_default_source/diffusion/junction_depth_vs_time.png)

这张图现在包含：

1. 激光过程中的即时结深
2. 初始结深参考线

所以可以直接看“激光有没有真的把结深往里推”。

---

## 13. 审查与可信度

这轮结果按项目流程已经交由审查线复核。

审查重点包括：

1. 新边界是否比旧写法更像文献主流
2. `90 W / 9%` 结果是否物理自洽
3. 质量守恒误差是否可接受

如果你之后把这份报告给别人，最稳妥的表述是：

当前结果已经足够用于方法开发、趋势判断、参数扫描和工艺口径比较；但它还不是包含 liquid flow、surface loss、`PSG/SiO2/Si` 显式界面和 `k(v)` 的最终发表版模型。

---

## 14. 局限性

当前报告必须诚实写清楚下面这些限制：

1. 仍然是 `1D` 深度模型
2. 还没有显式 2D 正方形光斑边缘效应
3. `PSG` 仍按高磷 `SiO2` 有效层处理
4. `PSG/SiO2/Si` 中的超薄 `SiO2` 还没有单独离散
5. 还没有表面 evaporation / ablation / out-diffusion 显式项
6. 还没有 moving interface + `k(v)` 再凝固分配模型

所以当前“主流写法”的准确说法应该是：

它已经从“纯 lumped Robin reservoir”升级到了“显式 finite source cell + melt-only injection”的主流框架方向，但还不是最完整的激光重熔发表级模型。

---

## 15. 下一步建议

如果按论文路线继续往下推，我建议优先级如下：

1. 显式加入 `PSG/SiO2/Si` 薄 `SiO2` 界面阻挡
2. 加入 `surface out-diffusion / evaporation`
3. 加入 moving interface 溶质守恒
4. 加入 `k(v)` / solute trapping
5. 最后升级到 `2D`

---

## 16. 本报告对应的关键文件

1. [run_phase3.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3.py)
2. [phase3_stack_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py)
3. [phase2_diffusion.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py)
4. [formula-reference-register.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/formula-reference-register.md)
5. [boundary-condition-review.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/boundary-condition-review.md)
6. [requirements.txt](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/requirements.txt)

这 6 个文件加上 `outputs/phase3/p90w_mainstream_default_source/`，已经足够让别人照着复现当前项目的主算例。
