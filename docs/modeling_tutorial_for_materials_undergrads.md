---
tags:
  - tutorial
  - laser-doping
  - materials
  - undergrad
  - obsidian
---

# 激光 PSG 磷掺杂建模教程

## 这份教程是写给谁的

这份教程默认你是：

1. 材料类本科生
2. 学过一点传热、扩散、半导体基础
3. 只会基础 Python

它的目标不是让你背代码，而是让你真正学会下面这件事：

> 如何把一个真实材料工艺问题，逐步变成一个能跑、能解释、能验证的数值模型。

当前项目的对象是：

- `532 nm` 绿光激光
- 表面有 `PSG` 作为磷源
- Si 基底里有 `Ga` 背景掺杂
- 激光照射后会升温、可能部分融化、并诱发 P 扩散

这份教程会从 4 个层次讲：

1. 先讲物理问题
2. 再讲数学公式
3. 再讲怎么把公式写成代码
4. 最后讲怎么检查结果是否可信

---

# Part 1：先把物理问题讲明白

## 1. 工艺过程到底发生了什么

我们关心的是一种表面源激光掺杂工艺。

把它想成下面这个顺序：

1. 表面先有一层 `PSG`
2. `PSG` 里含有很多 P
3. 激光脉冲打到样品表面
4. 表层快速升温
5. Si 可能进入部分融化或完全融化
6. P 在高温甚至液相 Si 里快速扩散
7. 最后形成新的 `P(z)` 掺杂轮廓

这件事里有 3 个最核心的物理模块：

1. 热
2. 相变
3. 扩散

所以我们的模型也按这 3 件事来建。

---

## 2. 为什么这个问题不能一上来就“全都建”

很多人第一次做建模，会想一步到位：

- 真实纹理
- 真正 2D/3D
- 真正移动界面
- 真正复杂边界

这样想没有错，但对于入门很危险。

因为你会同时面对：

1. 物理公式是否选对
2. 材料参数是否合理
3. 数值算法是否稳定
4. 几何离散是否正确

只要其中一个错了，最后结果都可能不可信，而且你很难知道到底错在哪。

所以这个项目现在用的是一种非常适合学习和入门的路线：

1. 先做 `1D` 深度方向模型
2. 先把热链条跑通
3. 再把扩散并进去
4. 再做扫描和验证
5. 然后先并入第一版纹理增强
6. 最后才往 FEM 和更复杂几何走

这就是为什么当前项目虽然还不是最终 FEM 版，但非常适合学习。

---

# Part 2：项目代码结构怎么读

当前最重要的代码文件有 6 个：

- [phase1_thermal.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py)
- [phase2_diffusion.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py)
- [phase3_stack_thermal.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py)
- [run_phase3.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3.py)
- [run_phase3_power_scan.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3_power_scan.py)
- [run_phase3_physics_validation.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3_physics_validation.py)

最简单的理解方式是：

- `phase1_thermal.py`
  负责“加热”
- `phase2_diffusion.py`
  负责“P 怎么进去”
- `phase3_stack_thermal.py`
  负责“把裸 Si 热模型升级成 PSG / Si 堆栈”
- `run_phase3.py`
  负责“跑一个算例”
- `run_phase3_power_scan.py`
  负责“扫很多功率点”
- `run_phase3_physics_validation.py`
  负责“判断这些结果是不是基本靠谱”

你如果要读代码，推荐顺序是：

1. 先看 `run_phase3.py`
2. 再看 `phase3_stack_thermal.py`
3. 再看 `phase2_diffusion.py`
4. 最后看扫描和验证脚本

原因很简单：

- 入口脚本会告诉你模型有哪些输入
- 热模型先决定温度历史
- 扩散模型再吃这个温度历史

---

# Part 3：先学热模型

## 1. 激光怎么进入模型

实验里你常常拿到的是：

- 平均功率 `P_avg`
- 重复频率 `f`
- 光斑尺寸

但热模型真正要用的是：

- 单脉冲能量
- fluence

所以第一步永远是换算：

$$
E_{pulse}=\frac{P_{avg}}{f}
$$

$$
F=\frac{E_{pulse}}{A_{spot}}
$$

其中：

- `E_pulse`：单脉冲能量
- `A_spot`：光斑面积
- `F`：单脉冲 fluence

这个关系在当前项目里由：

- [run_phase3.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3.py)
- [run_phase3_power_scan.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3_power_scan.py)

来完成。

为什么这一小步很重要：

- 如果你 fluence 算错了，后面整个热史都会错
- 很多实验“功率一样但结果不同”，本质上是 spot area 不同

这个物理关系本身是最基础的能量定义，不需要特别文献支持，但后面关于 `532 nm` 的吸收和反射参数要靠文献校准 [R2]。

---

## 2. 热方程长什么样

当前 1D 热模型的核心是：

$$
\rho c_p^{app}(T)\frac{\partial T}{\partial t}
=
\frac{\partial}{\partial z}
\left(
k(T)\frac{\partial T}{\partial z}
\right)
+
Q(z,t)
$$

这个方程可以这样理解：

- 左边：材料温度随时间变化要吃掉多少热
- 右边第一项：热会沿深度方向传导
- 右边第二项：激光在材料里注入热

这里最重要的量有 4 个：

- `rho`：密度
- `c_p^{app}`：表观热容
- `k(T)`：热导率
- `Q(z,t)`：体热源

在代码里你会看到这些函数：

- `apparent_heat_capacity(...)`
- `thermal_conductivity(...)`
- `volumetric_heat_source(...)`

都在 [phase1_thermal.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py) 里。

这个热传导方程属于经典热学基础，也和数值热处理、焊接、相变模拟里最常见的框架一致 [R4][R5]。

---

## 3. 为什么这里要用表观热容

如果没有相变，普通热容就够了。  
但现在 Si 可能会熔化，所以还要处理 latent heat。

当前项目采用的是“表观热容 / 焓法”思路：

$$
c_p^{app}(T)=c_p(T)+\text{latent heat contribution}
$$

它的思想是：

- 不显式追踪一条很尖的固液界面
- 而是把 latent heat 分布到一小段相变温区里

这为什么是一个好选择：

1. 对初学者更容易理解
2. 数值上比较稳
3. 很适合先做 1D 扫描

这类 fixed-grid enthalpy / apparent heat capacity 方法是相变数值模拟里很经典的一条路线 [R4][R5]。

---

## 4. 激光热源在深度上怎么分布

在最基础的一维模型里，我们把激光吸收写成 Beer-Lambert 形式：

$$
Q(z,t)=\frac{(1-R)q''(t)}{\delta}\exp\left(-\frac{z}{\delta}\right)
$$

其中：

- `R`：表面反射率
- `delta`：吸收深度
- `q''(t)`：表面热流包络

这个式子的意义很简单：

- 越靠近表面，吸收越强
- 越往下，吸收越弱

当前 `532 nm` 下 Si 的反射与吸收深度参考了 Green 的光学参数整理 [R2]。

---

## 5. 热模型的数值算法到底怎么做

这是很多初学者最怕的一块，但其实没有那么难。

### 第一步：把连续深度切成网格

把 Si 厚度离散成很多深度节点：

$$
z_0,z_1,z_2,\dots,z_{N-1}
$$

把时间离散成很多时刻：

$$
t^0,t^1,t^2,\dots
$$

于是连续函数 `T(z,t)` 就变成了网格值 `T_i^n`。

### 第二步：把导数换成差分

例如时间导数写成：

$$
\frac{\partial T}{\partial t}
\approx
\frac{T_i^{n+1}-T_i^n}{\Delta t}
$$

热传导项写成左右热流差。

### 第三步：每个节点得到一条代数方程

最后每个节点会得到形如：

$$
a_iT_{i-1}^{n+1}+b_iT_i^{n+1}+c_iT_{i+1}^{n+1}=r_i
$$

的方程。

把所有节点拼起来，就得到一个矩阵方程：

$$
\mathbf{A}\mathbf{T}^{n+1}=\mathbf{b}
$$

代码里解的其实就是这个。

---

## 6. 为什么用隐式法，不用显式法

显式法当然更直观，但这个问题里它不划算。

原因是：

1. 纳秒热扩散很快
2. 相变很 stiff
3. 网格又比较细

显式法为了稳定，通常要求非常小的 `dt`。  
所以当前项目选择：

- 隐式时间离散
- 稀疏矩阵求解

这样更稳，也更适合批量扫描。

这也是工程模拟里很常见的做法 [R4][R5]。

---

# Part 4：再学扩散模型

## 1. 扩散方程怎么写

当前 P 扩散模型的核心是：

$$
\frac{\partial C}{\partial t}
=
\frac{\partial}{\partial z}
\left(
D_{eff}(T,f_l)\frac{\partial C}{\partial z}
\right)
$$

这里：

- `C(z,t)`：P 浓度
- `D_eff`：有效扩散系数

为什么它依赖温度和液相分数：

- 固态扩散很慢
- 高温时更快
- 液态时会快很多

所以热模型和扩散模型是强耦合的。  
没有前面的热史，后面的扩散根本没法算。

扩散理论本身最基础的参考文献是 Crank [R1]。

---

## 2. 固态扩散和液态扩散

当前代码里，固态和液态都用 Arrhenius：

$$
D_s(T)=D_{0,s}\exp\left(-\frac{E_{a,s}}{k_B T}\right)
$$

$$
D_l(T)=D_{0,l}\exp\left(-\frac{E_{a,l}}{k_B T}\right)
$$

为什么这样写：

1. 扩散是热激活过程
2. Arrhenius 是最常见的基础表达
3. 这样才能体现高温和液相的巨大增强

在代码里：

- `solid_phosphorus_diffusivity_m2_s(...)`
- `liquid_phosphorus_diffusivity_m2_s(...)`

都在 [phase2_diffusion.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py) 里。

---

## 3. 部分融化时怎么处理

当前项目没有显式追踪真正 sharp 的固液界面扩散。  
相反，它先用了一个更容易实现的近似：

$$
D_{eff}(T,f_l)=(1-f_l)D_s(T)+f_lD_l(T)
$$

其中：

- `f_l=0`：完全固态
- `f_l=1`：完全液态
- 中间值：部分融化

这个写法的优点：

1. 连续
2. 易实现
3. 数值上稳

它的缺点：

- 不是最终最物理的界面模型

所以你要把它理解成：

- 当前阶段的工程闭合
- 不是最后的理论终点

---

## 4. 表面 source 为什么不是固定表面浓度

很多教材里，扩散边界最常见的是：

- constant concentration
- constant source

但这个项目没有直接这么做。  
我们把 PSG 当成一个有限库存 source。

它的思想是：

- PSG 里有很多 P
- 但它不是无限的
- 它和 Si 表面之间有一个交换通量

可以概念化地写成：

$$
J \sim v_{ex}(C_{src}-C_{surf})
$$

为什么不用固定表面浓度：

1. 更接近现实工艺
2. 可以追踪 source 是否被消耗
3. 不容易把表面注入夸大

激光前驱层掺杂和前驱层供源建模方面，当前项目主要参考了 Lill 等人的 precursor-layer 激光掺杂模型和后续统一模型 [R3][R6]。

---

## 5. 为什么会有基础 emitter 和 inactive P 层

现实工艺里，激光前往往不是“干净的未掺杂 Si 表面”。

常见情况包括：

1. 先有 `POCl3 diffusion` 做出的基础 emitter
2. Si 表面还残留一层化学 P

所以当前模型支持两类初始 profile：

### 基础 emitter

写成：

$$
C_{init}(z)=C_s \,\mathrm{erfc}\left(\frac{z}{2L}\right)
$$

为什么：

- 这是最经典的 constant-source diffusion 轮廓 [R1]
- 很适合做第一版近似

### 表面 inactive P layer

当前写成一层顶帽型表面高浓度层。

为什么：

- 便于把“化学库存”和“初始活化施主”分开
- 后面做片电阻建模时，这种分账非常重要

---

## 6. junction depth 是怎么定义的

当前结深定义为：

$$
C_P(z_j)=N_A^{Ga}
$$

也就是：

- P 浓度下降到 Ga 背景浓度的位置

为什么这个定义合理：

1. 它和 p 型基底补偿直接对应
2. 对器件理解最自然

---

## 7. `net donor upper bound` 为什么会突然下降

这个问题很重要，也最容易误读。

图里那条 `Final chemical net donor upper bound` 不是总 P，而是：

$$
N_{D,final}^{upper}=\max(C_{final}-N_A^{Ga},0)
$$

所以在结附近会发生三件事：

1. `P` 本身已经在下降
2. 还要减去 `Ga`
3. 一旦 `P < Ga`，直接截成 `0`

所以曲线会看起来掉得很快。

这通常不是数值错误，而是：

- “总浓度”转成“净施主浓度”后的自然结果

---

## 8. 扩散模型的数值算法怎么理解

扩散方程的离散方法和热方程非常像。

同样是：

1. 把深度离散
2. 把时间离散
3. 把导数换成差分
4. 每个节点写成一条代数方程
5. 拼成一个稀疏矩阵

最后解的是：

$$
\mathbf{A}\mathbf{C}^{n+1}=\mathbf{b}
$$

这里一个很重要的数值细节是：

- 界面扩散系数用 harmonic mean

它适合处理：

1. 固 / 液过渡
2. 高低扩散系数差很多的情况

所以它比简单平均更稳。

---

# Part 5：PSG / Si 堆栈热模型

## 1. 为什么要从裸 Si 升级成 PSG / Si

如果表面真有 PSG，那把样品还当成裸 Si 就不太合理了。

至少会影响：

1. 顶部反射
2. 表面热缓冲
3. PSG 本身吸收一部分热
4. 传到 Si 的能量

所以当前 Phase 3 才引入了：

- [phase3_stack_thermal.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py)

---

## 2. 分层热源怎么写

现在不是一个统一的单层吸收，而是：

1. 顶面先反射一部分
2. PSG 吸收一部分
3. 剩下的透到 Si
4. Si 再继续按自己的吸收深度吸收

所以当前热源是 layered Beer-Lambert 风格。

为什么这样很重要：

- 这是从“概念演示模型”走向“更接近真实工艺模型”的关键一步

关于激光前驱层、PSG 以及激光掺杂统一模型，当前项目主要参考了 [R3][R6][R7]。

---

# Part 6：怎么跑一个算例

## 1. 最常用的单点入口

最简单的运行方式：

```powershell
python .\run_phase3.py --average-power-w 90 --t-end-ns 400
```

这条命令做了什么：

1. 把功率换成 fluence
2. 跑 PSG / Si 热模型
3. 切出 Si 子域
4. 跑 P 扩散
5. 输出 summary 和图

---

## 2. 扫描一串功率点

如果你想看阈值，不要只跑一个点，要扫一串：

```powershell
python .\run_phase3_power_scan.py --output-dir outputs/phase3/power_scan_30_100w_dt005 --power-start-w 30 --power-stop-w 100 --power-step-w 5 --dt-ns 0.05 --t-end-ns 400 --nz 1200
```

这样你就可以看到：

- 温度随功率怎么变
- liquid fraction 怎么变
- 熔深怎么变
- junction 怎么变
- dose 怎么变

---

# Part 7：怎么读结果，而不是被结果骗

## 1. 为什么不能只看 `peak P`

因为 `peak P` 只是轮廓的最大值。

如果表面尖峰被摊平了，但 profile 往深处展宽了，就可能出现：

- `peak P` 下降
- 但 junction 和 dose 继续上升

所以真正更稳的指标是：

1. junction depth
2. net donor sheet dose
3. `P(30 nm)`
4. `P(100 nm)`
5. `P(300 nm)`

---

## 2. `max_liquid_fraction` 是什么

它表示全时空里液相分数 `f_l` 的最大值：

$$
\max_{z,t} f_l(z,t)
$$

怎么读：

- `0`：完全没进液相
- `1`：某处 fully molten
- 中间值：进入了部分融化区

这个指标很有用，因为它能告诉你：

- 系统离真正熔化还有多远

---

## 3. 为什么 near-threshold 区特别难

当前模型里，接近熔化阈值的时候容易出现：

- 时间步敏感
- 小的局部反常

原因不是模型一定错了，而是：

1. 相变本来就有阈值
2. `melt_only` 门控又加了一个阈值
3. `D_eff` 在这段变化非常快

所以 threshold 附近要更小心看：

- `dt`
- `dz`
- 验证脚本

---

# Part 8：为什么一定要做物理验证

一个模型能跑，不代表它可信。

所以当前项目专门做了：

- [run_phase3_physics_validation.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3_physics_validation.py)

它主要检查：

1. fluence 是否单调
2. 温度是否基本单调
3. liquid fraction 是否合理
4. melt depth 是否合理
5. junction 是否合理
6. mass balance 是否守恒
7. `peak P` 的变化能不能被 profile broadening 解释

这一步是整个项目非常重要的习惯：

> 先做结果，再做验证，最后才下结论。

---

# Part 9：为什么当前算法是一个很好的“教学版本”

如果你是初学者，当前这套算法很适合学。

原因是：

1. 物理链条完整
2. 代码规模还在可读范围
3. 热、相变、扩散三件事都能看到
4. 结果能和实验直觉对上
5. 还带有正式验证脚本

你要把它理解成：

- 不是“最终工业仿真器”
- 而是“很好的第一套可学习、可扩展的研究模型”

---

# Part 10：你如果继续学，下一步该学什么

在学会当前这版以后，最自然的下一步是：

1. 更真实的 texture enhancement
2. moving interface
3. partition coefficient / solute trapping
4. active donor + mobility 的片电阻模型
5. 2D 或 axisymmetric FEM

正确顺序建议是：

1. 先学会解释 1D 结果
2. 再学会做验证
3. 再增加复杂物理
4. 最后再增加几何复杂度

---

# Part 11：参考文献

下面这些文献，是这套教程当前真正依赖的核心参考。

## 扩散与初始 profile

`[R1]` J. Crank, *The Mathematics of Diffusion*, Oxford University Press.  
用途：

- 扩散方程基本形式
- `erfc` 型 profile 的物理背景
- 扩散长度和轮廓理解

链接：

- [Crank PDF](https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf)

## Si 在 532 nm 下的光学参数

`[R2]` M. A. Green, “Self-consistent optical parameters of intrinsic silicon at 300 K including temperature coefficients,” *Solar Energy Materials and Solar Cells* 92 (2008) 1305–1310.  
用途：

- `532 nm` 下 Si 的反射率
- 吸收系数 / 吸收深度

链接：

- [Accessible PDF copy](https://subversion.xray.aps.anl.gov/AGIPD_TCAD/PyTCADTools/Attenuation/Silicon_absorption_coeff_visible_photon.pdf)

## 激光前驱层 / PSG 掺杂基础模型

`[R3]` T. Lill et al., “Simulation of Doping Profiles for Laser Doping of Silicon from Phosphorus Precursors,” *Materials* 10, 189 (2017).  
用途：

- precursor-layer laser doping 的基础建模
- 表面 source、热史和轮廓之间的关系

链接：

- [MDPI](https://www.mdpi.com/1996-1944/10/2/189)

## 相变 fixed-grid / enthalpy 方法

`[R4]` V. R. Voller, M. Cross, N. C. Markatos, “An enthalpy method for convection/diffusion phase change,” *International Journal for Numerical Methods in Engineering* 24 (1987) 271–284.  
用途：

- 焓法 / fixed-grid 处理相变的基本思想

链接：

- [Reference page](https://experts.umn.edu/en/publications/an-enthalpy-method-for-convectiondiffusion-phase-change)

`[R5]` V. R. Voller, C. R. Swaminathan, “Fixed grid techniques for phase change problems: A review,” *International Journal for Numerical Methods in Engineering* 30 (1990) 875–898.  
用途：

- 为什么用 fixed-grid / apparent heat capacity
- 这类方法的数值思想和优缺点

链接：

- [Review PDF](https://ccc.illinois.edu/PDF%20Files/Publications/90_Fixed%20Grid%20Techniques%20for%20Phase%20Change%20Problems-%20A%20Review.pdf)

## 统一前驱层激光掺杂模型

`[R6]` A. Hassan et al., “Unified Model for Laser Doping of Silicon from Precursors,” *Materials* 14, 2322 (2021).  
用途：

- 把热、前驱层、扩散和工艺条件放到同一框架里理解

链接：

- [MDPI](https://www.mdpi.com/1996-1944/14/9/2322)

## 激光掺杂工艺与阈值行为

`[R7]` T. Lill et al., “Laser Doping from Dielectric Precursors for Silicon Solar Cells,” *Solar* 2(2), 15 (2022).  
用途：

- 激光掺杂与熔化阈值之间的关系
- 前驱层与吸收 / 反射对阈值的影响

链接：

- [MDPI Solar](https://www.mdpi.com/2673-9941/2/2/15)

## PSG / POCl3 工艺背景

`[R8]` J. Lei et al., “Model of phosphosilicate glass deposition in POCl3 to control phosphorus dose to Si,” *Journal of Applied Physics* 111, 094903 (2012).  
用途：

- PSG 的工艺背景
- `POCl3` 扩散后 PSG / Si 系统的理解

链接：

- [PNNL page](https://www.pnnl.gov/publications/model-phosphosilicate-glass-deposition-pocl3-control-phosphorus-dose-si)

---

# 最后一句话

如果你能把这份教程里的 3 件事真正理解透：

1. 热模型怎么来
2. 扩散模型怎么来
3. 为什么结果一定要做物理验证

那你就已经不只是“会跑代码”，而是开始真正学会“做材料过程建模”了。

如果你接下来想进一步学“代码本身怎么读”，请接着看：

- [[python_code_teaching_for_beginners]]
- [[literature-usage-register]]
