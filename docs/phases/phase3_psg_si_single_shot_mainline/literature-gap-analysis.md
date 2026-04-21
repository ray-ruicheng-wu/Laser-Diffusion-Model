# 当前结果与论文结果的差距分析

## 1. 当前模型的对照基线

这里先拿当前修正后的默认案例作为比较对象：

- 热模型输出：
  - 峰值表面温度：`1807 K`
  - 最大熔深：`128.3 nm`
  - 熔融窗口：`31.2 ns` 到 `57.0 ns`
- 掺杂模型输出：
  - 最终峰值 `P` 浓度：`5.162e20 cm^-3`
  - 最终结深：`143.7 nm`
  - 最终进入 Si 的总 P 剂量：`1.611e15 cm^-2`
  - 初始 source 面库存：`2.0e16 cm^-2`

注意：这仍然是“单脉冲 + 1D + 当前 Phase 1 热历史”结果，不是 `532 nm + PSG/Si + 多脉冲扫描` 的最终工艺模型。

## 2. 论文中的几个关键参考点

### 2.1 最接近我们问题设定的参考

Fraunhofer 2018 的 LDSE 工作直接研究了：

- `532 nm` 绿光纳秒激光
- `60–100 kHz`
- 从 `POCl3` 扩散后形成的 `PSG/SiO2` 堆栈向 Si 做局部激光掺杂

这篇工作的几个关键量是：

- 参考发射极表面浓度约 `Nsurf ≈ 4e19 cm^-3`
- 激光后典型表面浓度约 `4e19–5e19 cm^-3`
- 掺杂轮廓深度从约 `0.3 um` 增加到约 `0.5–0.7 um`
- 典型磷剂量约 `D ≈ 2e15 cm^-2`
- 局部片阻可降到约 `21–49 Ohm/sq`

### 2.2 PSG 剂量参考

Fraunhofer 2017 的 PSG/SiO2 堆栈研究给出：

- `PSG/SiO2` 堆栈总磷剂量约 `1.7e15 cm^-2`

这个量对我们特别重要，因为它能帮助判断当前 source 假设是不是过重。

### 2.3 更宽松的发射极参考

Fraunhofer 2017 的低掺杂磷发射极工作给出：

- `Nsurf ≈ 3.3e19–1.2e20 cm^-3`
- 结深约 `350 nm`

这不是激光 PSG 掺杂的直接同类实验，但可以作为“工业磷发射极轮廓”的宽松参考。

## 3. 和论文结果的直接比较

| 量 | 当前模型 | 论文参考 | 差距判断 |
| --- | ---: | ---: | --- |
| 峰值/表面近表面 `P` 浓度 | `5.162e20 cm^-3` | `4e19–5e19 cm^-3` | 当前高约 `10–13x` |
| 结深/轮廓深度 | `143.7 nm` | `0.5–0.7 um` | 当前浅约 `3.5–4.9x` |
| 最终进入 Si 的剂量 | `1.611e15 cm^-2` | `~2e15 cm^-2` | 当前低约 `20%`，量级接近 |
| 初始 source 剂量 | `2.0e16 cm^-2` | `~1.7e15 cm^-2` PSG stack dose | 当前高约 `11.8x` |
| 最大熔深 | `128.3 nm` | 文献轮廓深度常达 `300–700 nm` | 当前热影响深度偏浅 |

## 4. 最重要的观察

当前结果最有意思的一点是：

- `总剂量` 已经和文献量级比较接近
- 但 `轮廓太尖、太浅`

也就是说，我们现在不是“完全没把磷打进去”，而是把相近量级的磷压得过于靠近表面了。

这通常意味着：

1. 热历史太浅
2. 当前 `30 W @ 500 kHz @ 95 um square flat-top` 已可换算为单脉冲 `fluence`，但局部有效 `fluence` 仍可能受堆栈光学和扫描重叠影响
3. 表面供源和界面传质还偏强，导致近表面堆积过重

## 5. 为什么会出现这种差距

### 5.1 当前模型是单脉冲点模型

Fraunhofer 2018 的同类工作是：

- 线扫描
- 重叠脉冲
- `60–100 kHz`

而我们当前默认是：

- 单点
- 单脉冲
- 没有扫描重叠

这说明文献工艺路径和我们当前单脉冲固定点模型并不完全同构，因此对照时要特别小心。

### 5.2 当前热模型还不是 `PSG/Si` 双层

我们现在 Phase 1 默认热源仍然是演示级单层 Si 近似，不是：

- `532 nm`
- `PSG/SiO2/Si` 多层光学
- 分层热传导

这会直接影响熔深和熔融时间。

### 5.3 当前缺少 moving interface / partition / trapping

当前 Phase 2 还没有显式做：

- moving interface solute balance
- `k(v)` / partition coefficient
- resolidification trapping

这些项会改变掺杂轮廓形状，尤其是表面峰值和熔深附近的轮廓转折。

### 5.4 当前 source 假设偏重

虽然最后进入 Si 的剂量并不夸张，但当前初始 source 剂量设成了：

- `2.0e16 cm^-2`

而文献里可参考的 PSG stack 总剂量是：

- `1.7e15 cm^-2`

这说明我们的 source 上限假设偏大很多，只是当前 Robin 边界没有把这些剂量全部注入进去。

## 6. 当前最合理的判断

如果只问“和论文比，我们现在差在哪”：

1. `总剂量` 不算离谱，已经接近文献量级。
2. `表面浓度` 明显过高。
3. `结深/轮廓深度` 明显偏浅。
4. 差距最大的一层原因更像是 `热历史和工艺路径没建对`，而不只是扩散系数一个参数取错。

换句话说，下一步最值得优先补的不是继续微调 `D_l`，而是：

1. `PSG/Si` 双层热模型
2. 在已测 `95 um square flat-top` 下，不同平均功率工作点对应的单脉冲 `fluence`
3. moving interface + `k(v)`

## 7. 目前最值得追的三个问题

1. 真实 `PSG/SiO2` 堆栈下，在 `532 nm` 和给定脉冲条件下，熔深到底能不能从 `~0.13 um` 推到 `~0.5 um` 量级？
2. 在已测 `500 kHz / 95 um square flat-top` 前提下，真实堆栈光学和扫描路径会把有效 `fluence` 修正到什么程度？
3. 现在的高表面峰值，是主要来自 source 假设过重，还是来自缺少再凝固分凝/俘获？

## 8. 参考文献

- [Fraunhofer 2018: Laser-Doped Selective Emitter - Process Development and Speed-Up](https://publica.fraunhofer.de/entities/publication/899b393b-7f4c-4f3b-a184-8c76887b3e53)
- [Fraunhofer PDF of the 2018 LDSE paper](https://publica.fraunhofer.de/bitstreams/b35a6dac-961c-45c8-abb3-98c245d14428/download)
- [Fraunhofer 2017: Structure and composition of phosphosilicate glass systems formed by POCl3 diffusion](https://publica.fraunhofer.de/entities/publication/15920d2c-9879-4367-92d7-c5ecf681b3fc)
- [Fraunhofer 2017: Challenges for lowly-doped phosphorus emitters in silicon solar cells with screen-printed silver contacts](https://publica.fraunhofer.de/entities/publication/edd2cf44-a818-401f-8ab1-648c338a98ed)
- [Fraunhofer 2010: Industrialization of the laser diffusion process](https://publica.fraunhofer.de/entities/publication/4415978d-450f-475d-808e-de11f3d83db9)
