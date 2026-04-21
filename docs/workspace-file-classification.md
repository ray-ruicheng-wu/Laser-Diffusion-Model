# 工作区文件分类索引

这份文档的目标是给当前工作区建立一套清晰的“主线地图”。

重点不是把所有历史文件删掉，而是区分：

- 哪些是当前主线文档
- 哪些是当前主线输入
- 哪些是主线运行脚本
- 哪些是阶段性技术说明
- 哪些只是历史保留或归档

## 1. 推荐先看的主线文档

如果你是第一次进入这个项目，优先按下面顺序读：

1. [project_model_walkthrough_zh.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/project_model_walkthrough_zh.md)
2. [project_model_walkthrough_en.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/project_model_walkthrough_en.md)
3. [physics_user_quickstart_zh.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/physics_user_quickstart_zh.md)
4. [physics_user_quickstart_en.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/physics_user_quickstart_en.md)
5. [physics_parameter_manual_zh.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/physics_parameter_manual_zh.md)
6. [physics_parameter_manual_en.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/physics_parameter_manual_en.md)
7. [current-model-summary.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/current-model-summary.md)

它们分别承担的角色是：

- `project_model_walkthrough_*`
  当前统一主教程与主线总说明
- `physics_user_quickstart_*`
  面向使用者的运行顺序、结果读取和完整测试入口
- `physics_parameter_manual_*`
  面向调参与建模的参数手册
- `current-model-summary.md`
  面向快速导航的短索引

## 2. 当前主线运行脚本

这些脚本是当前最重要的运行入口：

- [run_phase1.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase1.py)
- [run_phase2.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase2.py)
- [run_phase3.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3.py)
- [run_phase3_power_scan.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3_power_scan.py)
- [run_sheet_resistance_cases.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_sheet_resistance_cases.py)
- [run_phase4_multishot.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase4_multishot.py)
- [run_build_multishot_activation_bootstrap.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_build_multishot_activation_bootstrap.py)
- [run_phase4_multishot_sheet_resistance.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase4_multishot_sheet_resistance.py)

配套输入准备脚本：

- [prepare_measured_initial_profile.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/prepare_measured_initial_profile.py)

## 3. `src/laser_doping_sim/` 主模块

### 3.1 热学

- [phase1_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py)
  单层 Si 热模型
- [phase3_stack_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py)
  `PSG/Si` 堆栈热模型

### 3.2 扩散与多脉冲

- [phase2_diffusion.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py)
  单脉冲扩散与 source exchange
- [phase4_multishot.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase4_multishot.py)
  多脉冲 shot-to-shot 继承

### 3.3 电学后处理

- [sheet_resistance.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/sheet_resistance.py)
  片电阻积分与 Masetti 迁移率
- [activation_models.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/activation_models.py)
  单脉冲和多脉冲经验活化模型

### 3.4 measured 输入

- [measured_profiles.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/measured_profiles.py)
  `SIMS + ECV` 处理后的 measured 初始轮廓

## 4. 当前主线输入

### 4.1 measured 初始轮廓

- [ctv_measured_initial_profile.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/measured_profiles/ctv_measured_initial_profile.csv)
- [ctv_measured_initial_profile_summary.json](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/measured_profiles/ctv_measured_initial_profile_summary.json)

这组文件属于当前化学主线输入。

### 4.2 单脉冲电学校准输入

- [measured_rsh_24_60w.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/activation_models/measured_rsh_24_60w.csv)

### 4.3 多脉冲电学校准输入

当前多脉冲活化参数一般来自新的 Phase 4 输出目录，而不是旧的单脉冲表直接覆盖：

- `outputs/phase4/.../multishot_dual_channel_params.csv`

## 5. `outputs/` 怎么理解

### 5.1 `outputs/phase1`

最早期热学基线、网格与时间步检查。

### 5.2 `outputs/phase2`

单层扩散和边界条件历史验证结果。

### 5.3 `outputs/phase3`

当前单脉冲主线结果库，主要包括：

- 单个 measured 主线 case
- 功率扫描
- 单脉冲 `Rsh` 后处理
- dual-channel activation 标定表

### 5.4 `outputs/phase4`

当前多脉冲主线结果库，主要包括：

- multi-shot chemistry
- thermal-history accumulate 测试
- multi-shot activation bootstrap
- multi-shot `Rsh` 后处理

如果你在看当前最活跃的 pulse-train 主线，优先看这里。

## 6. 当前主线技术文档

### 6.1 主线说明与导航

- [current-model-summary.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/current-model-summary.md)
- [session-log.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/session-log.md)
- [workspace-file-classification.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/workspace-file-classification.md)

### 6.2 Phase 说明

- [phase1-analysis.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/phase1-analysis.md)
- [phase2-analysis.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/phase2-analysis.md)
- [phase3-analysis.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/phase3-analysis.md)
- [phase4-multishot-v1-summary.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/phase4-multishot-v1-summary.md)
- [phase4-thermal-history-v2-summary.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/phase4-thermal-history-v2-summary.md)

### 6.3 公式、文献与口径

- [formula-reference-register.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/formula-reference-register.md)
- [dual-channel-activation-method.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/dual-channel-activation-method.md)
- [literature-usage-register.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/literature-usage-register.md)
- [boundary-condition-review.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/boundary-condition-review.md)
- [interface-model-literature-notes.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/interface-model-literature-notes.md)
- [laser-activation-literature-notes.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/laser-activation-literature-notes.md)
- [literature-gap-analysis.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/literature-gap-analysis.md)

### 6.4 教学与辅助文档

- [modeling_tutorial_for_materials_undergrads.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/modeling_tutorial_for_materials_undergrads.md)
- [python_code_teaching_for_beginners.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/python_code_teaching_for_beginners.md)
- [stage-report-template.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/stage-report-template.md)
- [tutorial_update_checklist.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/tutorial_update_checklist.md)

## 7. 已归档文档

已被新主线 walkthrough 取代、但仍保留历史价值的文档，放在：

- [archive/README.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/archive/README.md)

当前已归档：

- [project_total_walkthrough_obsidian.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/archive/legacy_walkthroughs/project_total_walkthrough_obsidian.md)
- [project_total_walkthrough_notebook.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/archive/legacy_walkthroughs/project_total_walkthrough_notebook.py)

## 8. 如果现在只想看“当前主线”，最短路径是什么

只看这几项就够：

### 文档

- [project_model_walkthrough_zh.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/project_model_walkthrough_zh.md)
- [physics_user_quickstart_zh.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/physics_user_quickstart_zh.md)
- [physics_parameter_manual_zh.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/physics_parameter_manual_zh.md)

### 输入

- [ctv_measured_initial_profile.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/measured_profiles/ctv_measured_initial_profile.csv)

### 代码

- [run_phase3.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3.py)
- [run_phase4_multishot.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase4_multishot.py)
- [run_sheet_resistance_cases.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_sheet_resistance_cases.py)
- [run_phase4_multishot_sheet_resistance.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase4_multishot_sheet_resistance.py)
