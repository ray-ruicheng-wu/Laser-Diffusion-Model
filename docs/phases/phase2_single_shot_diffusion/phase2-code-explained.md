# Phase 2 代码解释

## 1. 文件一：`src/laser_doping_sim/phase2_diffusion.py`

### 顶部常量和数据结构

- `CM3_TO_M3 = 1e6`
  这是单位换算常数。扩散方程按 SI 单位工作时更自然，所以 source 面库存和积分守恒都需要它。

- `DiffusionParameters`
  这里集中放 Phase 2 的核心参数。当前除了液相前因子、活化能和 source 有效厚度以外，还包含：
  - 固相 Arrhenius 前因子 `solid_prefactor_cm2_s`
  - 固相 Arrhenius 活化能 `solid_activation_energy_ev`
  - 可选的固相扩散率下限 `solid_diffusivity_m2_s`
  - `interfacial_transport_length_m`
  它们一起决定“即使不熔化，固体里也仍然允许存在很弱的 P 扩散和注入”。

- `DiffusionResult`
  这是结果容器，保存热历史、P 浓度场、结深曲线、PSG 剩余库存和扩散参数。

### `liquid_phosphorus_diffusivity_m2_s`

这段代码实现液相 P 扩散系数：

`D_l = D0 * exp(-Ea / k_B T)`

实现细节：

1. 先把 `cm^2/s` 转成 `m^2/s`
2. 把 `eV` 转成 `J`
3. 再按 Arrhenius 形式计算

### `solid_phosphorus_diffusivity_m2_s`

这段代码是这次新增的关键之一。它把固相 P in Si 的扩散也写成 Arrhenius 形式：

`D_s = D0_s * exp(-Ea_s / k_B T)`

如果用户额外给了一个 `solid_diffusivity_m2_s` 下限，它还会把这个值当成保底下限，防止极端参数下完全退化。

### `effective_diffusivity_m2_s`

这段代码把固相和液相扩散率按液相分数混合：

`D_eff = D_solid * (1 - f_l) + D_l * f_l`

物理意义是：

- 表面没熔时，P 仍按固相 Arrhenius 扩散，只是非常慢
- 一旦熔化，扩散率快速抬升

### `_harmonic_mean`

这是这次修正的关键之一。它把相邻网格点之间的界面扩散率从旧版的“算术平均”改成了“谐和平均”。

为什么要这样做：

- 液相和固相的扩散率能差很多个数量级
- 这类高反差问题如果直接用算术平均，会把界面通量算得过大
- 谐和平均更接近“串联阻力”的物理图像

### `_surface_reservoir_concentration_m3`

这段代码把 PSG 剩余面库存换算成一个等效的 source 平衡浓度。

做法是：

1. 用 `inventory / source_effective_thickness` 换算成等效体浓度
2. 再和设定的 `PSG P` 浓度上限、全局浓度上限取最小值

这保证了 source 既不会凭空无限大，也不会超过设置的 PSG 上限。

### `_assemble_diffusion_matrix`

这段代码负责组装隐式扩散方程的稀疏矩阵。

关键变化：

1. 表面不再区分 `dirichlet/neumann` 两个模式
2. 统一改成“零通量 + 可选传质项”的形式
3. 表面行现在多了 `surface_exchange` 项

也就是说，矩阵第一行现在对应的是：

`-D ∂C/∂z = h_m (C_eq,src - C_surf)`

而不是以前那种直接钉死 `C(0)`。

### `junction_depth_m`

旧版只返回“最后一个 `C >= C_background` 的网格点”，这会让结深被网格锁死。

现在这里改成：

1. 先找到最后一个还高于背景浓度的点
2. 再找它后面第一个低于背景浓度的点
3. 在两点之间做线性插值

这样读出来的结深就更像真正的浓度交点。

### `run_diffusion`

这是整个 Phase 2 的主循环，也是这次改动最多的地方。

#### 初始化

1. 从 Phase 1 热结果里拿到深度、时间、温度场和液相分数
2. 初始化 P 浓度场为零
3. 根据 `PSG P 浓度 * source 有效厚度` 算出初始面库存
4. 把基底 `Ga` 背景浓度转换成内部计算用的单位

#### 每一个时间步

每一步会做下面这些事：

1. 取上一步的 P 分布 `previous`
2. 根据当前温度和液相分数计算 `D_eff`
3. 只要 PSG 还有库存，就计算表面 source 平衡浓度
4. 再用当前表面有效扩散率计算：
   - 当前 source 等效平衡浓度
   - `surface_exchange_velocity = D_surface / interfacial_transport_length`
5. 组装隐式扩散矩阵
6. 在右端项里加入表面 Robin 边界贡献
7. 解线性方程得到新的 P 分布
8. 把负浓度裁掉，并限制在全局上限以内
9. 用 `Integral C dz` 直接算出当前 Si 内总 P 量
10. 由总量守恒反算 PSG 剩余库存
11. 计算当前结深

这一步里最关键的新点是：

- 库存不再按“本步正向增量”更新
- 而是按“source + Si 总量守恒”直接反推
- 表面 source 不再要求“先熔化才开启”
- 非融化条件下也允许极弱的固态注入

这就是为什么这次质量守恒误差能从之前的明显失衡，降到现在的浮点误差量级。

### `_summary`

这里会从最终结果里提取摘要指标。除了旧有的峰值浓度、最终结深和库存以外，现在还新增了：

- `final_silicon_inventory_atoms_m2`
- `final_mass_balance_error_atoms_m2`

这两个量就是专门为这次公式复核和数值审查准备的。

### `save_outputs`

这段代码把结果写到磁盘，包括：

- `phase2_results.npz`
- `summary.json`
- `p_concentration_heatmap.png`
- `final_p_profile.png`
- `junction_depth_vs_time.png`
- `source_inventory_vs_time.png`

## 2. 文件二：`run_phase2.py`

### 命令行参数

这个脚本把 Phase 1 和 Phase 2 的参数放到同一个入口里。

这次新增的关键参数是：

- `--interfacial-transport-length-nm`

它直接控制 Robin 边界里的界面传质强度：

- 数值越小，source -> molten Si 的通量越强
- 数值越大，source -> molten Si 的通量越弱

### 主流程

脚本做三件事：

1. 先跑 Phase 1 热模型
2. 用热历史驱动 Phase 2 扩散
3. 保存图表并打印摘要

现在打印结果里还会直接给出最终质量守恒误差，方便快速检查这一版是否数值上又跑偏了。

另外，命令行现在也支持：

- `--solid-prefactor-cm2-s`
- `--solid-activation-energy-ev`

用于显式控制固相 Arrhenius 扩散。

## 3. 这版代码最值得记住的地方

1. 表面 source 现在是“有限库存 + Robin 通量边界”，不是硬 Dirichlet。
2. PSG 库存现在按总量守恒反算，不会再无端丢质量。
3. 液/固界面通量采用谐和平均，避免高估跨界面扩散。
4. 结深读取改成了插值，不再直接受一个网格点控制。
5. 非融化条件下不再被强制压成零掺杂，而是保留固态扩散和弱注入。

## 4. 当前还没有实现的部分

这版代码仍然没有显式做：

1. 液相对流
2. 移动固液界面溶质守恒
3. `k(v)` 型 partition / solute trapping
4. PSG 显式玻璃层

所以它已经比旧版正确得多，但还不是最终研究版。
