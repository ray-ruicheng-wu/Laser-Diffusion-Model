# 文书老哥记忆文件

## 1. 角色

`文书老哥` 负责：

1. 持续搜索和整理激光掺杂、PSG、P in Si、Ga background 相关的一手或高质量资料。
2. 优先给出控制方程、边界条件、材料参数范围、物理极限和文献出处。
3. 不直接给最终工艺结论，优先提供“公式是否站得住”和“参数是否有来源”。

## 2. 当前项目范围

当前项目是：

- 激光诱导硅掺杂模拟
- 表面 source 为 `PSG`
- 掺杂元素为 `P`
- 基底背景掺杂为 `Ga`
- 当前先做 `1D depth-only`
- 激光已知条件中明确提到：
  - `532 nm`
  - `500 kHz`

新增统一口径：

- `PSG` 在当前项目里统一解释为 `phosphosilicate glass`
- 组成上按 `P2O5-SiO2 glass` 理解
- 当前最小实现里，把它近似成“一层高磷 SiO2”
- 若文献里出现 `PSG/SiO2/Si`，默认先理解为现实堆栈；当前模型若未显式分层，则视为把超薄 `SiO2` 夹层并入有效玻璃层

## 3. 当前已确认的研究结论

### 3.1 热模型侧

1. `532 nm` 裸硅下，吸收深度不应继续用早期演示值 `80 nm`。
2. 以裸硅公开光学数据做基线时，吸收深度更接近 `1 um` 量级。
3. 在裸硅 `532 nm` 基线下，当前默认单脉冲条件不会自然得到熔化。
4. 真实工艺更可能需要 `PSG/Si` 双层光学和热学，而不是把表面继续当作裸硅。
5. `PSG` 的更稳妥项目口径不是“未知覆盖层”，而是“高磷 `SiO2` 玻璃层”。

### 3.2 掺杂模型侧

1. 当前 Phase 2 的最小控制方程先采用：
   `∂C/∂t = ∂/∂z [ D(T, f_l) ∂C/∂z ]`
2. 若忽略液相流动，可以把它视为 1D Fick 扩散的最小模型。
3. `PSG -> molten Si` 的表面边界，优先应是：
   `有限库存 + Robin 通量/传质边界`
   而不应默认是硬 `Dirichlet` 表面浓度。
4. 对激光重熔/再凝固问题，后续高阶模型应关注：
   - `partition coefficient k`
   - `k(v)` 或 solute trapping
   - moving interface solute balance
5. 当前模型尚未显式包含液相对流、界面移动和再凝固分凝。

## 4. 当前默认参数口径

这些值目前是项目默认输入，不代表最终标定值：

| 参数 | 默认值 | 单位 | 备注 |
| --- | ---: | --- | --- |
| `P in PSG` | `2.0e21` | `cm^-3` | 表面 P source 浓度上限 |
| `Ga in Si` | `1.0e16` | `cm^-3` | 基底背景浓度 |
| `D_solid` | `1.0e-18` | `m^2/s` | 固相占位扩散率 |
| `D0_liquid` | `1.4e-3` | `cm^2/s` | 液相 P 扩散前因子 |
| `Ea_liquid` | `0.183` | `eV` | 液相 P 扩散活化能 |
| `source_effective_thickness` | `100` | `nm` | PSG 有限库存等效厚度 |
| `interfacial_transport_length` | `100` | `nm` | 界面传质长度 |

## 5. 当前已确认的实现修正

文书老哥在阅读资料时，应默认当前代码已经完成以下修正：

1. 表面边界从硬 `Dirichlet` 改成了 Robin 通量边界。
2. PSG 库存按总量守恒反算，而不是按单步正增量扣减。
3. 液/固界面扩散率离散使用谐和平均。
4. 结深采用与 `Ga` 背景浓度交点的线性插值。

如果以后搜索到与这四项矛盾的强证据，应明确指出是哪一项、为什么矛盾、文献依据是什么。

## 6. 当前主要不确定性

1. `PSG/Si` 双层热模型还没有完成。
2. Phase 1 的熔深对 `nz` 和 `dt` 仍然敏感。
3. `interfacial_transport_length` 目前是待标定参数。
4. 尚未加入移动界面、`k(v)`、再凝固分凝和俘获。
5. `500 kHz` 当前只用于功率到单脉冲能量的换算，不作为热积累主线。

## 7. 文书老哥后续查资料时的优先级

优先顺序如下：

1. `PSG/Si` 在 `532 nm` 下的光学参数和热学参数
   - 特别关注：文献是把 PSG 写成 `P2O5-SiO2 glass`、`P-rich SiO2`，还是显式 `PSG/SiO2/Si`
2. `P` 在液态 Si 中的扩散系数与温度关系
3. `PSG -> molten Si` 的界面传质/有限源模型
4. `P` 在快速凝固 Si 中的 `partition coefficient`、`solute trapping`、`k(v)`
5. `30 W @ 500 kHz` 与光斑尺寸对应的单脉冲 fluence 换算与标定

## 8. 已使用/可信的参考入口

1. Green 2008 silicon optical parameters:
   [PDF](https://subversion.xray.aps.anl.gov/AGIPD_TCAD/PyTCADTools/Attenuation/Silicon_absorption_coeff_visible_photon.pdf)
2. CERN silicon general properties:
   [Link](https://ssd-rd.web.cern.ch/Data/Si-General.html)
3. Crank, The Mathematics of Diffusion:
   [PDF](https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf)
4. OSTI / J. Appl. Phys. phosphorus out-diffusion in laser molten silicon:
   [Link](https://www.osti.gov/biblio/22402853)
5. MDPI 2021 unified model for laser doping:
   [Link](https://www.mdpi.com/1996-1944/14/9/2322)
6. Fraunhofer PSG laser doping references:
   [1991](https://publica.fraunhofer.de/entities/publication/bf765ea3-bd57-4a9a-b8ff-c27be293d951)
   [2011](https://publica.fraunhofer.de/entities/publication/a5194b29-eaed-452c-af70-a00a67bdb073)

## 9. 使用约定

以后只要继续调用 `文书老哥`，主线程应先要求它：

1. 先阅读本文件。
2. 再阅读 `docs/formula-reference-register.md`。
3. 只补充新的资料，不重复已经确认的内容。
4. 明确区分：
   - 文献直接支持
   - 合理推断
   - 尚未确认

文书老哥每次回传资料时，优先按下面格式输出：

1. 发现了哪个“缺少的数学模型”
2. 推荐公式
3. 推荐边界/界面条件
4. 适用前提
5. 引用文献链接
6. 建议登记到 `formula-reference-register.md` 的 `F-ID / Ref-ID`

## 10. 本次存档时间

- `2026-04-07`

## 11. 新的固定流程：每次结果生成后都要做文献对标

从现在开始，只要主线程生成了任何新的模拟结果，研究线都必须执行下面这套固定动作：

1. 读取最新结果的：
   - `summary.json`
   - 关键图表
   - 对应输出目录
2. 把当前结果和已知文献中的典型结果做对比：
   - 峰值表面温度
   - 熔深
   - 峰值 `P` 浓度
   - 结深
   - 剂量或 source 消耗
3. 专门思考三类问题：
   - 结果有没有明显违背文献常识或物理极限
   - 如果差距很大，更像是哪类模型缺失
   - 有没有值得立刻尝试的改进项
4. 回传时必须明确写出：
   - `对比对象文献`
   - `一致之处`
   - `可疑之处`
   - `最可能的误差来源`
   - `建议改进项`
   - `这些改进项对应的公式和文献`
5. 如果研究线判断“结果可能有错”，必须明确标成：
   - `疑似错误`
6. 如果研究线认为“可以继续改进”，必须明确区分：
   - `立即值得改`
   - `后续再改`

研究线的默认职责现在是：

- `查资料 + 结果对标 + 找可疑点 + 提改进建议`

## 12. 长时研究与可中断汇报

从现在开始，研究线允许做长时间、持续性的资料研究，不需要每次都在短时间内停止。

但主线程有一个新的调度规则：

1. 如果主线程暂时不需要阶段结论，研究线可以持续研究下去。
2. 如果主线程需要阶段性判断、文献对标结论或改进建议，可以直接中断研究线。
3. 被中断时，研究线必须先立即给出“当前最好的阶段性结论”，即使研究还没彻底结束。
4. 阶段性结论给出后，研究线默认应继续之前的研究，而不是把任务视为结束。
5. 阶段性结论里要明确区分：
   - 已确认
   - 当前最可能
   - 仍待继续查证
