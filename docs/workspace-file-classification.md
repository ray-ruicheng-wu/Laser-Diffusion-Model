# 工作区文件分类索引

## 1. 这份索引怎么用

这份文档的目标不是移动文件，而是给当前工作区建立一套“看得懂的地图”。

当前处理原则是：

- **不移动已有文件**
- **不改旧结果目录名**
- 先用索引把“当前主线 / 历史结果 / 教程文档 / 原始数据”分开

这样做的好处是：

- 不会打断现有脚本和文档里的路径引用
- 可以先稳住项目，再决定以后是否真的重构目录

## 2. 根目录文件怎么理解

### 2.1 代码入口脚本

这些是直接运行的脚本：

- [run_phase1.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase1.py)
- [run_phase2.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase2.py)
- [run_phase3.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3.py)
- [run_phase3_power_scan.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3_power_scan.py)
- [run_phase3_physics_validation.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3_physics_validation.py)
- [run_sheet_resistance_cases.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_sheet_resistance_cases.py)
- [prepare_measured_initial_profile.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/prepare_measured_initial_profile.py)

### 2.2 原始实验数据

- [CTV-ECV-RAW.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/raw_measurements/CTV-ECV-RAW.csv)
- [CTV-SIMS-RAW.xlsx](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/raw_measurements/CTV-SIMS-RAW.xlsx)

这两份是当前 measured 主线的上游数据，不建议改名或覆盖。

### 2.3 项目说明和依赖

- [README.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/README.md)
- [requirements.txt](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/requirements.txt)
- [.gitignore](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/.gitignore)

### 2.4 临时或外部参考文件

- [materials_14_02322_v2.pdf](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/references/materials_14_02322_v2.pdf)
- [R011537.pdf](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/references/R011537.pdf)

这两份建议视为“临时参考文献缓存”，后面如果要长期保留，更适合在 `docs/` 建一个单独文献缓存说明。

## 3. `src/laser_doping_sim/` 怎么分

### 3.1 热学主模块

- [phase1_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py)
  - 1D 热模型
  - 相变和液相分数

- [phase3_stack_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py)
  - `PSG/Si` 堆栈热模型
  - 光学输入和温度场输出

### 3.2 扩散主模块

- [phase2_diffusion.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py)
  - 总磷扩散
  - `PSG -> Si` 注入
  - measured 初始轮廓接入

### 3.3 measured profile 模块

- [measured_profiles.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/measured_profiles.py)
  - 读取和重采样 `SIMS + ECV`
  - 生成 `initial total / active / inactive`

### 3.4 电学后处理模块

- [sheet_resistance.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/sheet_resistance.py)
  - `Masetti` 迁移率
  - `Rsh` 积分

- [activation_models.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/activation_models.py)
  - 经验活化模型
  - 当前已接入 `piecewise_nonactive_pool`

## 4. `inputs/` 怎么分

### 4.1 measured profiles

- [inputs/measured_profiles](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/measured_profiles)

当前最重要的文件：

- [ctv_measured_initial_profile.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/measured_profiles/ctv_measured_initial_profile.csv)
- [ctv_measured_initial_profile.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/measured_profiles/ctv_measured_initial_profile.png)
- [ctv_measured_initial_profile_summary.json](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/measured_profiles/ctv_measured_initial_profile_summary.json)

这组文件属于：

- **当前主线输入**

### 4.2 activation models

- [inputs/activation_models](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/activation_models)

当前主线文件：

- [segmented_nonactive_pool_empirical_24_60w.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/activation_models/segmented_nonactive_pool_empirical_24_60w.csv)

这组文件属于：

- **当前主线电学校准输入**

## 5. `outputs/` 怎么分

## 5.1 `outputs/phase1`

这是最早期的热模型结果库，主要用于：

- 基线热模型
- 吸收深度和参数敏感性
- 网格与时间步收敛检查

如果是为了看“最早热模型是怎么建立的”，就从这里开始。  
如果是为了看**当前 measured 主线**，不优先看这里。

### 5.2 `outputs/phase2`

这是最早期的扩散主线结果库，主要用于：

- 经典 `Phase 2` 扩散验证
- 旧参数敏感性与守恒性检查

如果是为了追历史，保留它们是有价值的；但它们不是当前最活跃结果。

### 5.3 `outputs/phase3`

这是当前最重要的结果库。

建议把它按下面几类理解：

#### A. 当前主线 measured 热/扩散结果

- [power_scan_24_60w_step6_measured_ctv_psg_eq_sims](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_24_60w_step6_measured_ctv_psg_eq_sims)
- [power_scan_27_36w_measured_ctv_psg_eq_sims](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_27_36w_measured_ctv_psg_eq_sims)
- [power_scan_30_60w_measured_ctv_psg_eq_sims](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_30_60w_measured_ctv_psg_eq_sims)
- [p24w_measured_ctv_psg_eq_sims](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/p24w_measured_ctv_psg_eq_sims)

这些目录属于：

- **当前主线热/扩散结果**

#### B. 当前主线片电阻结果

- [sheet_resistance_segmented_nonactive_pool_anchor_24_60w](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/sheet_resistance_segmented_nonactive_pool_anchor_24_60w)
- [sheet_resistance_segmented_nonactive_pool_step6_24_60w](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/sheet_resistance_segmented_nonactive_pool_step6_24_60w)

这些目录属于：

- **当前主线电学结果**

#### C. measured 主线的历史中间版本

- [sheet_resistance_measured_ctv_caseA_inactive_stays_inactive](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/sheet_resistance_measured_ctv_caseA_inactive_stays_inactive)
- [sheet_resistance_measured_ctv_caseB_inactive_fully_activated](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/sheet_resistance_measured_ctv_caseB_inactive_fully_activated)
- [sheet_resistance_measured_ctv_partial_calibrated_30_60](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/sheet_resistance_measured_ctv_partial_calibrated_30_60)
- [sheet_resistance_measured_ctv_psg_eq_sims_27_36_lowpower_calibrated](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/sheet_resistance_measured_ctv_psg_eq_sims_27_36_lowpower_calibrated)
- [sheet_resistance_measured_ctv_psg_eq_sims_27_36_lowpower_calibrated_v2](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/sheet_resistance_measured_ctv_psg_eq_sims_27_36_lowpower_calibrated_v2)
- [sheet_resistance_measured_ctv_psg_eq_sims_30_60_calibration_v2](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/sheet_resistance_measured_ctv_psg_eq_sims_30_60_calibration_v2)
- [sheet_resistance_measured_ctv_psg_eq_sims_30_60_lowpower_calibrated](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/sheet_resistance_measured_ctv_psg_eq_sims_30_60_lowpower_calibrated)

这些目录属于：

- **保留的标定历史**

#### D. 旧 measured scan

- [power_scan_30_60_90w_measured_ctv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_30_60_90w_measured_ctv)

这个目录的价值是：

- 保留 `30/60/90W` 这组较早的 measured scan 口径

但它不是当前最新的 `PSG = surface SIMS` 主线。

#### E. 杂项/阶段性测试

- [20ns results](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/20ns results)

这个目录建议视为：

- **专题测试**

## 6. `docs/` 怎么分

### 6.1 当前主线管理文档

- [current-model-summary.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/current-model-summary.md)
- [workspace-file-classification.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/workspace-file-classification.md)
- [session-log.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/session-log.md)
- [modeling-roadmap.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/modeling-roadmap.md)

### 6.2 公式与文献台账

- [formula-reference-register.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/formula-reference-register.md)
- [literature-usage-register.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/literature-usage-register.md)
- [laser-activation-literature-notes.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/laser-activation-literature-notes.md)
- [boundary-condition-review.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/boundary-condition-review.md)
- [literature-gap-analysis.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/literature-gap-analysis.md)

### 6.3 分阶段技术文档

- [phase1-analysis.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/phase1-analysis.md)
- [phase1-code-explained.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/phase1-code-explained.md)
- [phase2-analysis.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/phase2-analysis.md)
- [phase2-code-explained.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/phase2-code-explained.md)
- [phase3-analysis.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/phase3-analysis.md)
- [phase3-code-explained.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/phase3-code-explained.md)
- [phase3-work-report.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/phase3-work-report.md)
- [phase3-physics-validation.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/phase3-physics-validation.md)
- [phase3-physics-validation-work-report.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/phase3-physics-validation-work-report.md)
- [power-scan-60-90w-report.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/power-scan-60-90w-report.md)

### 6.4 教程与教学文档

- [modeling_tutorial_for_materials_undergrads.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/modeling_tutorial_for_materials_undergrads.md)
- [python_code_teaching_for_beginners.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/python_code_teaching_for_beginners.md)
- [project_total_walkthrough_obsidian.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/project_total_walkthrough_obsidian.md)
- [project_total_walkthrough_notebook.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/project_total_walkthrough_notebook.py)
- [model_report_for_humans.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/model_report_for_humans.md)

### 6.5 论文草稿与对外表述

- [laser-psg-phosphorus-doping-paper-draft.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/laser-psg-phosphorus-doping-paper-draft.md)
- [reproducible-paper-report-90w.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/reproducible-paper-report-90w.md)

### 6.6 流程与模板

- [stage-report-template.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/stage-report-template.md)
- [tutorial_update_checklist.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/tutorial_update_checklist.md)

### 6.7 角色记忆文件

- [wenshu-laoge-memory.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/wenshu-laoge-memory.md)
- [rizhi-wendang-laoge-memory.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/rizhi-wendang-laoge-memory.md)
- [gou-jiao-de-memory.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/gou-jiao-de-memory.md)

## 7. 如果现在只想看“当前主线”，最短路径是什么

只看这些就够：

### 输入

- [ctv_measured_initial_profile.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/measured_profiles/ctv_measured_initial_profile.csv)
- [segmented_nonactive_pool_empirical_24_60w.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/activation_models/segmented_nonactive_pool_empirical_24_60w.csv)

### 代码

- [phase3_stack_thermal.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py)
- [phase2_diffusion.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py)
- [sheet_resistance.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/sheet_resistance.py)
- [activation_models.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/activation_models.py)

### 结果

- [power_scan_24_60w_step6_measured_ctv_psg_eq_sims](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_24_60w_step6_measured_ctv_psg_eq_sims)
- [sheet_resistance_segmented_nonactive_pool_anchor_24_60w](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/sheet_resistance_segmented_nonactive_pool_anchor_24_60w)

### 文档

- [current-model-summary.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/current-model-summary.md)
- [formula-reference-register.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/formula-reference-register.md)
- [session-log.md](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/docs/session-log.md)

## 8. 下一步如果要真正重构目录，建议怎么做

当前不建议立刻大挪目录。  
如果后面确定要重构，我建议按下面的思路分层：

- `inputs/raw/`
- `inputs/processed/`
- `outputs/current/`
- `outputs/archive/`
- `docs/current/`
- `docs/archive/`

但在这一步之前，先靠这份索引管理会更稳。
