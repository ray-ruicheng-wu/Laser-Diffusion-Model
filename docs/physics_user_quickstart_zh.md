# 物理用户快速上手教程

这份教程是给“懂物理、但不一定熟悉 Python 项目结构”的用户准备的。

它回答三个问题：

1. 这个项目到底在算什么
2. 我应该按什么顺序运行
3. 跑完以后应该看哪些结果文件

## 1. 这套代码在做什么

当前代码把激光掺杂问题拆成四层：

1. 热学
   - 激光把 `Si` 或 `PSG/Si` 结构加热
   - 输出温度场 `T(z,t)` 和液相分数 `f_l(z,t)`
2. 扩散
   - 用热历史驱动磷在硅中的扩散
   - 输出总磷浓度分布 `C_P(z,t)`
3. 电学后处理
   - 把总磷分成 active / inactive / injected 组件
   - 估算 `Rsh`
4. 多脉冲扩展
   - 在单脉冲结果基础上研究重复脉冲累积

最核心的物理链条是：

```text
激光输入 -> 温度场 -> 液相分数 -> 有效扩散系数 -> 磷浓度分布 -> 结深 / Rsh
```

## 2. 运行前准备

### 2.1 Python 环境

建议使用 `Python 3.11+`。

安装依赖：

```powershell
pip install -r requirements.txt
```

### 2.2 项目里最重要的目录

- [src/laser_doping_sim](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim)
  - 核心求解器和物理模型
- [inputs](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs)
  - 输入文件、测量 profile、经验活化表
- [outputs](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs)
  - 每次运行后的结果
- [run_phase1.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase1.py)
  - 单层热学入口
- [run_phase2.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase2.py)
  - 单层热学 + 扩散入口
- [run_phase3.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3.py)
  - `PSG/Si` 热学 + 扩散主入口
- [run_phase3_power_scan.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3_power_scan.py)
  - 功率扫描入口
- [run_sheet_resistance_cases.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_sheet_resistance_cases.py)
  - `Rsh` 后处理入口
- [run_phase4_multishot.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase4_multishot.py)
  - 多脉冲化学 / 热历史入口
- [run_build_multishot_activation_bootstrap.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_build_multishot_activation_bootstrap.py)
  - 多脉冲活化 bootstrap 表生成入口
- [run_phase4_multishot_sheet_resistance.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase4_multishot_sheet_resistance.py)
  - 多脉冲 `Rsh` 后处理入口

## 3. 推荐的完整测试顺序

如果你第一次接触这套代码，最推荐的顺序是：

1. 先跑 `Phase 1`，确认热模型正常
2. 再跑 `Phase 2`，确认单层扩散正常
3. 再跑 `Phase 3`，进入正式 `PSG/Si` 模型
4. 如果有多组功率，跑 `power scan`
5. 最后用 `Rsh` 后处理与实验对照
6. 如果关心 shot-to-shot 累积，再进入 `Phase 4`

下面按这个顺序给出“最小完整测试”。

## 4. 第一步：跑单层热学基线

命令：

```powershell
python .\run_phase1.py
```

这一步在物理上做的是：

- 把激光脉冲当作一个随时间变化、沿深度指数吸收的体热源
- 解 1D 热传导方程
- 用表观热容法处理相变

跑完以后，默认结果在：

- [outputs/phase1/default_run](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase1/default_run)

最值得先看的文件：

- `summary.json`
- `surface_temperature_vs_time.png`
- `melt_depth_vs_time.png`
- `temperature_heatmap.png`
- `liquid_fraction_heatmap.png`

你应该重点检查：

1. 峰值表面温度是否合理
2. 是否出现熔化
3. 熔化窗口持续多久
4. 熔深量级是否和经验相符

## 5. 第二步：跑单层热学驱动的扩散

命令：

```powershell
python .\run_phase2.py
```

这一步在物理上做的是：

- 先调用 `Phase 1` 生成热历史
- 再用温度场与液相分数构造 `D_eff(T, f_l)`
- 解 1D 磷扩散方程

结果目录：

- [outputs/phase2/default_run](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase2/default_run)

最值得先看的文件：

- `summary.json`
- `final_p_profile.png`
- `junction_depth_vs_time.png`
- `source_inventory_vs_time.png`
- `p_concentration_heatmap.png`

你应该重点检查：

1. 最终峰值 P 浓度
2. 最终结深和最大结深
3. source 是否被过快耗尽
4. 质量守恒误差是否足够小

## 6. 第三步：跑正式的 PSG/Si 双层模型

命令：

```powershell
python .\run_phase3.py
```

这是当前最重要的主入口。

它在物理上做的是：

1. 用 `PSG/Si` 双层光学-热学模型计算吸收和温度
2. 把热历史裁成 Si 子域
3. 用该热历史重新驱动磷扩散
4. 输出热学和扩散两套结果

默认输出目录：

- [outputs/phase3/default_run](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/default_run)

里面会分成两个子目录：

- `thermal/`
- `diffusion/`

你应该优先看：

- [summary.json](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/default_run/summary.json)
- [thermal/summary.json](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/default_run/thermal/summary.json)
- [diffusion/summary.json](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/default_run/diffusion/summary.json)

`Phase 3` 最重要的意义是：

- 把 `PSG` 层显式纳入热学模型
- 用实测 `500 kHz`、`95 um flat-top` 光斑面积来换算 fluence
- 用 `surface_reflectance / interface_transmission / absorption_depth` 处理双层吸收

## 7. 第四步：跑一组功率扫描

如果你不只关心单个功率，而是想看阈值、熔深趋势和结深趋势，运行：

```powershell
python .\run_phase3_power_scan.py
```

默认会扫一段功率区间，并在每个功率下重复：

- `Phase 3 thermal`
- `Phase 2 diffusion`

输出目录默认在：

- [outputs/phase3/power_scan_60_90w](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_90w)

这一步最适合用来回答：

- 多少功率开始熔化
- 熔深如何随功率变化
- 结深如何随功率变化
- 高功率下是否出现强注入

## 8. 第五步：用实验 profile 做 measured 初始条件

如果你已经有 `ECV` 和 `SIMS` 原始文件，先运行：

```powershell
python .\prepare_measured_initial_profile.py
```

默认输入：

- [inputs/raw_measurements/CTV-ECV-RAW.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/raw_measurements/CTV-ECV-RAW.csv)
- [inputs/raw_measurements/CTV-SIMS-RAW.xlsx](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/raw_measurements/CTV-SIMS-RAW.xlsx)

默认输出：

- [inputs/measured_profiles/ctv_measured_initial_profile.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/measured_profiles/ctv_measured_initial_profile.csv)
- [inputs/measured_profiles/ctv_measured_initial_profile.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/measured_profiles/ctv_measured_initial_profile.png)

然后在 `Phase 3` 里这样用：

```powershell
python .\run_phase3.py `
  --initial-profile-kind measured `
  --initial-profile-csv inputs/measured_profiles/ctv_measured_initial_profile.csv
```

这样模型的初始掺杂分布就不再是理想化的 `erfc emitter`，而直接来自实验 profile。

## 9. 第六步：计算片电阻 Rsh

跑完一组 `Phase 3` case 以后，可以做 `Rsh` 后处理。

例子：

```powershell
python .\run_sheet_resistance_cases.py `
  --case-dirs outputs/phase3/default_run `
  --output-dir outputs/phase3/sheet_resistance_default
```

这一步不会重跑主热学模型，而是：

1. 读取已有 case
2. 重新拆分 active / inactive / injected 贡献
3. 用活化分数假设构造 electrically active donor
4. 用 Masetti 迁移率模型计算 `Rsh`

适合回答：

- 当前总 P 中有多少应算 active donor
- 在某个活化假设下，四探针片阻大概是多少

## 10. 一套推荐的“完整主线测试”

如果你想用一组参数把“热学 -> 扩散 -> Rsh”完整跑一遍，我建议按下面做。

### 10.1 先准备 measured profile

```powershell
python .\prepare_measured_initial_profile.py
```

### 10.2 跑一个 measured 初始条件的 Phase 3 case

```powershell
python .\run_phase3.py `
  --output-dir outputs/phase3/tutorial_measured_case `
  --average-power-w 60 `
  --repetition-rate-hz 500000 `
  --square-side-um 95 `
  --pulse-fwhm-ns 10 `
  --surface-reflectance 0.09 `
  --interface-transmission 0.68 `
  --psg-absorption-depth-um 50 `
  --si-absorption-depth-nm 1274 `
  --initial-profile-kind measured `
  --initial-profile-csv inputs/measured_profiles/ctv_measured_initial_profile.csv `
  --boundary-model finite_source_cell `
  --source-exchange-mode all_states
```

### 10.3 再做 Rsh 后处理

```powershell
python .\run_sheet_resistance_cases.py `
  --case-dirs outputs/phase3/tutorial_measured_case `
  --output-dir outputs/phase3/tutorial_measured_case_rsh `
  --inactive-activation-fraction 0.05 `
  --final-inactive-activation-fraction 0.05 `
  --injected-activation-fraction 1.0
```

### 10.4 你最终要读哪些量

在热学部分读：

- 峰值表面温度
- 最大液相分数
- 最大熔深
- 熔化窗口

在扩散部分读：

- 最终峰值 P 浓度
- 最终结深
- 累积注入剂量
- source 耗尽比例

在 `Rsh` 部分读：

- `Rsh init`
- `Rsh af`
- active / inactive / injected 的拆分是否合理

## 11. 可选扩展：跑一组 Phase 4 多脉冲 case

如果你想把同一套流程继续扩展到重复脉冲，推荐先跑这样一组：

```powershell
python .\run_phase4_multishot.py `
  --output-dir outputs/phase4/tutorial_multishot_case `
  --average-power-w 60 `
  --shots 10 `
  --thermal-history-mode accumulate `
  --cycle-end-ns 2000 `
  --dt-ns 0.05 `
  --nz 300 `
  --profile-shots 1 2 5 10 `
  --fast-output
```

其中：

- `reuse_single_pulse` 适合更快的 chemistry-only 多脉冲近似
- `accumulate` 适合看真实的 shot-to-shot 热历史延续
- `--fast-output` 适合长计算，只保留 `csv/json/npz`

这一步最先读：

- `multishot/multishot_summary.csv`
- `multishot/summary.json`
- 根目录 `summary.json`

重点量：

- `shot_injected_dose_cm2`
- `cumulative_injected_dose_cm2`
- `final_junction_depth_nm`
- `remaining_source_inventory_atoms_m2`
- `peak_silicon_surface_temperature_k`
- `cycle_end_silicon_surface_temperature_k`

## 12. 可选扩展：做多脉冲 `Rsh` 后处理

如果你已经有多脉冲活化参数表，可以运行：

```powershell
python .\run_phase4_multishot_sheet_resistance.py `
  --phase4-dir outputs/phase4/tutorial_multishot_case `
  --activation-parameter-csv outputs/phase4/multishot_activation_bootstrap_scan_60w_1to10/multishot_dual_channel_params.csv `
  --output-dir outputs/phase4/tutorial_multishot_case/multishot_rsh
```

最先读：

- `multishot_sheet_resistance_summary.csv`
- `expanded_multishot_activation_table.csv`

重点看：

- `eta_inactive`
- `eta_injected`
- `rsh_after_ohm_per_sq`
- `Rsh` 和活化率是否随 shot 数单调演化
## 13. 最常见的调参方向

如果你发现“完全不熔”，优先检查：

- `average_power_w`
- `pulse_fwhm_ns`
- `surface_reflectance`
- `si_absorption_depth_nm`
- `fluence_j_cm2`

如果你发现“熔了但结深很浅”，优先检查：

- `source_dopant_concentration_cm3`
- `source_effective_thickness_nm`
- `interfacial_transport_length_nm`
- `source_exchange_mode`
- `liquid_prefactor_cm2_s`

如果你发现“总 P 很高但 Rsh 不降”，优先检查：

- `inactive_activation_fraction`
- `final_inactive_activation_fraction`
- `injected_activation_fraction`
- measured profile 的 active / inactive 拆分

## 14. 新用户最容易犯的错误

1. 把 `Phase 1` 的单层吸收参数直接当成 `Phase 3 PSG/Si` 的正式光学参数
2. 混淆“总 P”和“electrically active donor”
3. 看到 `final_net_donor_upper_bound` 就把它当真实 active donor
4. 用 `Rsh` 后处理参数去反推主扩散模型已经显式包含了电活化
5. 不先看 `summary.json` 就直接凭图像印象判断结果

## 15. 接下来该看哪份文档

如果你已经能跑通流程，下一步建议看：

- [physics_parameter_manual_zh.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/physics_parameter_manual_zh.md)

那份手册会把：

- `src` 里的每个参数是什么
- 每个参数对应的物理量是什么
- 为什么它会影响结果
- `run_*.py` 里的参数改大或改小分别意味着什么

系统地整理出来。
