# Phase 3 代码解释

## 1. 新增文件

Phase 3 主要新增了两个文件：

1. `src/laser_doping_sim/phase3_stack_thermal.py`
2. `run_phase3.py`

这两个文件一起完成了：

- `PSG/Si` 双层热传导
- 分层光学热源
- 从双层热结果裁出 Si 子域
- 再调用已有扩散模块

注意：当前复用的扩散模块已经允许“未熔化时仍存在固态扩散和弱注入”，所以 Phase 3 不会再把非熔化情形硬算成绝对零掺杂。

## 2. `phase3_stack_thermal.py`

### `PSGLayerProperties`

这部分定义 PSG 层的最小热物性：

- `rho`
- `cp`
- `k`
- `thickness`

当前 PSG 不做相变，所以它保持常数热物性。

这一版还多了材料解释字段：

- `matrix_material = SiO2`
- `dopant_oxide = P2O5`
- `model_description`

这让输出文件会明确写清：当前 `PSG` 在模型里是按“高磷 SiO2 层”处理的。

### `StackOpticalProperties`

这部分定义最小光学近似所需参数：

- `surface_reflectance`
- `interface_transmission`
- `psg_absorption_depth`
- `si_absorption_depth`

它们共同决定激光能量在 `PSG` 和 `Si` 中如何分配。

### `StackDomain1D`

这里把旧的单层厚度拆成：

- `silicon_thickness`
- 时间步和总时间
- 网格数

总厚度由 `PSG thickness + silicon thickness` 自动组成。

### `_stack_liquid_fraction`

这段代码是双层模型里的关键分流：

- 在 `PSG` 区域，液相分数永远为 `0`
- 在 `Si` 区域，继续用旧 Phase 1 的焓法液相分数

这样我们就能保持“只允许 Si 熔化”。

### `_stack_apparent_heat_capacity` 与 `_stack_thermal_conductivity`

这两段代码分别给出：

- PSG 的常数 `cp` / `k`
- Si 的相变相关 `cp_eff(T)` / `k(T)`

也就是说，双层模型在数值上仍是一个统一矩阵，但物性是分层切换的。

### `layered_volumetric_heat_source`

这段代码实现了双层光学热源：

1. 先算脉冲瞬时通量 `I(t)`
2. 扣掉表面反射
3. 在 PSG 里按 Beer-Lambert 衰减生成热源
4. 剩余通量再乘界面透射
5. 在 Si 里按自己的吸收深度继续衰减

这一步是 Phase 3 相比 Phase 1 最核心的物理升级。

### `_assemble_matrix`

这部分仍然是隐式热方程矩阵，但和旧版不同的地方在于：

1. `rho * cp_eff / dt` 现在是分层的
2. `k` 现在是分层的
3. 网格界面的导热率用谐和平均

这让 PSG/Si 热阻过渡更稳健。

### `run_stack_simulation`

这是双层热模型主循环。

每个时间步会做：

1. 生成分层热源
2. 组装隐式矩阵
3. 迭代求解温度
4. 更新 Si 液相分数
5. 计算相对于 Si 表面的熔深

注意这里的 `melt_depth` 已经是“相对于 Si 表面”的深度，不包含 PSG 厚度。

### `silicon_subdomain_view`

这段代码是为了让旧 Phase 2 扩散模块还能复用：

1. 把双层结果裁成只含 Si 的深度区间
2. 把深度零点重置到 Si 表面
3. 返回和旧 `SimulationResult` 兼容的对象

这样后面的扩散模块不用立刻重写。

## 3. `run_phase3.py`

这个脚本做的事情是：

1. 组装 `PSG/Si` 双层热模型参数
2. 运行双层热求解
3. 保存热输出到 `outputs/phase3/.../thermal`
4. 抽取 Si 子域
5. 用已有 Phase 2 扩散模块重驱动扩散
6. 保存扩散输出到 `outputs/phase3/.../diffusion`
7. 再写一个总 `summary.json`

所以 Phase 3 现在已经形成了完整流水线。

## 4. 当前这版代码最值得记住的地方

1. 它保留了旧 Phase 1 / Phase 2 的接口，不会把之前的结果打坏。
2. 它先用最小双层物理把热历史拉正，再复用现有扩散模块。
3. 当前结果不熔化本身就是一个有效结论，而不是代码失败。
