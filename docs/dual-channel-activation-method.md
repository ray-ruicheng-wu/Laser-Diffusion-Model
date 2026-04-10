# 双通道活化模型方法与当前结论

## 1. 为什么要把两类活化分开

当前 measured 主线里，激光后的有效施主来源至少有三部分：

1. 激光前就已经 active 的那部分 P
2. 激光前存在但未完全 active 的 `initial inactive P`
3. 激光过程中从 `PSG` 新进入 Si 的 `injected P`

如果把第 2 类和第 3 类混成一个单一 `non-active pool`，虽然可以把实验 `Rsh` 趋势贴住，但会丢掉物理解释力。

所以这一步的目标是把激光后有效施主重新写成：

\[
N_{D,\mathrm{act,final}}(z)
=
N_{D,\mathrm{active,component}}(z)
+ \eta_{\mathrm{inactive}}(P)\,N_{D,\mathrm{inactive,component}}(z)
+ \eta_{\mathrm{inj}}(P)\,N_{D,\mathrm{inj,component}}(z)
\]

这里：

- `eta_inactive(P)` 表示激光后初始 inactive P 的再激活比例
- `eta_inj(P)` 表示激光后新注入 P 的电学活化比例

## 2. 当前采用的分账方法

当前代码已经能把激光后 profile 拆成三部分：

- `final_active_component`
- `final_inactive_component`
- `final_injected_component`

当前实现入口：

- [run_sheet_resistance_cases.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_sheet_resistance_cases.py)
- [activation_models.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/activation_models.py)

双通道模式名是：

- `piecewise_dual_channel`

## 3. 标定方法

### 3.1 初始态基线

因为当前 measured 初始 profile 只有一条，所以初始片电阻先用实验前片阻的平均值来标定一个统一基线：

\[
N_{D,\mathrm{act,init}}
=
N_{D,\mathrm{active,init}}
+ f_{\mathrm{init}}N_{D,\mathrm{inactive,init}}
\]

当前得到：

- `f_init = 0.06447924522684517`
- 对应 `Rsh_init = 169.893775 ohm/sq`

### 3.2 低功率段：先拟合 `eta_inactive`

标定逻辑是：

- 如果某个功率点的 `final_injected_component_sheet_dose_cm2` 小于阈值
- 就把它当作“几乎没有新注入”
- 此时只拟合 `eta_inactive`

当前阈值：

- `1e14 cm^-2`

因此当前低注入标定点是：

- `24, 27, 30, 33, 36, 42, 48 W`

在这组点上：

\[
N_{D,\mathrm{act,final}}
=
N_{D,\mathrm{active,component}}
+ \eta_{\mathrm{inactive}}(P)N_{D,\mathrm{inactive,component}}
\]

并通过实验 `Rsh_after` 反求 `eta_inactive(P)`。

### 3.3 高功率段：再尝试拟合 `eta_inj`

对 `54, 60 W`：

- 先用低功率拟合得到的 `eta_inactive(P)` 外推到当前功率
- 再固定这部分
- 然后反求 `eta_inj(P)`

即：

\[
N_{D,\mathrm{act,final}}
=
N_{D,\mathrm{active,component}}
+ \eta_{\mathrm{inactive,from\ low\ power}}(P)\,N_{D,\mathrm{inactive,component}}
+ \eta_{\mathrm{inj}}(P)\,N_{D,\mathrm{inj,component}}
\]

## 4. 当前输入与输出文件

### 输入

- measured `Rsh` 表：
  - [measured_rsh_24_60w.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/inputs/activation_models/measured_rsh_24_60w.csv)

### 自动标定脚本

- [run_dual_channel_activation_calibration.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_dual_channel_activation_calibration.py)

### 输出

- [dual_channel_activation_model.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/dual_channel_activation_calibration_24_60w/dual_channel_activation_model.csv)
- [calibration_summary.json](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/dual_channel_activation_calibration_24_60w/calibration_summary.json)
- [measured_vs_modeled_rsh.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/dual_channel_activation_calibration_24_60w/measured_vs_modeled_rsh.csv)
- [dual_channel_activation_fractions.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/dual_channel_activation_calibration_24_60w/dual_channel_activation_fractions.png)
- [measured_vs_dual_channel_rsh.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/dual_channel_activation_calibration_24_60w/measured_vs_dual_channel_rsh.png)

## 5. 当前标定结果

### 5.1 低功率段 `eta_inactive`

当前低功率段拟合结果是：

- `24 W`: `0.08211699366064995`
- `27 W`: `0.1271423637719521`
- `30 W`: `0.15120848835373957`
- `33 W`: `0.3210707049033614`
- `36 W`: `0.4374652370682913`
- `42 W`: `0.5057229858360608`
- `48 W`: `0.6439491600220855`

并且在这些点上，当前双通道模型能精确贴住实验 `Rsh_after`。

### 5.2 高功率段 `eta_inj`

这里出现了当前最关键的新结论：

在把低功率得到的 `eta_inactive(P)` 直接延续到 `54/60 W` 后，模型已经预测出**过低**的 `Rsh`。

也就是说：

- 即使令 `eta_inj = 0`
- 仅靠“高 inactive 再激活”这一项
- 就已经把 `Rsh` 压得比实验更低

因此当前自动标定结果会给出：

- `54 W`: `eta_inj = 0`，且仍然 `Rsh_model < Rsh_exp`
- `60 W`: `eta_inj = 0`，且仍然 `Rsh_model << Rsh_exp`

这不是脚本 bug，而是一个真正的建模结论：

> 低功率段得到的 `eta_inactive` 不能直接无条件外推到高功率熔化区。

## 6. 当前得到的物理启发

这一步最重要的收获不是“已经完美分离成功”，而是明确看见了：

### 6.1 `24–48 W`

这段可以主要用：

- `initial inactive re-activation`

来解释。

### 6.2 `54–60 W`

这段不能再简单看成：

- “inactive activation 继续增加”

因为那样会让模型给出比实验更低的 `Rsh`。

更合理的解释是：

- 高功率区进入了新 regime
- `initial inactive` 的有效活化规律发生变化
- `injected P` 的活化规律也必须单独考虑
- 甚至可能要考虑高浓度去活化、聚集或 mobility 降低

## 7. 当前双通道模型的状态

当前这套双通道模型已经：

- 在代码结构上做出来了
- 能稳定分账
- 能自动反标参数
- 能证明高功率区存在不可直接外推的 regime change

但它还没有形成一个“最终 adopted 的高功率双通道闭合”。

## 8. 下一步该怎么做

最推荐的下一步不是继续硬拟合，而是先在下面几条路里选一条：

1. 让 `eta_inactive` 在高功率区允许 rollover / decrease
2. 让 `eta_inj` 单独受熔化或再凝固指标控制
3. 把 `Rsh` 中的 mobility 退化影响进一步显式化
4. 如果有 laser 后 `ECV`，直接用它帮助分离两条活化通道

## 9. 一句话结论

双通道模型现在已经正式建立起来了，但它目前最重要的价值是：

- **帮助我们发现高功率区不能再用低功率的 inactive 激活规律外推**

这就是这一步最关键的建模结果。

## 10. 2026-04-09 高功率段重拟合补充

在识别出 `54/60 W` 不能直接沿用低功率 `eta_inactive(P)` 后，又追加了一轮 **高功率段重拟合**。

### 10.1 重拟合假设

为了避免高功率区完全无约束，这一轮采用了一个最小闭合：

1. `48 W` 作为低功率段与高功率段的边界锚点
2. `eta_inactive(P)` 在 `48 -> 60 W` 之间做线性回落
3. `eta_inj(P)` 在 `48 -> 60 W` 之间从 `0` 线性抬升
4. 用 `54 W` 和 `60 W` 的实验 `Rsh` 反求：
   - `eta_inactive(60 W)`
   - `eta_inj(60 W)`

### 10.2 拟合结果

输出文件：

- [dual_channel_activation_model_refit.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/dual_channel_high_power_refit_48_60w/dual_channel_activation_model_refit.csv)
- [high_power_refit_summary.json](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/dual_channel_high_power_refit_48_60w/high_power_refit_summary.json)
- [measured_vs_refit_rsh.png](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/dual_channel_high_power_refit_48_60w/measured_vs_refit_rsh.png)

当前得到：

- `eta_inactive(48 W) = 0.6439491600220855`
- `eta_inactive(54 W) = 0.41047939837389896`
- `eta_inactive(60 W) = 0.1770096367257125`
- `eta_inj(54 W) = 0.006692692684585006`
- `eta_inj(60 W) = 0.013385385369170012`

### 10.3 当前解释

这组结果说明：

1. 为了贴住 `54/60 W` 的实验片阻，高功率区的“initial inactive 再激活”必须明显低于低功率外推值
2. `PSG` 注入通道在当前闭合下只需要一个很小但非零的电学活化比例
3. 因而高功率区更像是：
   - `inactive` 通道发生 rollover / weakening
   - `injected` 通道开始参与

但要注意：

- 这依然是 **高功率段的经验闭合**
- 不是已经被独立 `ECV` 证实的唯一物理解

## 11. 2026-04-09 细时间步单调段重拟合

在继续检查 `all_states` 版本后，我们发现：

- 先前 `54–60 W` 的异常不只是电学校准层问题
- `dt = 0.2 ns` 的热结果本身在该段也不稳定
- 把时间步细化到 `dt = 0.05 ns` 后，`54–60 W` 不再表现为先前那种大熔深 fully molten 区间

对应结果目录：

- `outputs/phase3/power_scan_54_60w_step2_dt005_measured_ctv_psg_eq_sims_allstates`
- `outputs/phase3/power_scan_48_60w_step2_dt005_measured_ctv_psg_eq_sims_allstates`

### 11.1 新的高功率段经验闭合

为了先修复 `Rsh` 曲线在 `48–60 W` 的异常趋势，本轮采用了一个更保守的经验段模型：

1. 以细时间步 `dt = 0.05 ns` 的结果为准
2. 采用实验锚点：
   - `48 W -> 89 ohm/sq`
   - `54 W -> 82 ohm/sq`
   - `60 W -> 69 ohm/sq`
3. 对 `50/52/56/58 W` 采用线性插值得到单调 target `Rsh`
4. 在 `48–60 W` 段只反解：
   - `effective_final_inactive_activation_fraction`
5. 在该段固定：
   - `effective_final_injected_activation_fraction = 0`

对应脚本：

- `run_dual_channel_monotonic_segment_refit.py`

### 11.2 本轮结果

输出文件：

- [dual_channel_activation_model_monotonic_segment_refit.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/dual_channel_monotonic_segment_refit_48_60w_dt005_allstates/dual_channel_activation_model_monotonic_segment_refit.csv)
- [target_vs_modeled_rsh_monotonic_segment_refit.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/dual_channel_monotonic_segment_refit_48_60w_dt005_allstates/target_vs_modeled_rsh_monotonic_segment_refit.csv)
- [sheet_resistance_summary.csv](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/sheet_resistance_dual_channel_48_60w_dt005_monotonic_segment_refit/sheet_resistance_summary.csv)

对应 `Rsh` 为：

- `48 W -> 89`
- `50 W -> 86.67`
- `52 W -> 84.33`
- `54 W -> 82`
- `56 W -> 77.67`
- `58 W -> 73.33`
- `60 W -> 69`

### 11.3 这一轮结果该怎么理解

这轮结果的价值在于：

- 它把高功率段 `Rsh` 的异常非单调趋势先修正掉了
- 它明确告诉我们：旧的高功率粗步长结果不能再作为 adopted 主线

但这轮也留下了一个重要信号：

- 虽然 `Rsh` 已经恢复单调
- `effective_final_inactive_activation_fraction`
- 在 `58 W` 达到约 `0.943`
- 到 `60 W` 又回落到约 `0.868`

所以这说明：

- 当前“单调段 refit”仍然是 **经验输出层**
- 它更像是在吸收尚未显式建模的高功率物理
- 下一步仍应继续改进：
  - 界面模型
  - 高频段热模型
  - 或 initial inactive / injected 两通道的更物理电学闭合
