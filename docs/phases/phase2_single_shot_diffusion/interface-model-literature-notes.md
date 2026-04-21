# 界面模型文献笔记

## 1. 当前 `effective interface transport length` 是什么

当前代码里，界面交换速度写成：

\[
v_{\mathrm{ex}} = \frac{A_{\mathrm{factor}} D_{\mathrm{surface}}}{L_{\mathrm{int}}}
\]

对应实现见：

- [phase2_diffusion.py](C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py)

更完整地说，当前界面注入是：

\[
J_{\mathrm{in}}
=
H(f_l-f_{\mathrm{th}})
\frac{A_{\mathrm{factor}} D_{\mathrm{surface}}}{L_{\mathrm{int}}}
\max(0, C_{\mathrm{src}}-C_{\mathrm{surf}})
\]

并且还会被有限 source inventory 限流。

这里的 `L_int` 当前应读成：

- **effective interface transport length**
- 不是实测真实氧化层厚度
- 是把 `PSG / SiO2 / Si` 界面的综合传质阻力压缩成一个参数

## 2. 100 nm 有没有直接文献依据

当前结论：**没有直接文献支持“100 nm 就是真实界面层厚度”。**

它当前只是：

- 一个保守的
- 数值上稳定的
- 便于扫描灵敏度的

经验等效参数。

更准确地说，它只是：

- 界面阻力的 lumped closure

不是：

- 已被确认的物理氧化层厚度

## 3. 文献真正支持什么

### 3.1 PSG 与 Si 之间存在薄 `SiO2` 阻挡层

1. Werner et al. 2017  
   [Fraunhofer ISE PDF](https://www.ise.fraunhofer.de/content/dam/ise/de/documents/publications/conference-paper/33-eupvsec-2017/Werner_2AV214.pdf)

   支持点：

   - `PSG/SiO2/Si` stack 是真实存在的工艺对象
   - 更薄的 intermediate oxide 与更强的 laser doping 相关
   - 量级更接近几纳米到十几纳米，而不是 `100 nm`

2. Jäger et al. 2020  
   [ISFH abstract page](https://isfh.de/en/publications/advanced-chemical-model-for-the-diffusion-mechanism-of-phosphorus-into-the-silicon-wafer-during-pocl3-diffusion)

   支持点：

   - `O2` drive-in 会在 `PSG` 和 Si 之间长出 interfacial `SiO2`
   - 该层会限制 P 向 Si 的扩散
   - 这是一个明确的“界面阻挡”物理

3. Messmer et al. 2020  
   [Fraunhofer ISE 2020 PDF](https://www.ise.fraunhofer.de/content/dam/ise/de/documents/publications/conference-paper/37th-eupvsec-2020/Messmer_2CV144.pdf)

   支持点：

   - thinner intermediate oxide layers correlate with enhanced laser-induced `Rsh` reduction
   - 文中还讨论了高比例 electrically inactive phosphorus 的后续激活

### 3.2 P 在 `Si/SiO2` 界面会 pile-up，分配 / segregation 不能忽略

1. Mustafa Radi dissertation, TU Wien  
   [Segregation effects at Si/SiO2 interface](https://www.iue.tuwien.ac.at/diss/radi/node24.html)

   支持点：

   - `P` 和 `As` 在 `Si/SiO2` 界面会出现 pile-up
   - 界面处应考虑 segregation coefficient
   - 可以用 `m = C_si / C_ox` 的界面平衡口径

2. Feldmann et al. 2019  
   [ScienceDirect abstract / DOI 10.1016/j.solmat.2019.109978](https://www.sciencedirect.com/science/article/abs/pii/S0927024819303071)

   支持点：

   - 研究了 dopant 从 `poly-Si` 通过 `SiOx` 进入 `c-Si`
   - 结论指出 phosphorus piles up at the `poly-Si/SiOx` interface
   - 文章明确提到：segregation coefficient 和 `SiOx` 中 diffusivity 被确定

虽然这不是 laser doping 论文，但它和我们想建的“source / oxide barrier / c-Si”界面模型非常接近。

### 3.3 更合理的 laser precursor 模型是显式 source，不是单靠一个 `L_int`

1. Lill et al. 2017  
   [Materials 2017](https://www.mdpi.com/1996-1944/10/2/189)

   支持点：

   - precursor layer 应显式进入模型
   - melt threshold 对结果极其敏感

2. Hassan et al. 2021  
   [Materials 2021](https://www.mdpi.com/1996-1944/14/9/2322)

   支持点：

   - 统一 precursor laser doping 框架
   - 更自然的写法是 source layer + thermal history + dopant transport

## 4. 建议替代 `L_int` 的界面模型

### 4.1 最小升级版：显式 oxide barrier + segregation

推荐把当前界面交换写成：

\[
J_{\mathrm{int}}
=
H(f_l-f_{\mathrm{th}})
\frac{D_{\mathrm{ox}}^{\mathrm{eff}}(T)}{t_{\mathrm{ox}}}
\left(
C_{\mathrm{src,ox}} - \frac{C_{\mathrm{si}}}{m}
\right)
\]

其中：

- `t_ox`：真实或等效中间氧化层厚度
- `D_ox^eff(T)`：P 在 oxide/PSG 中的有效扩散系数
- `m = C_si / C_ox`：Si/oxide 界面 segregation coefficient

这比当前的

\[
\frac{D_{\mathrm{surface}}}{L_{\mathrm{int}}}
\]

更物理，因为它把：

- oxide thickness
- oxide diffusivity
- segregation

分开了。

### 4.2 更稳妥的工程版：串联阻力模型

如果还想保留 lumped closure，但比单个 `L_int` 更合理，可以写成：

\[
J_{\mathrm{int}}
=
H(f_l-f_{\mathrm{th}})
\frac{C_{\mathrm{src,eq}}-C_{\mathrm{si}}}
{
\frac{1}{k_{\mathrm{diss}}}
+
\frac{t_{\mathrm{ox}}}{D_{\mathrm{ox}}^{\mathrm{eff}}}
+
\frac{1}{k_{\mathrm{mix}}}
}
\]

意思是把界面阻力拆成：

- source 溶解 / 释放阻力
- oxide 穿透阻力
- melt-side 混合阻力

这会比单个 `L_int` 更有解释力，也更容易和文献参数对齐。

## 5. 当前推荐

当前我建议：

1. **不要再把 `100 nm` 当成真实物理厚度来解释**
2. 当前结果里可以继续把它读成：
   - “界面限流的经验等效长度”
3. 下一轮真正升级时，优先做：
   - `explicit source cell + oxide thickness + segregation coefficient`
4. 如果想先保守一点，就做：
   - `series resistance interface model`

## 6. 一句话结论

当前 `interfacial_transport_length = 100 nm` 没有直接的真实厚度文献依据；  
更好的下一代界面模型，应基于：

- 薄 `SiO2` 阻挡层
- `P` 在 `Si/SiO2` 界面的 segregation / pile-up
- 显式 source layer

而不是继续把所有界面物理都塞进一个单独的 `L_int` 参数里。
