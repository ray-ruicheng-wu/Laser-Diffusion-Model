# 日志和文档老哥记忆文件

## 1. 角色

`日志和文档老哥` 负责：

1. 维护阶段总结、结果摘要、续做入口和文档一致性。
2. 把每个阶段的重要结果、关键结论、风险点和下一步写进可续接的记录。
3. 不负责查新文献，不负责决定物理公式是否正确；这些优先交给 `文书老哥`。
4. 不直接修改核心求解代码，除非主线程明确要求它参与文档相关的小型接口补充。

## 2. 与其他角色的分工

### 文书老哥

负责：

- 找文献
- 补数学模型
- 整理参数范围
- 判断哪些公式有来源

不负责：

- 维护阶段日志的完整叙事
- 维护“下一次从哪里继续做”

### 狗叫的

负责：

- 校对公式实现
- 检查结果是否符合数学和物理量级
- 指出 bug、守恒问题、收敛问题

### 臭写代码的

负责：

- 写代码
- 修 bug
- 跑结果

### 日志和文档老哥

负责：

- 把上面三条线的结果整理成项目记录
- 保证 docs 内口径一致
- 每阶段结束后补齐总结

## 3. 固定维护的文件

优先维护这些文件：

1. `docs/session-log.md`
2. `docs/modeling-roadmap.md`
3. `docs/formula-reference-register.md`
4. `docs/phaseX-analysis.md`
5. `docs/phaseX-code-explained.md`

必要时可以新增：

1. `docs/stage-summary-*.md`
2. `docs/results-*.md`
3. `docs/handoff-*.md`

## 4. 每阶段结束后的固定动作

每完成一个阶段，日志和文档老哥至少要检查并更新：

1. 本阶段做了什么
2. 最终输出文件在哪里
3. 关键结果数值是什么
4. 结果是否已经经过 `狗叫的` 审查
5. 采用了哪些公式
6. 引用了哪些文献
7. 当前还缺什么
8. 下一步建议做什么

新增约束：

1. 任何一轮新结果，如果没有 `狗叫的` 审查记录，就不能算正式阶段结果。
2. 阶段工作报告必须单独保留“狗叫的审查记录”小节。

建议固定对应到这些文档字段或块：

1. `current target`
2. `本次结论`
3. `当前推荐路线`
4. `近期待确认`
5. `继续入口`
6. `阶段当前状态`
7. `默认结果`
8. `新确认的工艺前提`
9. `交付物`

## 5. 文档输出口径

写文档时优先保持：

1. 先写结论，再写细节
2. 明确区分：
   - 已实现
   - 已验证
   - 候选方案
   - 未完成
3. 尽量给出文件路径和结果位置
4. 不重复抄长段代码，优先指向代码文件

## 6. 与公式总表的关系

日志和文档老哥不独立决定新公式是否采用，但要负责检查：

1. 新阶段是否用了新公式
2. 新公式是否已经登记到 `docs/formula-reference-register.md`
3. 阶段文档里的公式口径是否和总表一致

## 7. 使用约定

以后只要继续调用 `日志和文档老哥`，主线程应先要求它：

1. 先阅读本文件
2. 再阅读 `docs/session-log.md`
3. 再阅读 `docs/formula-reference-register.md`
4. 再检查 `docs/modeling-roadmap.md`
5. 只做文档、归档、总结和续做整理
6. 如发现资料口径不确定，应把问题转给 `文书老哥`

## 8. 本次存档时间

- `2026-04-07`

## 9. 新的归档门槛：必须包含研究线对标

从现在开始，报告线在归档任何新结果之前，必须确认下面两条都已经完成：

1. 审查线已经给出审查结论
2. 研究线已经给出文献对比和改进建议

报告线还必须检查阶段报告中是否已经写明：

1. 当前结果和哪些论文对比
2. 差距在哪里
3. 研究线是否认为结果 `疑似有错 / 基本可信`
4. 研究线建议优先改什么

如果第 2 条没有完成，报告线不应把本轮结果视为“完整归档”
## 9. 片电阻分析的固定产物

如果某一阶段包含片电阻分析，后续阶段报告里必须默认检查并记录这三个标准产物是否已生成：

1. `silicon_p_profile_sheet_analysis.png`
2. `cumulative_p_dose_vs_depth.png`
3. `silicon_profile_analysis.csv`

### sheet dose 口径

后续凡是写片电阻/片剂量分析，`sheet dose` 一律按真实表面 `z=0` 起积分，不再用表观顶部或网格首点替代。

### 初始未激活表面 P 层

如果模型支持初始未激活表面 `P` 层，例如 `30 nm / 5e20 cm^-3`，后续归档时要把它作为前序工序残留 `P` 单独记账，并在初始片电阻分析里与 `active emitter` 分开记录。

### 60–90W 功率扫描口径

当前这轮功率扫描的候选正式口径改为 `dt=0.1` 版本，目录为 `C:\Users\User\Desktop\Codex\Diffusion Simulation\outputs\phase3\power_scan_60_90w_dt01`。`dt=0.2` 版本因高功率时间步敏感性暂不作为正式口径；等审查线和研究线回结论后再正式归档。

### 论文式主文档入口

后续如果要写阶段报告或总报告，优先把 `docs/laser-psg-phosphorus-doping-paper-draft.md` 当作当前项目的主论文草稿入口。

### 新的细时间步扫描

新的细时间步扫描 `outputs/phase3/power_scan_30_100w_dt005` 已完成，但当前只作为中间状态记录。后续要等审查线和研究线都给出结论后，再写正式报告。

### 片电阻后处理首版

本轮已新增：

- `src/laser_doping_sim/sheet_resistance.py`
- `run_sheet_resistance_cases.py`
- `outputs/phase3/sheet_resistance_inactive5pct_30_60_90`

并且 `F-032` / `F-033` / `F-034` 与 `R-021` 已经补进公式/文献台账。

当前只按中间结果记账；等审查线和研究线给出简短回执后，再决定是否扩写到正式阶段补充。

### measured-profile 导入与 measured-driven 扫描

本轮已新增：

- `src/laser_doping_sim/measured_profiles.py`
- `prepare_measured_initial_profile.py`
- `inputs/measured_profiles/ctv_measured_initial_profile.csv`
- `inputs/measured_profiles/ctv_measured_initial_profile.png`
- `outputs/phase3/power_scan_30_60_90w_measured_ctv`

当前只按待回执的阶段补充记账，不提前升级成正式 milestone；等审查线和研究线给出简短回执后，再决定是否正式扩写。

### measured 初始条件重构

这轮 measured 初始条件的后续归档要点要记住：

1. RAW 输入直接来自 `CTV-ECV-RAW.csv` 和 `CTV-SIMS-RAW.xlsx`
2. `measured` 模式下的 `initial total` 现在直接取 `SIMS total`
3. 当前 `measured inactive` 口径恢复为 `max(SIMS - ECV, 0)`，覆盖上一轮“平滑表面残差估计”的临时写法
4. `30/60/90W` 的 measured-driven 新结果已经按这套重构后的初始条件重跑

后续如要写正式阶段补充，应优先强调“authoritative total 的口径收紧”以及“当前 inactive 采用 `max(SIMS - ECV, 0)` 记账”这两个变化。

### measured-profile / Rsh 当前归档口径

后续遇到 measured-driven 的片电阻归档，要默认记住下面这套更新后的口径：

1. `measured inactive` 当前恢复为 `max(SIMS - ECV, 0)`。
2. `final total` 始终包含 `PSG injected component`。
3. measured-driven `Rsh` 默认保留两套后处理边界：
   - `Case A`：initial inactive 在 laser 后仍不计 active
   - `Case B`：initial inactive 在 laser 后全部计为 active
4. 当前对照结果目录是：
   - `outputs/phase3/sheet_resistance_measured_ctv_caseA_inactive_stays_inactive`
   - `outputs/phase3/sheet_resistance_measured_ctv_caseB_inactive_fully_activated`
5. 这轮结果当前只按“待审查线、待研究线回执的阶段补充”记账，不能提前升级成正式 milestone。

### PSG = surface SIMS 低功率校准口径

后续如果再引用这轮 measured-driven 低功率扫描，要默认记住：

1. `source_dopant_concentration_cm3` 当前已提高到 measured surface `SIMS = 4.5913166904198945e21 cm^-3`
2. 初始 inactive baseline activation 取 `0.04448923256987511`，对应 `Rsh_init = 180 ohm/sq`
3. 低功率 post-laser inactive activation 取 `0.38734199240748757`，对应 `30W -> 110 ohm/sq`
4. 当前低功率 `Rsh` 读取按 `injected_activation_fraction = 0.0`
5. 当前代表目录：
   - `outputs/phase3/power_scan_27_36w_measured_ctv_psg_eq_sims`
   - `outputs/phase3/sheet_resistance_measured_ctv_psg_eq_sims_27_36_lowpower_calibrated_v2`
6. `27/30/33/36W` 当前全部显示：
   - `no melt`
   - `no injection`
   - `Rsh` 基本都在 `110 ohm/sq`
7. 这轮结果当前只按“待审查线、待研究线回执的阶段补充”记账，不能提前升级成正式 milestone。

### 基于实验趋势的低功率经验电学校准

后续如果再引用低功率 `Rsh` 拟合，要默认记住还有一层更贴近实验趋势的经验校准：

1. 实验点：
   - `24W`：`170.8851 -> 163.13`
   - `27W`：`171.64 -> 150.38`
   - `30W`：`175.79 -> 144.95`
   - `33W`：`161.26 -> 117.588`
2. 统一 baseline calibration：
   - `initial inactive activation = 0.06447924522684517`
   - 平均 `Rsh_init = 169.893775 ohm/sq`
3. 逐点 final inactive activation：
   - `24W = 0.08211699366064995`
   - `27W = 0.1271423637719521`
   - `30W = 0.15120848835373957`
   - `33W = 0.3210707049033614`
4. 这组参数的归档定位是“经验性电学校准层”。
5. 必须同时写明：在当前 `PSG = surface SIMS + melt_only` 模型下，`24–36W` 的实际热/扩散结果仍全部属于 `no melt / no injection`，所以这层参数不能被误写成热扩散层或低功率注入层的物理结论。
6. 这轮结果当前同样只按“待审查线、待研究线回执的阶段补充”记账，不能提前升级成正式 milestone。

### 6W 间隔经验外推

后续如果引用 `24–60W` 的 `6W` 间隔经验外推，要默认记住：

1. 目录是：
   - `outputs/phase3/power_scan_24_60w_step6_measured_ctv_psg_eq_sims`
2. 当前外推表是：
   - `empirical_rsh_extrapolation_step6.csv`
   - `empirical_rsh_extrapolation_step6_clamped.csv`
3. 代表值：
   - `24W -> 164.17 ohm/sq`
   - `30W -> 138.10 ohm/sq`
   - `36W -> 105.17 ohm/sq`
4. `42W` 起 raw `final inactive activation > 1`，已经不物理；因此：
   - raw 外推只能当“失效提醒”
   - `clamped` 结果只能当辅助边界参考
5. 当前 `clamped` 代表值：
   - `42W -> 71.28 ohm/sq`
   - `48W -> 71.28 ohm/sq`
   - `54W -> 60.56 ohm/sq`
   - `60W -> 29.77 ohm/sq`
6. 必须同时写明：`54W` 起热模型已经进入 `partial melt / injection` 过渡，因此不宜继续用纯低功率经验律裸外推。
7. 这轮结果当前只按“待审查线、待研究线回执的阶段补充”记账，不能提前升级成正式 milestone。

### 教程同步收尾

后续每次阶段报告完成后，默认还要检查当前主线教程 `docs/project_model_walkthrough_zh.md` 是否已经同步更新；只有教程同步完成，才算 milestone 真正收尾。

### 裁剪版 P profile 合并对比图

本轮新增的 `30W/60W/90W redistribution` 裁剪版 `P profile` 合并对比图为：

- `outputs/phase3/p_profile_cropped_comparison_30_60_90w.png`

当前先按中间材料记账，等审查线和研究线回执后再决定是否正式归档。

### 30W/60W/90W 裁剪图回执

本轮 `30W/60W/90W` 裁剪版 `P profile` 对比图已经收到回执：

- 审查线：没有明显物理或逻辑错误，变化与 summary 一致；但裁剪到 `junction + 50nm` 会隐藏更深尾部剂量信息，需和全深度 / 累计剂量图配套解读。
- 研究线：符合 redistribution 主线，`30W/60W` 基本不变，`90W` 主要是近表面峰值下降和深部展宽；当前仍属于 `PSG` 再注入几乎为零的 regime。

这条记录可引用，但暂不升级成新 milestone。

### 30–100W / 2W step / dt=0.05ns 完整扫描

新的完整扫描目录为：

- `C:\Users\User\Desktop\Codex\Diffusion Simulation\outputs\phase3\power_scan_30_100w_step2_dt005_redistribution`

这轮已补齐 `30–100W`、`2W` 步长、`dt = 0.05 ns` 下的完整总表、`json`、`manifest` 和趋势图。

当前只按中间结果记账，等审查线和研究线给出简短回执后，再决定是否写正式阶段补充。
