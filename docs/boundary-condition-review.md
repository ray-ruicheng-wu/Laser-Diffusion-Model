# 边界条件审查报告

## 1. 这份报告回答什么问题

这份报告只回答一个具体问题：

当前模型里 `PSG -> Si` 的表面边界条件为什么写成 Robin 型，它和别人论文里常见的写法相比，到底算不算合理。

这里不讨论全部热模型，只讨论“磷从表面 source 进入硅”的数学闭合方式。

---

## 2. 我们当前模型里的边界条件到底是什么

当前实现位置：

- [phase2_diffusion.py:87](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py#L87)
- [phase2_diffusion.py:127](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py#L127)
- [phase2_diffusion.py:219](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py#L219)

当前边界可以写成：

`-D * dC/dz = h_m * (C_src,eq - C_surf)`

同时我们又加了两个约束：

1. `PSG` 不是无限供给，而是有限库存
2. `h_m` 不是独立常数，而是近似写成 `D_surface / L_tr`

也就是说，当前模型实际上是假设：

- 表面有一个“等效 reservoir”
- reservoir 和硅表面之间有一个“等效界面阻力”
- 这个阻力被压缩进一个参数 `L_tr`

所以现在这条 Robin 边界最准确的物理解释不是“真正把界面微观机理全建出来了”，而是：

它是一个把 `PSG` 溶出、超薄 `SiO2` 阻挡、界面交换、以及近表面混合效应都揉成一个 lumped resistance 的降阶闭合。

---

## 3. 别人论文里常见的边界条件大致分几类

### 3.1 常量源 / 固定表面浓度

这类最常见于传统热扩散、`POCl3` 预扩散、或者把 `PSG` 当成“足够厚、足够快补给”的近似情况。

典型口径是：

- `C(0,t) = C_s`
- 或者把表面当成 constant-source diffusion

这类写法在传统扩散教材和高浓度 P 扩散模型里很常见，用来描述“表面浓度被外部源钉住”的情形。

对应参考：

- [Crank, The Mathematics of Diffusion](https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf)
- [Velichko 2019: A comprehensive model of high-concentration phosphorus diffusion in silicon](https://arxiv.org/abs/1905.10667)

这类边界的优点是简单，缺点是会天然高估激光单脉冲条件下的表面补给能力，尤其当 source 很薄、时窗只有几十纳秒时更明显。

### 3.2 显式前驱体层 / source cell

这类更接近激光掺杂文献里的做法。思路不是直接给 `Si` 一个表面浓度，而是：

1. 在硅外面再放一个 source control volume
2. source 在激光过程中熔化、挥发或保持固态
3. 再让 source 和第一层熔融硅之间交换溶质

一个很直接的例子是：

- [Lill et al. 2017, Materials 10(2) 189](https://www.mdpi.com/1996-1944/10/2/189)

这篇文献的模型写法里，source 被做成独立单元，文中明确说明它作为有限掺杂源，并在熔融期间把掺杂扩散进第一层 Si 单元；再凝固时再通过分配系数处理溶质分布。

这类做法和我们当前 Robin 的最大区别是：

- 它不是把界面阻力揉成一个 `L_tr`
- 而是把 source 本身作为一个显式状态变量来算

### 3.3 移动界面 + 分配系数 + 表面流失

这类是更完整的激光重熔模型，常见于“先有液相，再有快速再凝固”的论文。

它们通常会同时包含：

1. 液相扩散
2. 固液界面移动
3. 再凝固分配系数 `k` 或 `k(v)`
4. 表面 out-diffusion / evaporation / ablation

对应参考：

- [OSTI / J. Appl. Phys. 2015: Phosphorus out-diffusion in laser molten silicon](https://www.osti.gov/biblio/22402853)
- [MDPI 2021: Unified Model for Laser Doping of Silicon from Doping Precursor Layers](https://www.mdpi.com/1996-1944/14/9/2322)

这一路模型的核心不是 Robin，而是：

- 在液相里解扩散
- 在移动界面上做溶质守恒
- 在再凝固处用分配系数决定“多少留下、多少被推出去”

如果还考虑 precursor 挥发或表面流失，表面还会再多一条单独的 loss 通量。

### 3.4 显式界面阻挡：`PSG/SiO2/Si`

现实里表面并不总是“PSG 直接接触 Si”。工业 `POCl3` diffusion 后，常常是 `PSG/SiO2/Si`。

这意味着界面本身就可能成为掺杂注入的瓶颈。

对应参考：

- [PNNL 2012: A model of phosphosilicate glass deposition by POCl3 to control phosphorus dose in Si](https://www.pnnl.gov/publications/model-phosphosilicate-glass-deposition-pocl3-control-phosphorus-dose-si)
- [Fraunhofer 2017: Suitability of industrial POCl3 tube furnace diffusion processes for laser doping applications](https://www.ise.fraunhofer.de/content/dam/ise/de/documents/publications/conference-paper/33-eupvsec-2017/Werner_2AV214.pdf)

这两类资料支持一个很重要的判断：

如果样品里有真实的薄 `SiO2`，那么“source 很足”并不等于“注入一定很强”，因为界面本身会抑制额外 P 进入 Si。

---

## 4. 所以，我们的 Robin 边界合理吗

结论分两层。

### 4.1 作为当前 reduced-order 模型，它是合理的

它合理的地方在于：

1. 它比硬 `Dirichlet` 表面浓度更保守，也更像有限 source
2. 它允许“未熔化时仍有弱注入”，这和 `PSG -> Si` 固态扩散文献不冲突
3. 它能自然表现 source 充足但结深不继续增加的 transport-limited 情形
4. 它在 1D、单脉冲、先做快速参数扫描的阶段非常实用

换句话说：

如果我们当前的目标是“先判断热预算、source 总量、基础 emitter 和结深之间的大趋势”，Robin 是一个可以站得住的降阶边界。

### 4.2 但它不是当前问题的最完整物理写法

它不够的地方主要有四个：

1. 它没有把 source layer 本身显式离散出来
2. 它没有把 `SiO2` 阻挡和 `PSG` 供给分开
3. 它没有写移动固液界面的溶质守恒
4. 它没有单独处理表面 out-diffusion / evaporation

所以当前 `L_tr` 的真实含义其实很重：

- 它同时代替了界面化学
- 代替了超薄氧化层阻挡
- 代替了 source 溶出速度
- 还部分代替了表面近场混合

这就导致它“能用”，但可解释性不够强。

---

## 5. 更准确地说，当前 Robin 边界处在什么物理层级

最稳妥的说法是：

当前 Robin 边界是一个“有效界面传质”模型。

它适合被解释为：

`J_in = h_int,eff * (C_src,eq - C_surf)`

其中 `h_int,eff` 不是某个单一可直接测量的微观常数，而是一个 lumped effective coefficient。

所以：

- 如果我们把它当成“降阶等效模型”，它是合理的
- 如果我们把它当成“已经忠实表示了 PSG/SiO2/Si 界面全部机理”，那就不合理

---

## 6. 对当前项目的直接建议

### 6.1 现在先不要删 Robin

现阶段不建议立刻删掉 Robin。

原因是：

1. 它已经比硬表面浓度更好
2. 它已经能表现“库存不是瓶颈，界面/时窗才是瓶颈”
3. 它很适合继续做快速扫描和工艺敏感性分析

### 6.2 但下一步升级应该怎么走

如果我们要让边界更接近真实物理，我建议优先级这样排：

1. 把当前 Robin 重解释为“有效界面阻力”，只在报告里这样表述，不再把它说成第一性原理边界
2. 在 1D 里先升级成“显式 source cell + 有限库存”
3. 再把 `PSG/SiO2/Si` 的薄 `SiO2` 阻挡单独做成一层或一个单独传输系数
4. 最后再补 moving interface + `k(v)` + surface out-diffusion

如果只做一个最小升级，我最推荐的是：

- 保留有限库存
- source 不再只剩一个 `C_src,eq`
- 而是显式加一个 source control volume
- Si 表面和 source cell 之间再交换通量

这样会比单纯 Robin 更接近文献里“前驱体层显式存在”的做法。

---

## 7. 对我们当前结果意味着什么

这次文献复核以后，当前模型结论可以这样理解：

1. 当前算到“source 很多但结深不增加”，不能简单解释成 source 不够
2. 更合理的解释是：当前有效界面阻力和有效热时窗把系统推到了 transport-limited 区间
3. 这和工业上 `PSG/SiO2/Si` 界面会抑制额外注入的认识是一致的
4. 但如果要把这种抑制从“经验结论”升级成“可解释的物理量”，就必须把界面写得更显式

---

## 8. 当前判断

一句话版本：

我们的 Robin 边界不是错的，但它更像一个合理的第一版工程近似，而不是激光重熔掺杂的最终物理边界。

更简短一点：

- 用它做趋势判断：可以
- 用它解释界面微观机理：不够
- 作为下一步升级的过渡模型：合适

---

## 9. 参考文献

- [Crank, The Mathematics of Diffusion](https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf)
- [Velichko 2019: A comprehensive model of high-concentration phosphorus diffusion in silicon](https://arxiv.org/abs/1905.10667)
- [Lill et al. 2017, Materials 10(2) 189](https://www.mdpi.com/1996-1944/10/2/189)
- [OSTI / J. Appl. Phys. 2015: Phosphorus out-diffusion in laser molten silicon](https://www.osti.gov/biblio/22402853)
- [MDPI 2021: Unified Model for Laser Doping of Silicon from Doping Precursor Layers](https://www.mdpi.com/1996-1944/14/9/2322)
- [PNNL 2012: A model of phosphosilicate glass deposition by POCl3 to control phosphorus dose in Si](https://www.pnnl.gov/publications/model-phosphosilicate-glass-deposition-pocl3-control-phosphorus-dose-si)
- [Fraunhofer 2017: Suitability of industrial POCl3 tube furnace diffusion processes for laser doping applications](https://www.ise.fraunhofer.de/content/dam/ise/de/documents/publications/conference-paper/33-eupvsec-2017/Werner_2AV214.pdf)
