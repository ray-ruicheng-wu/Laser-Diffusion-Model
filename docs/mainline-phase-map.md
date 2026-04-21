# Mainline Phase Map

这份文档专门回答一个问题：

`main` 工作区里每个 phase 到底在做什么，应该看哪些脚本、模块、输出和说明文档。

如果你想快速接手这个项目，最推荐先读这份，再去读总教程和参数手册。

如果你更喜欢直接在文件树里按 phase 找东西，也可以先打开：

- `docs/phases/README.md`

## 总体结构

当前主线可以按下面 5 个阶段来理解：

1. `Phase 0`
   数据准备与电学校准输入
2. `Phase 1`
   单层 Si 热学基线
3. `Phase 2`
   单脉冲热驱动总磷扩散
4. `Phase 3`
   `PSG/Si` 双层单脉冲主线与实验对标
5. `Phase 4`
   多脉冲 thermal-history 与 multi-shot 电学扩展

下面按 phase 分别说明。

## Phase 0

### Title

`数据准备与电学校准输入`

### 这一步做什么

这一步不直接求解热学或扩散，而是把实验原始数据整理成主线模型可以读取的输入，并准备后续 `Rsh` 标定所需的经验参数表。

它解决的是：

- `SIMS + ECV` 怎么变成可直接插值的初始 `P profile`
- 单脉冲和多脉冲的活化经验参数表从哪里来
- measured 输入应该放在工作区的哪个位置

### 主要脚本

- `prepare_measured_initial_profile.py`
- `run_dual_channel_activation_calibration.py`
- `run_dual_channel_high_power_refit.py`
- `run_dual_channel_monotonic_segment_refit.py`
- `run_sheet_resistance_cases.py`

### 主要模块

- `src/laser_doping_sim/measured_profiles.py`
- `src/laser_doping_sim/activation_models.py`
- `src/laser_doping_sim/sheet_resistance.py`

### 典型输入 / 输出

- 输入：
  - `inputs/raw_measurements/`
  - `inputs/raw_measurements/CTV-ECV-RAW.csv`
  - `inputs/raw_measurements/CTV-SIMS-RAW.xlsx`
- 输出：
  - `inputs/measured_profiles/ctv_measured_initial_profile.csv`
  - `inputs/measured_profiles/ctv_measured_initial_profile_summary.json`
  - `outputs/phase3/.../dual_channel_activation_model.csv`
  - `outputs/phase4/.../multishot_dual_channel_params.csv`

### 主要文档

- `docs/phases/phase0_data_and_calibration/dual-channel-activation-method.md`
- `docs/modeling_tutorial_for_materials_undergrads.md`
- `docs/python_code_teaching_for_beginners.md`

## Phase 1

### Title

`单层 Si 热学基线`

### 这一步做什么

只算热，不算掺杂。

这一阶段的任务是确认：

- 激光输入如何转成深度方向热源
- `T(z,t)` 是否合理
- 相变窗口和熔深是否合理

这是整个项目最基础的热历史来源。

### 主要脚本

- `run_phase1.py`

### 主要模块

- `src/laser_doping_sim/phase1_thermal.py`

### 典型输出

- `outputs/phase1/default_run/summary.json`
- `outputs/phase1/default_run/temperature_heatmap.png`
- `outputs/phase1/default_run/liquid_fraction_heatmap.png`
- `outputs/phase1/default_run/melt_depth_vs_time.png`

### 主要文档

- `docs/phases/phase1_single_layer_thermal/phase1-analysis.md`
- `docs/phases/phase1_single_layer_thermal/phase1-code-explained.md`

## Phase 2

### Title

`单脉冲热驱动总磷扩散`

### 这一步做什么

在 `Phase 1` 的热历史上加入 `P` 的扩散和表面 source exchange。

这一阶段的重点是：

- 用 `T(z,t)` 与液相分数构造有效扩散系数
- 把表面 source 写成有限库存边界
- 输出第一次可用的 `P profile` 和结深

### 主要脚本

- `run_phase2.py`

### 主要模块

- `src/laser_doping_sim/phase2_diffusion.py`
- `src/laser_doping_sim/phase1_thermal.py`

### 典型输出

- `outputs/phase2/default_run/final_p_profile.png`
- `outputs/phase2/default_run/junction_depth_vs_time.png`
- `outputs/phase2/default_run/source_inventory_vs_time.png`
- `outputs/phase2/default_run/p_concentration_heatmap.png`

### 主要文档

- `docs/phases/phase2_single_shot_diffusion/phase2-analysis.md`
- `docs/phases/phase2_single_shot_diffusion/phase2-code-explained.md`
- `docs/phases/phase2_single_shot_diffusion/boundary-condition-review.md`

## Phase 3

### Title

`PSG/Si 双层单脉冲主线与实验对标`

### 这一步做什么

这一步把项目从“演示级单层模型”推进到“当前单脉冲主线”。

主要新增的是：

- `PSG/Si` 双层热学
- `532 nm`、`95 um flat-top`、`9%` 反射率等工艺条件
- measured initial profile
- 功率扫描
- 物理验证
- 单脉冲 `Rsh` 对照

可以把这一阶段理解为：

`当前单脉冲主线最核心的一层`

### 主要脚本

- `run_phase3.py`
- `run_phase3_power_scan.py`
- `run_phase3_physics_validation.py`
- `run_sheet_resistance_cases.py`

### 主要模块

- `src/laser_doping_sim/phase3_stack_thermal.py`
- `src/laser_doping_sim/phase2_diffusion.py`
- `src/laser_doping_sim/measured_profiles.py`
- `src/laser_doping_sim/activation_models.py`
- `src/laser_doping_sim/sheet_resistance.py`

### 典型输出

- `outputs/phase3/default_run/thermal/`
- `outputs/phase3/default_run/diffusion/`
- `outputs/phase3/power_scan_.../`
- `outputs/phase3/sheet_resistance_.../`
- `outputs/phase3/dual_channel_activation_.../`

### 主要文档

- `docs/phases/phase3_psg_si_single_shot_mainline/phase3-analysis.md`
- `docs/phases/phase3_psg_si_single_shot_mainline/phase3-code-explained.md`
- `docs/phases/phase3_psg_si_single_shot_mainline/phase3-physics-validation.md`
- `docs/phases/phase3_psg_si_single_shot_mainline/phase3-physics-validation-work-report.md`
- `docs/phases/phase0_data_and_calibration/dual-channel-activation-method.md`

## Phase 4

### Title

`多脉冲 thermal-history 与 multi-shot 电学扩展`

### 这一步做什么

这一步把单脉冲主线扩展到 repeated shots。

当前主线里已经支持两条多脉冲路径：

- `reuse_single_pulse`
  - 每个 shot 复用同一条单脉冲热历史
- `accumulate`
  - 每个 shot 重新求解热循环，并把 cycle-end 温度场传给下一个 shot

这一阶段还包括：

- multi-shot 化学组分继承
- source inventory shot-to-shot 继承
- multi-shot activation bootstrap
- multi-shot `Rsh` 后处理

### 主要脚本

- `run_phase4_multishot.py`
- `run_single_cycle_cooling_check.py`
- `run_build_multishot_activation_bootstrap.py`
- `run_phase4_multishot_sheet_resistance.py`

### 主要模块

- `src/laser_doping_sim/phase4_multishot.py`
- `src/laser_doping_sim/phase3_stack_thermal.py`
- `src/laser_doping_sim/activation_models.py`
- `src/laser_doping_sim/sheet_resistance.py`

### 典型输出

- `outputs/phase4/.../multishot/`
- `outputs/phase4/.../thermal/`
- `outputs/phase4/.../thermal_last_shot/`
- `outputs/phase4/.../multishot_rsh/`

### 主要文档

- `docs/phases/phase4_multishot_mainline/phase4-multishot-v1-summary.md`
- `docs/phases/phase4_multishot_mainline/phase4-thermal-history-v2-summary.md`

## 横跨所有 Phase 的支撑文档

这些文件不只属于某一个 phase，而是整个项目的公共口径：

- `docs/project_model_walkthrough_zh.md`
- `docs/project_model_walkthrough_en.md`
- `docs/physics_user_quickstart_zh.md`
- `docs/physics_user_quickstart_en.md`
- `docs/physics_parameter_manual_zh.md`
- `docs/physics_parameter_manual_en.md`
- `docs/formula-reference-register.md`
- `docs/literature-usage-register.md`
- `docs/session-log.md`

## 如果现在只想看当前主线

最短路径建议是：

1. 先读 `docs/mainline-phase-map.md`
2. 或者直接打开 `docs/phases/README.md`
3. 再读 `docs/project_model_walkthrough_zh.md`
4. 再读 `docs/physics_user_quickstart_zh.md`
5. 想改单脉冲主线，看 `run_phase3.py`
6. 想跑多脉冲主线，看 `run_phase4_multishot.py`
7. 想做电学后处理，看 `run_sheet_resistance_cases.py` 和 `run_phase4_multishot_sheet_resistance.py`

