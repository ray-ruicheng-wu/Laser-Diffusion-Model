# Phase 3 Physics Validation Work Report

## 1. 阶段信息

- 阶段名称：Phase 3 物理验证
- 目标：在进入 texture enhancement 之前，先验证当前 60-90W 功率扫描是否满足基本物理趋势
- 主扫描目录：[`power_scan_60_90w_dt01`](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_90w_dt01)
- 细时间步复核目录：[`power_scan_60_65w_dt005`](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/power_scan_60_65w_dt005)
- 验证输出目录：[`physics_validation_60_90w`](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/physics_validation_60_90w)

## 2. 验证方法

本轮验证采用“主功率扫描 + 低功率段细时间步复核”的组合方式，重点检查模型在功率升高时是否满足基本趋势一致性。

检查项包括：

1. fluence 是否随功率单调增加
2. stack 表面峰值温度是否非递减
3. Si 表面峰值温度是否非递减
4. 最大液相分数是否非递减
5. 最大熔深是否非递减
6. 结深是否非递减
7. chemical net donor sheet dose 是否保持合理趋势
8. source inventory 是否保持守恒一致性
9. peak P 是否可用“轮廓展宽”解释，而不是被误读成总掺杂减少
10. 60W -> 65W 低功率段是否对 `dt` 敏感

## 3. 关键图

本轮验证主要依赖以下图件：

1. [`power_vs_p_selected_depths.png`](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/physics_validation_60_90w/power_vs_p_selected_depths.png)
2. [`power_vs_near_surface_dose.png`](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/physics_validation_60_90w/power_vs_near_surface_dose.png)
3. [`power_vs_near_surface_profile_com.png`](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/physics_validation_60_90w/power_vs_near_surface_profile_com.png)

补充的结构化结果可见：

- [`physics_validation_report.md`](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/physics_validation_60_90w/physics_validation_report.md)
- [`physics_validation_summary.json`](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/physics_validation_60_90w/physics_validation_summary.json)
- [`physics_validation_table.csv`](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/outputs/phase3/physics_validation_60_90w/physics_validation_table.csv)

## 4. 主要通过项

审查线结论：当前模型通过趋势级物理验证，但 `60W -> 65W` 属于近阈值数值敏感区。

通过项如下：

1. fluence 随功率严格增加。
2. stack 表面峰值温度随功率增加。
3. Si 表面峰值温度在配置容差内保持非递减。
4. 最大液相分数随功率增加。
5. 最大熔深随功率非递减。
6. 结深随功率非递减。
7. mass balance error 保持在浮点噪声量级。
8. 细时间步复核恢复了低功率区的单调性，因此 `60W -> 65W` 的局部反转不应被当成稳健物理结论。

## 5. Caveat

本轮验证有一个明确 caveat：

- `dt = 0.1 ns` 的官方扫描在 `60W -> 65W` 段暴露出时间步敏感性。
- `dt = 0.05 ns` 的复核表明，这一低功率局部反转更像数值阈值区问题，而不是稳健的物理反转。
- 因此，低功率段应作为“近阈值敏感区”处理，不能过度解读为材料行为突变。

## 6. 与研究线文献趋势对照

研究线结论显示：`peak P` 可以非单调，但只要 `dose` 和 `junction depth` 上升，同时 profile broadening 更明显，这仍然与文献趋势一致。

本轮验证的对照结论是：

1. `peak P` 非单调是可以接受的。
2. `net donor sheet dose` 上升，说明总有效掺入没有下降。
3. `junction depth` 上升，说明 profile 确实在向更深处扩展。
4. `P(30 nm)`, `P(100 nm)`, `P(300 nm)` 以及 near-surface center-of-mass 的共同下移，支持“profile broadening”而非“掺杂减少”的解释。

因此，当前结果与研究线文献结论是对得上的：峰值不一定单调，但剂量和结深的上升更能反映真实物理趋势。

## 7. 结果是否通过

结论是：通过，但带注记。

- 通过：整体趋势级物理验证成立。
- 注记：`60W -> 65W` 段属于数值敏感区，后续正式引用时应保留 caveat。

## 8. 下一步：Texture Enhancement

在当前验证基线上，下一步建议进入 texture enhancement，而不是先改大幅度热学假设。

优先级最高的 texture 项是：

1. 有效光学增强，例如降低逃逸反射或提高吸收分数
2. 增大 PSG/Si 界面在投影面积上的有效接触面积

不建议第一步就引入过大的熔点修正或过强的经验性降阈值，因为当前验证已经说明，问题首先在于阈值附近的数值敏感性和光热耦合口径，而不是整体趋势本身。

## 9. 归档结论

这轮物理验证可以正式归档为：

- 趋势级通过
- 低功率近阈值段需要保留时间步敏感性注记
- `peak P` 的非单调不构成失效，应该结合 dose / junction / profile broadening 一起解释
- 下一步进入 texture enhancement
