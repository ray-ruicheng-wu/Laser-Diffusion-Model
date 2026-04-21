# 工作区文件分类索引

这份文档专门给 `main` 工作区做分类。

目标不是把文件名全部背下来，而是回答 3 个问题：

1. 每个 phase 的标题是什么
2. 这一步主要做什么
3. 这个 phase 对应的脚本、模块、输出和文档分别在哪

## 1. 最推荐先看的入口文档

如果你第一次进入这个项目，建议按这个顺序：

1. `docs/mainline-phase-map.md`
2. `docs/project_model_walkthrough_zh.md`
3. `docs/physics_user_quickstart_zh.md`
4. `docs/physics_parameter_manual_zh.md`
5. `docs/current-model-summary.md`

它们的作用分别是：

- `mainline-phase-map.md`
  - 用 phase 视角看整个工作区
- `docs/phases/README.md`
  - 在 docs 目录树里直接按 phase 导航
- `project_model_walkthrough_zh.md`
  - 看建模故事和当前主线逻辑
- `physics_user_quickstart_zh.md`
  - 看运行顺序和结果怎么读
- `physics_parameter_manual_zh.md`
  - 看参数怎么改
- `current-model-summary.md`
  - 看最短导航索引

## 2. 按 Phase 分类的主线文件

如果你在文件树里更喜欢“直接点开一个 phase 文件夹”，现在也可以从这里开始：

- `docs/phases/phase0_data_and_calibration/`
- `docs/phases/phase1_single_layer_thermal/`
- `docs/phases/phase2_single_shot_diffusion/`
- `docs/phases/phase3_psg_si_single_shot_mainline/`
- `docs/phases/phase4_multishot_mainline/`

### Phase 0

Title：

`数据准备与电学校准输入`

这一步做什么：

- 把 `SIMS + ECV` 原始信息整理成 measured 初始 profile
- 准备单脉冲 / 多脉冲的经验活化输入
- 为后续 `Rsh` 标定准备数据口径

主要脚本：

- `prepare_measured_initial_profile.py`
- `run_dual_channel_activation_calibration.py`
- `run_dual_channel_high_power_refit.py`
- `run_dual_channel_monotonic_segment_refit.py`
- `run_sheet_resistance_cases.py`

主要模块：

- `src/laser_doping_sim/measured_profiles.py`
- `src/laser_doping_sim/activation_models.py`
- `src/laser_doping_sim/sheet_resistance.py`

主要输入：

- `inputs/raw_measurements/`
- `inputs/measured_profiles/`
- `inputs/activation_models/`

### Phase 1

Title：

`单层 Si 热学基线`

这一步做什么：

- 只算热学
- 建立单层 Si 的激光加热、相变、熔深时间窗

主要脚本：

- `run_phase1.py`

主要模块：

- `src/laser_doping_sim/phase1_thermal.py`

主要输出目录：

- `outputs/phase1/`

主要文档：

- `docs/phases/phase1_single_layer_thermal/phase1-analysis.md`
- `docs/phases/phase1_single_layer_thermal/phase1-code-explained.md`

### Phase 2

Title：

`单脉冲热驱动总磷扩散`

这一步做什么：

- 在 `Phase 1` 热历史上求总磷扩散
- 加入表面 source exchange 和库存守恒
- 生成第一次可用的结深和浓度分布

主要脚本：

- `run_phase2.py`

主要模块：

- `src/laser_doping_sim/phase2_diffusion.py`
- `src/laser_doping_sim/phase1_thermal.py`

主要输出目录：

- `outputs/phase2/`

主要文档：

- `docs/phases/phase2_single_shot_diffusion/phase2-analysis.md`
- `docs/phases/phase2_single_shot_diffusion/phase2-code-explained.md`
- `docs/phases/phase2_single_shot_diffusion/boundary-condition-review.md`

### Phase 3

Title：

`PSG/Si 双层单脉冲主线与实验对标`

这一步做什么：

- 把热模型升级成 `PSG/Si` 双层
- 并入 measured initial profile
- 做功率扫描、物理验证和单脉冲 `Rsh` 对照

这也是当前最重要的单脉冲主线。

主要脚本：

- `run_phase3.py`
- `run_phase3_power_scan.py`
- `run_phase3_physics_validation.py`
- `run_sheet_resistance_cases.py`

主要模块：

- `src/laser_doping_sim/phase3_stack_thermal.py`
- `src/laser_doping_sim/phase2_diffusion.py`
- `src/laser_doping_sim/measured_profiles.py`
- `src/laser_doping_sim/activation_models.py`
- `src/laser_doping_sim/sheet_resistance.py`

主要输出目录：

- `outputs/phase3/default_run/`
- `outputs/phase3/power_scan_.../`
- `outputs/phase3/sheet_resistance_.../`
- `outputs/phase3/dual_channel_activation_.../`

主要文档：

- `docs/phases/phase3_psg_si_single_shot_mainline/phase3-analysis.md`
- `docs/phases/phase3_psg_si_single_shot_mainline/phase3-code-explained.md`
- `docs/phases/phase3_psg_si_single_shot_mainline/phase3-physics-validation.md`
- `docs/phases/phase3_psg_si_single_shot_mainline/phase3-physics-validation-work-report.md`
- `docs/phases/phase0_data_and_calibration/dual-channel-activation-method.md`

### Phase 4

Title：

`多脉冲 thermal-history 与 multi-shot 电学扩展`

这一步做什么：

- 把单脉冲主线扩展到 repeated shots
- 支持 `reuse_single_pulse` 和 `accumulate`
- 继续做 multi-shot 注入、multi-shot 活化和 `Rsh` 后处理

主要脚本：

- `run_phase4_multishot.py`
- `run_single_cycle_cooling_check.py`
- `run_build_multishot_activation_bootstrap.py`
- `run_phase4_multishot_sheet_resistance.py`

主要模块：

- `src/laser_doping_sim/phase4_multishot.py`
- `src/laser_doping_sim/phase3_stack_thermal.py`
- `src/laser_doping_sim/activation_models.py`
- `src/laser_doping_sim/sheet_resistance.py`

主要输出目录：

- `outputs/phase4/.../multishot/`
- `outputs/phase4/.../thermal/`
- `outputs/phase4/.../thermal_last_shot/`
- `outputs/phase4/.../multishot_rsh/`

主要文档：

- `docs/phases/phase4_multishot_mainline/phase4-multishot-v1-summary.md`
- `docs/phases/phase4_multishot_mainline/phase4-thermal-history-v2-summary.md`

## 3. `src/laser_doping_sim/` 怎么理解

如果只看核心模块，可以按功能拆成 4 类：

### 热学

- `phase1_thermal.py`
  - 单层 Si 热学
- `phase3_stack_thermal.py`
  - `PSG/Si` 双层热学

### 扩散

- `phase2_diffusion.py`
  - 单脉冲总磷扩散与 source exchange
- `phase4_multishot.py`
  - 多脉冲 shot-to-shot 继承与 thermal-history 扩展

### 电学

- `sheet_resistance.py`
  - `Rsh` 积分和迁移率模型
- `activation_models.py`
  - 单脉冲 / 多脉冲经验活化模型

### measured 输入

- `measured_profiles.py`
  - `SIMS + ECV` 处理后的主线 profile

## 4. `outputs/` 怎么看

- `outputs/phase1/`
  - 热学基线与网格 / 时间步测试
- `outputs/phase2/`
  - 单脉冲扩散和边界条件验证
- `outputs/phase3/`
  - 当前单脉冲主线、功率扫描、单脉冲 `Rsh`
- `outputs/phase4/`
  - 当前多脉冲主线、thermal-history、bootstrap 和 multi-shot `Rsh`

如果你现在最关心 pulse-train 主线，优先看 `outputs/phase4/`。

## 5. 横跨所有 Phase 的公共文档

### 主教程与用户入口

- `docs/project_model_walkthrough_zh.md`
- `docs/project_model_walkthrough_en.md`
- `docs/physics_user_quickstart_zh.md`
- `docs/physics_user_quickstart_en.md`
- `docs/physics_parameter_manual_zh.md`
- `docs/physics_parameter_manual_en.md`

### 公式、文献和统一口径

- `docs/formula-reference-register.md`
- `docs/literature-usage-register.md`
- `docs/phases/phase2_single_shot_diffusion/interface-model-literature-notes.md`
- `docs/phases/phase0_data_and_calibration/laser-activation-literature-notes.md`
- `docs/phases/phase3_psg_si_single_shot_mainline/literature-gap-analysis.md`

### 日志与阶段记录

- `docs/session-log.md`
- `docs/phases/phase3_psg_si_single_shot_mainline/phase3-work-report.md`
- `docs/stage-report-template.md`

## 6. 归档区

历史但不再作为主入口的内容放在：

- `docs/archive/`

如果你只是想接手当前主线，不需要先看这里。

## 7. 如果现在只想看“当前 main 主线”，最短路径是什么

文档：

- `docs/mainline-phase-map.md`
- `docs/project_model_walkthrough_zh.md`
- `docs/physics_user_quickstart_zh.md`
- `docs/current-model-summary.md`

输入：

- `inputs/measured_profiles/ctv_measured_initial_profile.csv`

代码：

- `run_phase3.py`
- `run_phase4_multishot.py`
- `run_sheet_resistance_cases.py`
- `run_phase4_multishot_sheet_resistance.py`

