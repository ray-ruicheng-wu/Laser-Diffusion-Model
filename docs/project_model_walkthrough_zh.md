---
tags:
  - laser-doping
  - psg
  - phosphorus
  - silicon
  - modeling
  - tutorial
  - chinese
---

# 激光 PSG 磷掺杂项目总教程（中文）

## 1. 文档目的

这份文档把原来的 `project_total_walkthrough_obsidian` 和 `current-model-summary` 合并成一份统一总教程。它面向两个目标：

- 作为项目当前主线的总说明
- 作为后续继续开发时的统一入口

它重点回答 5 个问题：

1. 我们到底在模拟什么
2. 模型是怎么一步一步搭起来的
3. 当前用了哪些核心公式，为什么这么选
4. 代码结构是什么样的
5. 当前结果、局限和下一步是什么

## 2. 当前项目一句话总结

当前模型是一套 **1D、单脉冲、测量驱动的激光磷重分布/注入模型**。

它的物理主链条是：

`laser -> heating -> phase change -> phosphorus transport -> profile / junction / sheet dose`

在这个物理主模型之上，我们又加了一层 **经验电学校准模型**，把激光后的 `P profile` 转成片电阻 `Rsh`，用来和实验四探针结果对照。

## 3. 我们在模拟什么工艺

当前目标工艺是：

- 波长：`532 nm`
- 表面 source：`PSG`
- 激光前已有基础磷分布
- 激光后发生快速加热、可能局部熔化，并导致 `P` 的重分布和额外注入

当前主线假设包括：

- 激光按单脉冲等效输入
- 深度方向先做 `1D`
- `PSG` 先近似为一层高磷 `SiO2`
- 表面反射率直接使用你的实测值 `9%`
- 初始 profile 不再靠假设函数，而是由 `SIMS + ECV` 直接提供

## 4. 建模流程是怎么一步步建立的

### 4.1 Phase 1：先把热历史算对

第一步只做热模型，不碰掺杂。

原因是激光掺杂最先发生的不是扩散，而是吸收能量、升温、相变。只有热历史大体对了，后面的掺杂才有物理意义。

这一阶段求解的是：

\[
\rho c_{\mathrm{eff}}(T)\frac{\partial T}{\partial t}
=
\frac{\partial}{\partial z}\left(k(T)\frac{\partial T}{\partial z}\right)
+ Q_{\mathrm{laser}}(z,t)
\]

这里：

- `rho` 是密度
- `c_eff(T)` 是带潜热修正的有效热容
- `k(T)` 是热导率
- `Q_laser(z,t)` 是激光热源

这一阶段的主要输出是：

- 表面峰值温度
- 液相分数
- 熔深
- 熔融时间窗

对应代码：

- `src/laser_doping_sim/phase1_thermal.py`
- `run_phase1.py`

### 4.2 Phase 2：在热历史上叠加总磷扩散

第二步把 `P` 的输运接到温度场上。

当前扩散方程求的是总磷浓度：

\[
\frac{\partial C}{\partial t}
=
\frac{\partial}{\partial z}
\left(
D_{\mathrm{eff}}(T,f_l)\frac{\partial C}{\partial z}
\right)
\]

其中有效扩散系数写成：

\[
D_{\mathrm{eff}}(T,f_l)=(1-f_l)D_s(T)+f_lD_l(T)
\]

这里：

- `D_s(T)` 是固态硅中的磷扩散系数
- `D_l(T)` 是液态硅中的磷扩散系数
- `f_l` 是液相分数

为什么这样写：

- 没有融化时，也允许固态扩散，但很弱
- 接近融化时，扩散能力会迅速提高
- 先用连续、稳定的写法把阈值附近的趋势捕捉住

表面边界现在不是固定表面浓度，而是有限库存 source exchange。对当前主线，`PSG -> Si` 的明显注入主要在 `melt_only` 条件下打开。

对应代码：

- `src/laser_doping_sim/phase2_diffusion.py`
- `run_phase2.py`

### 4.3 Phase 3：把 PSG 和实际工艺条件并进来

第三步把实际工艺条件加入热模型和扩散模型：

- `PSG` 表面源
- `532 nm`
- square flat-top 光斑
- 表面反射率 `9%`
- measured initial profile

当前 `PSG` 的热学和光学处理是：

- 成分上视为 `P2O5-SiO2` 玻璃
- 第一版建模里近似为高磷 `SiO2`
- 光学热源仍先用 Beer-Lambert 型吸收

对应代码：

- `src/laser_doping_sim/phase3_stack_thermal.py`
- `run_phase3.py`
- `run_phase3_power_scan.py`

### 4.4 初始条件从假设轮廓升级到 measured profile

项目早期曾用参数化 profile 演示趋势，但现在主线已改成测量驱动。

当前定义是：

\[
P_{\mathrm{total,init}}(z)=P_{\mathrm{SIMS}}(z)
\]

\[
P_{\mathrm{active,init}}(z)=P_{\mathrm{ECV}}(z)
\]

\[
P_{\mathrm{inactive,init}}(z)=\max(P_{\mathrm{SIMS}}(z)-P_{\mathrm{ECV}}(z),0)
\]

这一步的意义是：

- `SIMS` 负责化学总量
- `ECV` 负责电学活化量
- 它们的差负责初始 inactive phosphorus

处理后的主线输入文件：

- `inputs/measured_profiles/ctv_measured_initial_profile.csv`
- `inputs/measured_profiles/ctv_measured_initial_profile_summary.json`

当前表面测量驱动值约为：

- `surface total P = 4.59e21 cm^-3`
- `surface active P = 7.30e20 cm^-3`
- `surface inactive P = 3.86e21 cm^-3`

## 5. 当前为什么还需要电学经验层

热模型和扩散模型输出的是总磷浓度分布，但实验片电阻看的是 electrically active donor。

因此，当前 `Rsh` 计算要分两步：

### 5.1 先把浓度变成导电率

\[
\sigma(z)=q\mu_n(z)n(z)
\]

\[
R_{\mathrm{sh}}=\frac{1}{\int \sigma(z)\,dz}
\]

迁移率目前采用：

- `Masetti @ 300 K`

对应代码：

- `src/laser_doping_sim/sheet_resistance.py`

### 5.2 再决定哪些 P 算 electrically active

这是当前最难、也是最经验化的部分。

现在主线采用的是 **segmented empirical non-active pool activation model**。

初始时：

\[
N_{D,\mathrm{act,init}}
=
N_{D,\mathrm{active,init}}
+ f_{\mathrm{init}}N_{D,\mathrm{inactive,init}}
\]

当前：

- `f_init = 0.06447924522684517`

激光后：

\[
N_{D,\mathrm{pool,final}}
=
N_{D,\mathrm{inactive,final}}
+ N_{D,\mathrm{injected,final}}
\]

\[
N_{D,\mathrm{act,final}}
=
N_{D,\mathrm{active,final}}
+ f_{\mathrm{pool}}(P_{\mathrm{laser}})\,N_{D,\mathrm{pool,final}}
\]

也就是说，当前把“激光后仍不确定活化程度的部分”合并成一个 `non-active pool`，再用实验 `Rsh` 数据按功率反标活化率。

参数表在：

- `inputs/activation_models/segmented_nonactive_pool_empirical_24_60w.csv`

对应代码：

- `src/laser_doping_sim/activation_models.py`
- `run_sheet_resistance_cases.py`

这一步要明确地读成：

- **经验电学校准层**

不是：

- “已经完成了第一性原理活化模型”

最新一轮又把这一步进一步拆成了 **双通道活化分账**：

\[
N_{D,\mathrm{act,final}}
=
N_{D,\mathrm{active,component}}
+ \eta_{\mathrm{inactive}}(P)\,N_{D,\mathrm{inactive,component}}
+ \eta_{\mathrm{inj}}(P)\,N_{D,\mathrm{inj,component}}
\]

也就是把：

- 初始 inactive P 的再激活
- `PSG` 注入 P 的电学活化

分成两条通道分别标定。当前方法见：

- `run_dual_channel_activation_calibration.py`
- `docs/dual-channel-activation-method.md`

这一步目前的结论是：

- `24–48 W` 可以主要由 `initial inactive re-activation` 解释
- 但把低功率区得到的 `eta_inactive(P)` 直接带到 `54/60 W` 会把 `Rsh` 预测得过低
- 所以高功率区已经进入新的 electrical regime

## 6. 当前主线参数是什么

当前 measured 主线的关键参数包括：

- 波长：`532 nm`
- 频率：`500 kHz`
- 光斑：`95 um` square flat-top
- 反射率：`9%`
- `PSG` 磷浓度：设为 measured 表面 `SIMS` 水平，即 `4.5913166904198945e21 cm^-3`
- 背景掺杂：`Ga = 1e16 cm^-3`
- `PSG` 厚度：`150 nm`
- `source effective thickness`：`100 nm`
- `interfacial transport length`：`100 nm`

## 7. 当前结果到哪了

### 7.1 热/扩散主线结果

当前主线扫描目录：

- `outputs/phase3/power_scan_24_60w_step6_measured_ctv_psg_eq_sims`

几个代表点：

#### 24 W

- 峰值硅表面温度：`1151.08 K`
- `max_liquid_fraction = 0`
- 熔深：`0 nm`
- 注入剂量：`0`
- 结深：`372.79 nm`

#### 30 W

- 峰值硅表面温度：`1363.85 K`
- `max_liquid_fraction = 0`
- 熔深：`0 nm`
- 注入剂量：`0`
- 结深：`372.79 nm`

#### 54 W

- 峰值硅表面温度：`1682.31 K`
- `max_liquid_fraction = 0.502`
- 最大熔深：`81.11 nm`
- 注入剂量：`3.01e14 cm^-2`

#### 60 W

- 峰值硅表面温度：`2043.52 K`
- `max_liquid_fraction = 1.0`
- 最大熔深：`611.30 nm`
- 注入剂量：`1.06e16 cm^-2`
- 结深：`448.27 nm`

这说明：

- `24–48 W` 基本仍是未熔化或阈值附近
- `54 W` 开始进入 partial melt / injection 过渡区
- `60 W` 已出现明显重熔和显著注入

### 7.2 片电阻主线结果

当前和实验对照的主线结果在：

- `outputs/phase3/sheet_resistance_segmented_nonactive_pool_anchor_24_60w`

目前复现的是：

- `24 W`: `169.89 -> 163.13 ohm/sq`
- `27 W`: `169.89 -> 150.38`
- `30 W`: `169.89 -> 144.95`
- `33 W`: `169.89 -> 117.588`
- `36 W`: `169.89 -> 105`
- `42 W`: `169.89 -> 99`
- `48 W`: `169.89 -> 89`
- `54 W`: `169.89 -> 82`
- `60 W`: `169.89 -> 69`

这一步说明：

- 当前 measured initial profile + empirical activation layer 已能贴住实验 `Rsh` 趋势
- 但 `Rsh` 结果依然是“物理扩散 + 经验电学校准”的组合

## 8. 当前模型最可靠的部分

目前最可靠的是：

- measured `SIMS + ECV` 驱动的初始 profile
- 1D 热历史与熔深的相对趋势
- 总磷扩散与重分布的趋势
- 使用 `Rsh` 后处理和实验趋势对照

因此，当前模型已经适合：

- 做功率扫描
- 看 `P profile` 前后变化
- 看结深变化
- 看片电阻随功率的趋势

## 9. 当前模型最大的局限

### 9.1 活化模型仍然主要是经验层

现在虽然已经把

- initial inactive phosphorus 的再激活
- injected phosphorus 的活化

在记账上分开了，但高功率区的物理闭合还没有最终确定。

更准确地说：

- 低功率区的 `eta_inactive(P)` 已经可以经验标定
- 高功率区的 `eta_inj(P)` 还不能仅靠现有 `Rsh` 数据唯一确定
- 因而双通道模型目前仍然应读成“经验电学校准层”，而不是已经完全 adopted 的第一性活化动力学

### 9.2 仍然是 1D

横向光斑分布、制绒金字塔侧壁和谷底局部聚能，目前还没有显式进入主方程。

### 9.3 `PSG/SiO2/Si` 界面还没完全显式化

当前 `PSG` 近似已经比最初真实得多，但尚未把可能存在的超薄 `SiO2` 阻挡层写成独立界面输运问题。

## 10. 代码结构应该怎么读

如果要从代码理解项目，建议按这个顺序读：

1. `run_phase3.py`
2. `src/laser_doping_sim/phase3_stack_thermal.py`
3. `src/laser_doping_sim/phase2_diffusion.py`
4. `src/laser_doping_sim/measured_profiles.py`
5. `src/laser_doping_sim/sheet_resistance.py`
6. `src/laser_doping_sim/activation_models.py`
7. `run_phase3_power_scan.py`
8. `run_sheet_resistance_cases.py`

理由是：

- 先看主入口知道参数从哪里来
- 再看热模型
- 再看扩散
- 再看 measured 输入和电学后处理

## 11. 这份总教程配套看哪些文件

### 公式和文献

- `docs/formula-reference-register.md`
- `docs/literature-usage-register.md`
- `docs/laser-activation-literature-notes.md`

### 阶段分析

- `docs/phase1-analysis.md`
- `docs/phase2-analysis.md`
- `docs/phase3-analysis.md`
- `docs/phase3-physics-validation.md`

### 教学文档

- `docs/modeling_tutorial_for_materials_undergrads.md`
- `docs/python_code_teaching_for_beginners.md`

### 工作区地图

- `docs/workspace-file-classification.md`

## 12. 下一步最值得做什么

当前最值得的升级顺序是：

1. 给 `54W+` 单独建立高功率活化闭合，而不是继续沿用低功率 `eta_inactive(P)`
2. 把 `initial inactive re-activation` 和 `injected P activation` 的高功率约束继续补强
3. 把 texture enhancement 做成显式几何/有效光学模型
4. 继续细化 `PSG/SiO2/Si` 界面

## 13. 一句话结尾

现在这套模型最重要的价值，不是已经“完美预测了所有物理”，而是它已经把：

- 热
- 相变
- 总磷扩散
- measured 初始条件
- 片电阻对照

这几条主线连接起来了，并且能够稳定地支持下一轮更细的物理升级。
