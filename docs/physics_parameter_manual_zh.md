# 物理参数与命令行参数手册

这份手册是给想“系统理解模型参数”的用户准备的。

目标不是只告诉你参数名，而是把每个参数都放回到：

1. 它对应什么物理量
2. 它出现在哪个方程里
3. 它为什么会影响结果
4. 增大或减小它，一般会产生什么后果

## 1. 先记住整套模型的主方程

### 1.1 热学

单层硅热模型的核心是：

```text
rho * c_eff(T) * dT/dt = d/dz [ k_eff(T) * dT/dz ] + Q(z,t)
```

其中：

- `rho` 是密度
- `c_eff(T)` 是表观热容
- `k_eff(T)` 是导热率
- `Q(z,t)` 是激光体热源

### 1.2 固液混合层

液相分数用窄温区平滑表示：

```text
f_l(T) =
0,                           T <= solidus
(T - solidus) / mushy_width, solidus < T < liquidus
1,                           T >= liquidus
```

### 1.3 扩散

磷扩散的核心是：

```text
dC/dt = d/dz [ D_eff(T, f_l) * dC/dz ]
```

```text
D_eff = D_solid(T) * (1 - f_l) + D_liquid(T) * f_l
```

### 1.4 界面注入

表面 source 到 Si 的交换采用：

```text
J = h_m (C_src - C_surf)
```

其中

```text
h_m ~ D_surface / L_tr
```

### 1.5 片电阻

`Rsh` 不是用总 P 直接算，而是用 electrically active donor：

```text
sigma(z) = q * mu(N_ionized) * n(z)
G_sheet = ∫ sigma(z) dz
Rsh = 1 / G_sheet
```

## 2. `src/laser_doping_sim/phase1_thermal.py`

这个文件定义了单层 Si 热模型的核心参数。

### 2.1 `MaterialProperties`

定义位置：

- [phase1_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py#L21)

参数：

- `rho`
  - 物理量：密度，单位 `kg/m^3`
  - 作用：进入热惯性项 `rho * c`
  - 变大后果：温升更慢，更不容易熔化

- `cp_solid`
  - 物理量：固态比热，单位 `J/(kg*K)`
  - 作用：决定固态升温需要多少能量
  - 变大后果：在相同激光输入下温升更慢

- `cp_liquid`
  - 物理量：液态比热，单位 `J/(kg*K)`
  - 作用：决定液态区继续升温的难易
  - 变大后果：熔化后温升更缓

- `k_solid`
  - 物理量：固态导热率，单位 `W/(m*K)`
  - 作用：决定热量向深处扩散的快慢
  - 变大后果：表面峰温通常下降，但热影响区可能更深

- `k_liquid`
  - 物理量：液态导热率，单位 `W/(m*K)`
  - 作用：决定液态区导热能力
  - 变大后果：液态热量更容易向周围传走

- `latent_heat`
  - 物理量：熔化潜热，单位 `J/kg`
  - 作用：相变时需要额外吸收的能量
  - 变大后果：更难熔化，熔深通常变浅

- `melt_temp`
  - 物理量：名义熔点，单位 `K`
  - 作用：定义相变温区中心
  - 变大后果：达到熔化所需温度更高

- `mushy_width`
  - 物理量：固液混合区温宽，单位 `K`
  - 作用：把尖锐相变平滑成一个温区
  - 变大后果：相变更平滑，数值更稳定，但固液界面更“钝”

### 2.2 `LaserPulse`

定义位置：

- [phase1_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py#L33)

参数：

- `fluence`
  - 物理量：单脉冲能量密度，单位 `J/m^2`
  - 作用：控制总注入能量
  - 变大后果：升温更高，更容易熔化

- `pulse_fwhm`
  - 物理量：脉冲半高全宽，单位 `s`
  - 作用：控制高斯脉冲在时间轴上的宽度
  - 原理：高斯时间分布
  - 变小后果：峰值热流更尖、更容易瞬时过热
  - 变大后果：总能量不变时，峰值变低、加热更平缓

- `peak_time`
  - 物理量：脉冲峰值时刻，单位 `s`
  - 作用：把脉冲放在时间窗的什么位置
  - 物理上不是材料常数，更像数值时间窗设置
  - 改它通常不改变总能量，只改变脉冲在计算窗口中的位置

- `absorptivity`
  - 物理量：吸收率，无量纲
  - 作用：决定多少表面入射光真正进入热源
  - 变大后果：温升更高

- `absorption_depth`
  - 物理量：吸收深度，单位 `m`
  - 原理：Beer-Lambert 指数吸收
  - 变小后果：能量更集中于表面
  - 变大后果：能量沉积更深、更分散

### 2.3 `SurfaceSourceLayer`

定义位置：

- [phase1_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py#L42)

参数：

- `kind`
  - 物理意义：source 类型，例如 `PSG`
  - 作用：主要用于元数据和后续扩散解释

- `dopant`
  - 物理意义：source 中的掺杂元素，例如 `P`

- `dopant_concentration_cm3`
  - 物理量：source 中的掺杂浓度，单位 `cm^-3`
  - 在扩散里决定源库存和表面可提供的 P 量
  - 变大后果：更容易得到高注入

- `notes`
  - 说明字段，不直接进入物理求解

### 2.4 `SubstrateDoping`

定义位置：

- [phase1_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py#L50)

参数：

- `species`
  - 衬底背景掺杂种类，例如 `Ga`

- `concentration_cm3`
  - 物理量：背景受主浓度，单位 `cm^-3`
  - 作用：决定结深判定条件和 net donor
  - 变大后果：达到结深所需 donor 更高，结通常更浅

- `notes`
  - 说明字段

### 2.5 `Domain1D`

定义位置：

- [phase1_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py#L57)

参数：

- `thickness`
  - 物理量：计算深度，单位 `m`
  - 变大后果：计算域更深，边界干扰更小，但计算量增加

- `nz`
  - 物理量：深度网格数
  - 变大后果：空间分辨率更高，但计算更慢

- `dt`
  - 物理量：时间步长，单位 `s`
  - 变小后果：时间分辨率更高，但计算更慢

- `t_end`
  - 物理量：仿真结束时刻，单位 `s`
  - 变大后果：能看更长冷却过程和后续扩散过程

- `ambient_temp`
  - 物理量：环境/初始温度，单位 `K`
  - 变大后果：更接近预热基底，达到熔化更容易

- `bottom_bc`
  - 物理意义：底部边界条件
  - `dirichlet`：底部固定温度
  - `neumann`：底部零热流
  - `dirichlet` 通常更保守，`neumann` 更容易保温

## 3. `src/laser_doping_sim/phase2_diffusion.py`

### 3.1 `DiffusionParameters`

定义位置：

- [phase2_diffusion.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py#L27)

参数：

- `boundary_model`
  - 物理意义：表面 source 边界模型
  - `finite_source_cell`：有限库存 source
  - `robin_reservoir`：更理想化的 Robin reservoir
  - 正式主线一般更推荐 `finite_source_cell`

- `source_exchange_mode`
  - 物理意义：source 和 Si 什么时候允许交换
  - `melt_only`：只在表面进入液态后注入
  - `all_states`：固态和液态都允许交换
  - `all_states` 更接近“固态弱注入 + 液态强注入”的连续物理图像

- `solid_diffusivity_m2_s`
  - 物理意义：固态扩散率下限，单位 `m^2/s`
  - 若设为 `0`，固态扩散完全按 Arrhenius 公式算
  - 若设为正数，相当于给固态扩散率一个保底值

- `solid_prefactor_cm2_s`
  - 物理量：固态 Arrhenius 前因子，单位 `cm^2/s`
  - 变大后果：固态扩散更强

- `solid_activation_energy_ev`
  - 物理量：固态扩散激活能，单位 `eV`
  - 变大后果：固态扩散更难发生

- `liquid_prefactor_cm2_s`
  - 物理量：液态 Arrhenius 前因子，单位 `cm^2/s`
  - 变大后果：液态扩散更强

- `liquid_activation_energy_ev`
  - 物理量：液态扩散激活能，单位 `eV`
  - 变大后果：液态扩散更弱

- `interface_liquid_threshold`
  - 物理意义：界面“算熔化”的液相分数阈值
  - 只在 `melt_only` 模式下起门控作用
  - 变大后果：更难打开界面注入

- `source_effective_thickness_m`
  - 物理意义：把 source 折算成面库存时使用的等效厚度
  - 变大后果：相同 source 浓度对应更大库存

- `interfacial_transport_length_m`
  - 物理意义：界面传质长度/界面交换阻力尺度
  - 原理：`h_m ~ D / L_tr`
  - 变大后果：界面注入更慢
  - 变小后果：界面注入更快

- `initial_profile_kind`
  - 初始掺杂轮廓类型
  - `none`：无初始 emitter
  - `erfc_emitter`：解析型发射极
  - `measured`：实验测量 profile

- `initial_profile_csv`
  - measured 初始轮廓文件路径

- `initial_surface_concentration_cm3`
  - 当 `initial_profile_kind=erfc_emitter` 时的表面 P 浓度
  - 变大后果：初始 emitter 更重掺

- `initial_junction_depth_m`
  - 当 `initial_profile_kind=erfc_emitter` 时的初始结深
  - 变大后果：初始 emitter 更深

- `initial_inactive_surface_p_concentration_cm3`
  - 物理意义：初始失活表面 P 层浓度
  - 用来表示表面残余的高浓度但未必活化的 P

- `initial_inactive_surface_thickness_m`
  - 物理意义：初始失活表面 P 层厚度
  - 变大后果：表面 inactive 储量更大

- `texture_interface_area_factor`
  - 物理意义：纹理表面的实际面积 / 投影面积
  - 作用：增强 conformal PSG 覆盖带来的界面交换总量
  - 变大后果：在同样 projected area 下，注入更强

### 3.2 `DiffusionResult`

定义位置：

- [phase2_diffusion.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py#L48)

它主要是输出结构，包含：

- `concentration_p_cm3`
  - 总 P
- `initial_active_p_cm3`
  - 初始 active 轮廓
- `initial_inactive_p_cm3`
  - 初始 inactive 轮廓
- `junction_depth_m`
  - 结深随时间
- `source_inventory_atoms_m2`
  - source 剩余库存
- `surface_injection_flux_atoms_m2_s`
  - 界面注入通量

附加的 `*_origin_*` 字段用于多成分拆分和后处理，不直接改变主求解方程。

## 4. `src/laser_doping_sim/phase3_stack_thermal.py`

### 4.1 `PSGLayerProperties`

定义位置：

- [phase3_stack_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py#L32)

参数：

- `rho`
  - PSG 密度，单位 `kg/m^3`
- `cp`
  - PSG 比热，单位 `J/(kg*K)`
- `k`
  - PSG 导热率，单位 `W/(m*K)`
- `thickness`
  - PSG 厚度，单位 `m`
- `matrix_material`
  - 基体材料标签，默认 `SiO2`
- `dopant_oxide`
  - 掺杂氧化物标签，默认 `P2O5`
- `model_description`
  - 文字说明，不直接参与计算

调参直觉：

- `psg_thickness` 增大：更多光先在 PSG 内传播，也会改变到达 Si 的能量
- `psg_k` 增大：PSG 更容易导热

### 4.2 `StackOpticalProperties`

定义位置：

- [phase3_stack_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py#L45)

参数：

- `surface_reflectance`
  - 顶表面反射率
  - 变大后果：进入堆栈的能量减少

- `texture_reflectance_multiplier`
  - 纹理修正因子
  - 用于把平面反射率修正成纹理表面等效反射率
  - 小于 `1` 往往表示纹理增强吸收

- `interface_transmission`
  - PSG/Si 界面透射率
  - 变大后果：更多能量进入 Si

- `psg_absorption_depth`
  - PSG 吸收深度，单位 `m`
  - 变小后果：PSG 内吸收更强

- `si_absorption_depth`
  - Si 吸收深度，单位 `m`
  - 变大后果：能量在 Si 内沉积得更深

### 4.3 `StackDomain1D`

定义位置：

- [phase3_stack_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py#L54)

参数：

- `silicon_thickness`
  - Si 厚度
- `nz`
  - 全堆栈总网格数
- `dt`
  - 时间步
- `t_end`
  - 终止时间
- `ambient_temp`
  - 初始温度
- `bottom_bc`
  - 底部边界

## 5. `src/laser_doping_sim/phase4_multishot.py`

### 5.1 `MultiShotParameters`

定义位置：

- [phase4_multishot.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase4_multishot.py#L34)

参数：

- `shot_count`
  - 脉冲个数
  - 变大后果：更强的累积效应

- `source_replenishment_mode`
  - 多脉冲间 source 是否补充
  - 物理上对应扫描/重复照射之间前驱体是否恢复

- `thermal_history_mode`
  - 多脉冲热历史如何传递
  - 决定是简单复用单脉冲热史，还是考虑 shot-to-shot 温度延续

- `notes`
  - 说明字段

`MultiShotResult` 主要是多脉冲输出结构，不是输入参数。

## 6. `src/laser_doping_sim/sheet_resistance.py`

### 6.1 `MasettiElectronMobilityModel`

定义位置：

- [sheet_resistance.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/sheet_resistance.py#L10)

这是经验迁移率模型参数集。

参数：

- `temperature_k`
  - 测量温度，默认 `300 K`

- `mu_max_cm2_v_s`
  - 物理意义：低掺杂极限下的高迁移率上限
  - 变大后果：在中低掺杂区，导电率会提高，`Rsh` 倾向下降
- `mu_min1_cm2_v_s`
  - 物理意义：高掺杂极限下的一支最小迁移率项
  - 变大后果：高浓度区迁移率不会掉得那么低，`Rsh` 会偏小
- `mu_min2_cm2_v_s`
  - 物理意义：另一支高掺杂极限最小迁移率项
  - 变大后果：重掺区电导会提高
- `mu_1_cm2_v_s`
  - 物理意义：控制高浓度修正项幅值的经验系数
  - 变大后果：高掺杂区迁移率抑制更强
- `c_r_cm3`
  - 物理意义：从高迁移率平台开始滚降的特征浓度
  - 变大后果：迁移率下降会推迟到更高掺杂才明显发生
- `c_s_cm3`
  - 物理意义：高浓度修正项对应的特征浓度
  - 变大后果：最重掺区的迁移率修正发生位置后移
- `alpha`
  - 物理意义：控制第一段滚降斜率的指数
  - 变大后果：迁移率随掺杂变化的转折更陡
- `beta`
  - 物理意义：控制高浓度修正项斜率的指数
  - 变大后果：超高掺杂区迁移率变化更敏感
- `p_c_cm3`
  - 物理意义：指数预修正项中的参考浓度
  - 当前默认 `0`，表示这一项几乎不额外改变低浓度行为

这些都是 Masetti 模型的经验系数。

物理意义：

- 它们共同决定迁移率如何随离化杂质浓度变化
- 一般不建议在没有文献依据时随意改

如果改动它们，结果主要会体现在：

- `conductivity(z)` 变化
- `Rsh` 变化

但不会改变热学或扩散本身。

## 7. `src/laser_doping_sim/activation_models.py`

这些不是主扩散方程参数，而是 `Rsh` 后处理使用的经验活化模型参数。

### 7.1 `PiecewiseLinearNonactiveActivationModel`

参数：

- `initial_inactive_activation_fraction`
  - 激光前 inactive 的基线活化比例

- `power_w`
  - 功率采样点

- `final_nonactive_activation_fraction`
  - 激光后 non-active pool 的经验活化率曲线
  - 变大后果：同一功率下更多 non-active pool 会被计入 active donor，`Rsh` 更低

### 7.2 `PiecewiseLinearDualChannelActivationModel`

参数：

- `initial_inactive_activation_fraction`
  - 激光前 initial inactive pool 的基线活化比例
- `power_w`
  - 功率采样点
- `final_inactive_activation_fraction`
  - 激光后“再分布的初始 inactive 组分”的活化率曲线
- `final_injected_activation_fraction`
  - 激光后“新注入 P 组分”的活化率曲线

物理思想：

- 把“初始 inactive 再激活”和“新注入 P 的活化”分成两条独立通道

### 7.3 `PiecewiseMultiShotDualChannelActivationModel`

参数：

- `inactive_shot1_fraction`
  - 第 1 个 shot 后，inactive 通道的活化率
- `inactive_inf_fraction`
  - shot 数很多时，inactive 通道趋近的饱和值
- `inactive_n0_shots`
  - inactive 通道接近饱和值的特征 shot 数
- `injected_shot1_fraction`
  - 第 1 个 shot 后，injected 通道的活化率
- `injected_inf_fraction`
  - shot 数很多时，injected 通道趋近的饱和值
- `injected_reference_dose_cm2`
  - 参考注入剂量，用来标定 injected 通道的剂量尺度
- `injected_q0_cm2`
  - injected 通道随剂量演化的特征剂量

物理意义：

- 描述多脉冲下活化率如何随 shot 数和累积剂量演化

这部分更偏经验电学校准，不建议作为第一批需要调的参数。

## 8. `src/laser_doping_sim/measured_profiles.py`

### 8.1 `MeasuredInitialProfile`

参数：

- `depth_nm`
  - 深度坐标，单位 `nm`
- `total_p_cm3`
  - 总磷浓度
  - 通常更接近 `SIMS` 意义上的化学总量
- `active_p_cm3`
  - electrically active phosphorus
  - 通常更接近 `ECV` 或电学可见 donor 的口径
- `inactive_p_cm3`
  - inactive phosphorus
  - 在当前 measured 构造里，通常由 `max(total - active, 0)` 得到

它是数据结构，不是 PDE 自由参数。

## 9. `run_phase1.py` 参数说明

这是单层热学启动脚本。

### 9.1 激光参数

- `--fluence-j-cm2`
  - 单脉冲 fluence
  - 增大后通常更容易熔化

- `--pulse-fwhm-ns`
  - 时间脉宽
  - 变小后峰值热流更大

- `--peak-time-ns`
  - 脉冲峰值时刻
  - 主要影响时间窗排布

- `--absorption-depth-nm`
  - 单层 Si 吸收深度
  - 变小后更表面加热

- `--absorptivity`
  - 吸收率
  - 变大后升温更高

### 9.2 热学网格与边界

- `--thickness-um`
  - 1D 计算深度
  - 太小会让底部边界影响结果，太大则增加计算量
- `--nz`
  - 深度网格点数
  - 增大后空间分辨率更高
- `--dt-ns`
  - 时间步长
  - 变小后时间分辨率更高，但计算更慢
- `--t-end-ns`
  - 总模拟时间
  - 变大后更适合看冷却尾段
- `--ambient-temp-k`
  - 初始/环境温度
  - 提高后更容易熔化
- `--bottom-bc`
  - 底部边界条件
  - `dirichlet` 更像强散热，`neumann` 更像绝热

### 9.3 相变参数

- `--melt-temp-k`
  - 名义熔点
  - 提高后更难达到熔化
- `--mushy-width-k`
  - 固液混合层温宽
  - 增大后相变更平滑，界面更钝

### 9.4 source / substrate 元数据

- `--source-kind`
  - source 名称标签，例如 `PSG`
- `--source-dopant`
  - source 中的掺杂元素名称，例如 `P`
- `--source-dopant-concentration-cm3`
  - source 浓度元数据
  - 在 `Phase 1` 里不改热场，只为后续阶段记录
- `--source-notes`
  - source 说明文字
- `--substrate-dopant`
  - 衬底背景掺杂元素标签
- `--substrate-dopant-concentration-cm3`
  - 衬底背景浓度元数据
- `--substrate-notes`
  - 衬底说明文字

## 10. `run_phase2.py` 参数说明

它继承了 `run_phase1.py` 的热学参数，再加扩散参数。

新增扩散相关参数：

- `--boundary-model`
  - 选表面边界类型

- `--source-exchange-mode`
  - 选 `melt_only` 还是 `all_states`

- `--solid-diffusivity-m2-s`
  - 固态扩散率下限

- `--solid-prefactor-cm2-s`
  - 固态 Arrhenius 前因子
- `--solid-activation-energy-ev`
  - 固态扩散激活能
- `--liquid-prefactor-cm2-s`
  - 液态 Arrhenius 前因子
- `--liquid-activation-energy-ev`
  - 液态扩散激活能

- `--interface-liquid-threshold`
  - `melt_only` 模式下的界面液相判据

- `--source-effective-thickness-nm`
  - source 库存等效厚度

- `--interfacial-transport-length-nm`
  - 界面传质长度

- `--initial-profile-kind`
  - `none` 或 `erfc_emitter`

- `--initial-surface-p-concentration-cm3`
  - 初始发射极表面浓度

- `--initial-junction-depth-nm`
  - 初始发射极结深

- `--initial-inactive-surface-p-concentration-cm3`
  - 初始失活表面层浓度

- `--initial-inactive-surface-thickness-nm`
  - 初始失活表面层厚度

调参规律：

- 想让“原有 emitter 在不熔情况下也继续动”，重点看固态扩散参数
- 想让“PSG 注入更强”，重点看 `source_effective_thickness`、`interfacial_transport_length`、`source_exchange_mode`

## 11. `run_phase3.py` 参数说明

这是最重要的主脚本。

### 11.1 设备与光斑参数

- `--average-power-w`
  - 平均功率
  - 增大后单脉冲能量随之增大

- `--repetition-rate-hz`
  - 重复频率
  - 在平均功率固定下，增大它会让单脉冲能量变小

- `--spot-shape`
  - `square_flat_top` 或 `circular_flat_top`

- `--square-side-um`
  - 方形 flat-top 边长
  - 变大后 spot area 增大、fluence 下降

- `--spot-diameter-um`
  - 圆形 flat-top 直径

- `--fluence-j-cm2`
  - 若手动指定，会覆盖由功率和光斑面积推导的 fluence

### 11.2 时间脉冲参数

- `--pulse-fwhm-ns`
  - 时间脉宽
  - 变小会让峰值热流更尖
- `--peak-time-ns`
  - 脉冲峰值落在时间轴上的位置
  - 主要影响时间窗排布

### 11.3 光学参数

- `--surface-reflectance`
  - 顶表面反射率
  - 增大后进入样品的能量减少，温升和熔深通常下降

- `--texture-reflectance-multiplier`
  - 纹理反射修正
  - 小于 `1` 往往表示更强的 trapping

- `--interface-transmission`
  - PSG/Si 界面透射率
  - 增大后更多能量进入 Si

- `--psg-absorption-depth-um`
  - PSG 吸收深度
  - 变小后 PSG 内部吸收增强

- `--si-absorption-depth-nm`
  - Si 吸收深度
  - 变大后热沉积更深，表面峰值可能下降但热影响区加深

### 11.4 PSG 层物性

- `--psg-thickness-nm`
  - PSG 厚度
  - 增大后会改变 PSG 吸收与到达 Si 的能量分配
- `--psg-rho`
  - PSG 密度
- `--psg-cp`
  - PSG 比热
- `--psg-k`
  - PSG 导热率

### 11.5 Si 热学与网格参数

- `--si-thickness-um`
  - Si 子域厚度
- `--nz`
  - 双层模型总网格点数
- `--dt-ns`
  - 时间步长
- `--t-end-ns`
  - 总模拟时间
- `--ambient-temp-k`
  - 初始温度
- `--melt-temp-k`
  - Si 名义熔点
- `--mushy-width-k`
  - Si 固液混合层温宽
- `--bottom-bc`
  - 底部边界条件

### 11.6 source / substrate 参数

- `--source-kind`
  - source 标签
- `--source-dopant`
  - source 掺杂元素标签
- `--source-dopant-concentration-cm3`
  - source 浓度
  - 增大后可提供更高注入上限
- `--source-notes`
  - source 描述文字
- `--substrate-dopant`
  - 衬底背景掺杂种类
- `--substrate-dopant-concentration-cm3`
  - 衬底背景浓度
  - 增大后结深判据更严格
- `--substrate-notes`
  - 衬底描述文字

### 11.7 扩散参数

- `--boundary-model`
  - 选有限 source cell 或 Robin reservoir
- `--source-exchange-mode`
  - 选仅熔化注入还是固液全状态交换
- `--solid-diffusivity-m2-s`
  - 固态扩散率保底值
- `--solid-prefactor-cm2-s`
  - 固态 Arrhenius 前因子
- `--solid-activation-energy-ev`
  - 固态扩散激活能
- `--liquid-prefactor-cm2-s`
  - 液态 Arrhenius 前因子
- `--liquid-activation-energy-ev`
  - 液态扩散激活能
- `--interface-liquid-threshold`
  - `melt_only` 模式下界面打开的液相阈值
- `--source-effective-thickness-nm`
  - source 等效厚度
- `--interfacial-transport-length-nm`
  - 界面传质长度

### 11.8 初始掺杂参数

- `--initial-profile-kind`
  - `none`、`erfc_emitter`、`measured`

- `--initial-profile-csv`
  - measured 初始轮廓路径

- `--initial-surface-p-concentration-cm3`
  - `erfc emitter` 模式下的表面浓度
- `--initial-junction-depth-nm`
  - `erfc emitter` 模式下的初始结深

- `--initial-inactive-surface-p-concentration-cm3`
  - 初始 inactive 表面层浓度
- `--initial-inactive-surface-thickness-nm`
  - 初始 inactive 表面层厚度

### 11.9 纹理参数

- `--texture-interface-area-factor`
  - 直接给 actual/projected 面积比
  - 增大后 PSG 到 Si 的总交换面积更大，注入更强

- `--texture-pyramid-sidewall-angle-deg`
  - 如果不直接给面积因子，就按 `sec(angle)` 估算
  - 角度越大，估算出的界面面积因子越大

- `--texture-notes`
  - 说明字段

调参直觉：

- 想提高峰温：增大 `average_power_w`，减小 `surface_reflectance`
- 想让能量更深沉积：增大 `si_absorption_depth_nm`
- 想增强注入：增大 `source_dopant_concentration_cm3`，减小 `interfacial_transport_length_nm`
- 想增强纹理带来的界面供源能力：增大 `texture_interface_area_factor`

## 12. `run_phase3_power_scan.py` 参数说明

它和 `run_phase3.py` 基本相同，但额外有功率扫描参数：

- `--power-start-w`
  - 起始功率

- `--power-stop-w`
  - 结束功率

- `--power-step-w`
  - 步长

这三个参数只改变扫描区间，不改变单个 case 的物理方程。

注意这份脚本默认值更偏“研究线”：

- `nz = 1200`
- `t_end_ns = 400`
- `initial_profile_kind = erfc_emitter`
- `initial_surface_p_concentration_cm3 = 3.5e20`
- `initial_junction_depth_nm = 300`
- `initial_inactive_surface_p_concentration_cm3 = 5.0e20`
- `initial_inactive_surface_thickness_nm = 30`

所以它更适合系统扫功率，而不是拿来当最简 demo。

## 13. `prepare_measured_initial_profile.py` 参数说明

- `--ecv-csv`
  - ECV 原始文件路径
  - 决定 active profile 的主要输入来源

- `--sims-xlsx`
  - SIMS 原始文件路径
  - 决定 total profile 的主要输入来源

- `--sims-location`
  - 在 xlsx 中选哪一个测点/位置
  - 改它会切换到另一条 measured profile

- `--output-csv`
  - 输出统一 measured profile
  - 这是后续 `--initial-profile-kind measured` 最常用的输入文件

- `--output-plot`
  - 输出预览图
  - 用来快速检查 total / active / inactive 拆分是否合理

- `--output-summary`
  - 输出摘要 json
  - 便于记录本次构造 profile 时使用了哪组输入

物理上这一步不是求解，而是把实验 profile 变成统一输入。

## 14. `run_sheet_resistance_cases.py` 参数说明

这是 `Rsh` 后处理脚本。

- `--case-dirs`
  - 要处理的 case 目录
  - 可以一次处理多个功率 case

- `--output-dir`
  - 输出目录
  - 会写出 `Rsh` 汇总表和柱状图

- `--inactive-activation-fraction`
  - 激光前 initial inactive 的活化比例
  - 增大后 `Rsh_init` 会下降

- `--final-inactive-activation-fraction`
  - 激光后 redistributed inactive 的活化比例
  - 增大后会降低激光后的 `Rsh`

- `--injected-activation-fraction`
  - 激光后 injected P 的活化比例
  - 增大后 injected dose 对 `Rsh` 的贡献更强

- `--measurement-temperature-k`
  - 迁移率模型测量温度
  - 改它会通过迁移率模型改变 `Rsh`

- `--activation-model`
  - `fixed_fractions`
  - `piecewise_nonactive_pool`
  - `piecewise_dual_channel`
  - 用于选择固定活化假设，还是按功率变化的经验活化曲线

- `--activation-table-csv`
  - 分段经验活化曲线文件
  - 只在分段 activation 模式下使用

物理上最重要的一点：

- 这一步不是主 PDE 的一部分
- 它是在“总 P 已经求出来以后”，再用经验 fraction 把其中一部分解释成 electrically active donor

## 15. 高级校准脚本参数

这些脚本偏研究用途，不是新手第一轮必须用的。

### 15.1 `run_dual_channel_activation_calibration.py`

主要参数：

- `--case-dirs`
  - 参与标定的 case 目录列表
- `--measured-rsh-csv`
  - 实测 `Rsh` 数据表
- `--output-dir`
  - 标定结果输出目录
- `--measurement-temperature-k`
  - 电学后处理温度
- `--injection-threshold-cm2`
  - 低于此 injected dose 的 case 被视为“主要由 inactive 再激活主导”
- `--target-initial-rsh-ohm-per-sq`
  - 初始片阻标定目标

### 15.2 `run_dual_channel_high_power_refit.py`

主要参数：

- `--case-dirs`
  - 高功率 refit 使用的 case
- `--measured-rsh-csv`
  - 实测高功率 `Rsh` 表
- `--base-activation-csv`
  - 低功率段已标定好的 activation 曲线
- `--initial-inactive-activation-fraction`
  - 加载基础 activation 表时使用的初始 inactive 基线活化率
- `--boundary-power-w`
  - 低功率曲线固定到哪个功率点为止
- `--output-dir`
  - refit 输出目录
- `--measurement-temperature-k`
  - 电学后处理温度

### 15.3 `run_dual_channel_monotonic_segment_refit.py`

主要参数：

- `--case-dirs`
  - 分段 refit 使用的 case
- `--measured-rsh-csv`
  - 实测 `Rsh` 数据
- `--base-activation-csv`
  - 低功率基础 activation 表
- `--initial-inactive-activation-fraction`
  - 基础表加载时使用的初始 inactive 活化率
- `--measurement-temperature-k`
  - 电学后处理温度
- `--output-dir`
  - 输出目录

这类脚本的作用不是改热学/扩散，而是校准高功率区的经验活化读法。

### 15.4 `run_phase3_physics_validation.py`

这是功率扫描结果的物理一致性检查脚本。

主要参数：

- `--scan-dir`
  - 主功率扫描目录

- `--fine-scan-dir`
  - 细化功率扫描目录

- `--output-dir`
  - 验证结果输出目录

- `--depths-nm`
  - 在哪些深度抽样最终 P profile

- `--near-surface-window-nm`
  - 用于近表面积分剂量和质心检查的表层窗口厚度

这一步不重新解 PDE，而是检查已有扫描结果是否满足一些基本物理趋势，例如：

- 功率增大时温度是否整体上升
- 结深、熔深是否大体合理
- 近表面剂量和 profile 质心是否出现异常跳变
- 质量守恒误差是否可接受

## 16. 如果只想知道“改这个参数会怎样”，优先记这张表

- `average_power_w` 增大
  - 单脉冲能量增大
  - 峰温上升
  - 更容易熔化
  - 更可能增强注入和结深

- `pulse_fwhm_ns` 减小
  - 峰值热流增大
  - 更容易瞬时熔化

- `surface_reflectance` 增大
  - 进入样品的能量减少
  - 温度、熔深、扩散通常都下降

- `si_absorption_depth_nm` 增大
  - 热沉积更深
  - 表面温峰可能下降，但热影响深度可能加深

- `source_dopant_concentration_cm3` 增大
  - source 更富 P
  - 注入上限提高

- `interfacial_transport_length_nm` 增大
  - 界面交换变慢
  - 注入减弱

- `solid_activation_energy_ev` 增大
  - 固态扩散减弱
  - 低功率区更难出现明显扩散

- `liquid_prefactor_cm2_s` 增大
  - 液态扩散增强
  - 熔化区掺杂更容易深入

- `initial_surface_p_concentration_cm3` 增大
  - 初始 emitter 更重掺
  - 即使后续注入弱，最终 profile 也可能仍较深

- `initial_inactive_surface_p_concentration_cm3` 增大
  - 表面 inactive 储量增大
  - 对后续 `Rsh` 读法会更敏感

- `inactive_activation_fraction / injected_activation_fraction` 增大
  - `Rsh` 会降低
  - 但这属于电学后处理，不代表总 P 真的变多

## 17. 建议的调参顺序

如果你要做物理拟合，建议顺序是：

1. 先定设备输入
   - `average_power_w`
   - `repetition_rate_hz`
   - `spot size`
   - `pulse_fwhm_ns`

2. 再定光学
   - `surface_reflectance`
   - `interface_transmission`
   - `psg_absorption_depth`
   - `si_absorption_depth`

3. 再定热学
   - `melt_temp`
   - `mushy_width`
   - `psg` / `si` 热物性

4. 再定扩散
   - `solid/liquid diffusivity`
   - `source_effective_thickness`
   - `interfacial_transport_length`

5. 最后才用 `Rsh` 活化参数做电学校准

如果把这个顺序反过来，很容易出现：

- 先用经验活化把 `Rsh` 拟合好了
- 但热学和扩散本体其实还不对

这时物理解释会混乱。
