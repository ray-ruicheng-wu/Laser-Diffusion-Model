---
tags:
  - python
  - tutorial
  - beginner
  - code-reading
  - obsidian
---

# 从零读懂这套代码：给只会基础 Python 的材料本科生

## 这份教程的目标

这份教程不是在教你“怎么用 ChatGPT 跑一个脚本”，而是在教你：

> 如何真正看懂这套项目代码，知道每个 Python 文件在做什么，知道每个函数为什么存在，知道一个数值模型是怎么从公式一步步变成程序的。

默认你现在的水平是：

1. 会最基础的 Python
2. 知道变量、函数、`for` 循环、`if`
3. 没怎么系统学过 NumPy、SciPy、数据结构或工程代码组织

这份教程会尽量按“从陌生到熟悉”的顺序来讲：

1. 先讲怎么读一个科研 Python 项目
2. 再讲这套代码里的 Python 语法
3. 再讲每个文件在做什么
4. 再讲关键函数怎么对应物理公式
5. 最后讲怎么自己修改和扩展

---

# Part 1：先学会“怎么看代码”

## 1. 不要一上来就逐行读

很多初学者一打开代码就从第一行读到最后一行，结果读着读着就迷路了。

更好的顺序是：

1. 先看入口脚本
2. 再看主模块
3. 再看辅助函数
4. 最后才看细节

在这个项目里，推荐顺序是：

1. [run_phase3.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3.py)
2. [phase3_stack_thermal.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py)
3. [phase2_diffusion.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py)
4. [phase1_thermal.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py)
5. [run_phase3_power_scan.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3_power_scan.py)
6. [run_phase3_physics_validation.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3_physics_validation.py)

为什么不是先看 `phase1_thermal.py`？

因为入口脚本最能回答：

- 这个项目怎么运行
- 用户能改哪些参数
- 最后会输出什么

---

## 2. 看代码时脑子里要一直追 3 条线

读科研代码，不要只看“语法”，要同时追 3 条线：

### 线 1：数据从哪里来

比如：

- 激光功率从命令行来
- 命令行变成 `LaserPulse`
- `LaserPulse` 进入热模型

### 线 2：数据怎么变化

比如：

- 热模型输出温度场
- 扩散模型拿这个温度场算 `P(z,t)`
- 结果变成 summary、图和 CSV

### 线 3：每一步为什么这样算

比如：

- 为什么这里用高斯脉冲
- 为什么这里用隐式法
- 为什么这里要减 `Ga background`

只要你能同时看这 3 条线，代码就会越来越清楚。

---

# Part 2：先补齐这套代码里最重要的 Python 基础

这一部分很重要。  
因为很多人其实不是不懂物理，而是被 Python 写法吓住了。

---

## 1. `import` 是什么

比如在 [phase1_thermal.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py) 开头你会看到：

```python
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from scipy.sparse import diags
from scipy.sparse.linalg import spsolve
```

意思分别是：

- `dataclasses`
  用来定义结构化数据对象
- `json`
  用来写 summary 文件
- `Path`
  用来处理路径
- `matplotlib`
  用来画图
- `numpy`
  用来做数组和数值计算
- `scipy.sparse`
  用来解稀疏矩阵方程

你可以这样理解：

- `import` 就是在把“别的工具箱”拿进来用

---

## 2. 为什么大家都把 `numpy` 写成 `np`

你会经常看到：

```python
import numpy as np
```

这只是一个简写习惯。

后面你看到：

- `np.linspace(...)`
- `np.zeros(...)`
- `np.exp(...)`

都表示在调用 NumPy 里的函数。

---

## 3. 什么是 `dataclass`

看这个例子：

```python
@dataclass(slots=True)
class LaserPulse:
    fluence: float = 0.55 * 1.0e4
    pulse_fwhm: float = 10.0e-9
    peak_time: float = 30.0e-9
    absorptivity: float = 0.72
    absorption_depth: float = 80.0e-9
```

这表示：

- 我们定义了一个叫 `LaserPulse` 的数据对象
- 它里面放了 5 个字段

你可以把它理解成一个“带名字的参数包”。

如果不用 dataclass，可能就要传一大串参数，很容易乱。

用了 dataclass 以后，我们可以写：

```python
pulse = LaserPulse(fluence=..., pulse_fwhm=...)
```

然后把整个 `pulse` 传给函数。

这在科研代码里特别有用，因为物理参数很多。

### `slots=True` 是什么

这个选项你现在可以先简单理解成：

- 限制对象只拥有声明过的字段
- 更省内存
- 更不容易手滑写错字段名

对初学者来说，知道它“不是核心物理逻辑”就够了。

---

## 4. 类型标注 `: float` 是什么

比如：

```python
fluence: float = 0.55 * 1.0e4
```

这里的 `: float` 只是告诉你：

- 这个变量应该是浮点数

它主要作用是：

1. 让代码更容易读
2. 让编辑器更好提示
3. 降低多人协作时的误解

对 Python 来说，这通常不是强制的“编译器检查”，更像说明书。

---

## 5. `np.ndarray` 是什么

在这个项目里，很多量都不是单个数字，而是一整串数，比如：

- 深度网格
- 时间网格
- 温度场
- 浓度场

这些都存在 NumPy 数组里。

比如：

```python
depth = np.linspace(0.0, domain.thickness, domain.nz)
```

意思是：

- 从 `0` 到厚度
- 均匀切成 `nz` 个点

得到一个一维数组。

再比如：

```python
temperature = np.zeros((time.size, depth.size))
```

这表示：

- 建一个二维数组
- 行数是时间点个数
- 列数是深度点个数

也就是：

- 每一行：某个时刻的温度分布
- 每一列：某个深度随时间的温度变化

---

## 6. 什么是切片

你会经常看到：

```python
temperature[:, silicon_mask]
conductivity[:-1]
conductivity[1:]
```

这些是 NumPy 的切片语法。

### `[:-1]`

表示：

- 从开头到倒数第一个之前

### `[1:]`

表示：

- 从第二个开始到最后

### `[:, silicon_mask]`

这里是二维数组切片：

- `:` 表示所有行
- `silicon_mask` 表示只取满足条件的列

这套写法在科学计算里非常常见。

---

## 7. `if ... else ...` 在科学代码里常干什么

在这个项目里，`if` 最常见的用途有三种：

1. 切换边界条件
2. 切换物理模式
3. 做健壮性检查

比如：

```python
if domain.bottom_bc == "dirichlet":
    ...
if domain.bottom_bc == "neumann":
    ...
```

这表示：

- 不同边界条件，对应不同离散写法

再比如：

```python
if params.source_exchange_mode == "melt_only" and liquid_fraction_surface <= params.interface_liquid_threshold:
    return 0.0
```

意思是：

- 如果还没达到液相门槛，那表面额外注入就不开

---

## 8. 什么是 `raise ValueError(...)`

比如：

```python
if value_cm3 < 0.0:
    raise ValueError(...)
```

意思是：

- 如果输入不合理，就立刻报错

这是好习惯。  
因为科研代码最怕“输入错了但是还继续算”。

当前项目里，这类检查很多，比如：

- 掺杂浓度不能是负数
- source thickness 不能小于 0
- transport length 不能小于 0

---

## 9. `Path` 是什么

比如：

```python
output_path = Path(output_dir)
output_path.mkdir(parents=True, exist_ok=True)
```

你可以把 `Path` 理解成：

- 比字符串更聪明的路径对象

它的好处是：

1. 拼路径方便
2. 跨平台更安全
3. 读写文件更直观

---

## 10. `json.dump(...)` 在干什么

这个项目很多结果都会保存成 `summary.json`。

比如：

```python
with (output_path / "summary.json").open("w", encoding="utf-8") as handle:
    json.dump(summary, handle, indent=2)
```

意思是：

1. 打开一个 JSON 文件准备写入
2. 把 Python 字典 `summary` 写进去
3. `indent=2` 表示格式化得更好读

这样做的好处：

- 人能看
- 脚本也能读

---

# Part 3：先从入口脚本学起

## 1. `run_phase3.py` 是最重要的入门文件

如果你只能先读一个文件，就读：

- [run_phase3.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3.py)

因为它回答了最关键的问题：

1. 这个程序接受什么输入
2. 它调用哪些核心模块
3. 最后会输出什么

你读这个文件时，建议按下面顺序看：

### 第一步：看 `build_parser()`

这部分在定义命令行参数。

你会看到很多：

```python
parser.add_argument("--average-power-w", type=float, default=30.0)
```

这句话可以读成：

- 增加一个命令行参数 `--average-power-w`
- 类型是 `float`
- 默认值是 `30.0`

这相当于在告诉你：

- 用户可以改哪些物理参数

### 第二步：看 `_fluence_j_cm2(...)`

这部分在做最基础的激光能量换算。

它把：

- 平均功率
- 频率
- 光斑面积

换成：

- 单脉冲能量
- fluence

### 第三步：看 `main()`

这里才是真正的主流程：

1. 读命令行参数
2. 构建 `LaserPulse`
3. 构建 Si 和 PSG 的物性
4. 跑 stack 热模型
5. 提取 Si 子域
6. 跑扩散模型
7. 保存结果
8. 打印 summary

如果你能把 `main()` 的流程图画出来，就说明你已经开始读懂整个工程了。

---

# Part 4：读懂 `phase1_thermal.py`

## 1. 这个文件的定位

这个文件是整个项目最基础的热学骨架。

即使现在主要跑的是 Phase 3，Phase 1 仍然很重要，因为：

1. 很多基础 dataclass 在这里定义
2. 相变函数在这里定义
3. 高斯脉冲函数在这里定义
4. 最基础的热离散框架在这里定义

---

## 2. 先看 dataclass，不要先看矩阵

初学者一看到 `_assemble_matrix(...)` 很容易害怕。  
更好的顺序是：

### `MaterialProperties`

告诉你材料需要哪些参数：

- 密度
- 固态 / 液态热容
- 固态 / 液态热导率
- latent heat
- 熔点
- mushy width

### `LaserPulse`

告诉你脉冲需要哪些参数：

- fluence
- 脉宽
- 峰值时间
- 吸收率
- 吸收深度

### `Domain1D`

告诉你数值网格需要哪些参数：

- 厚度
- 网格数
- 时间步长
- 总时间
- 环境温度
- 底边界条件

只要先把这些“参数包”看懂，后面的函数就不再神秘。

---

## 3. `liquid_fraction(...)` 这个函数在做什么

这是一个非常重要的函数。

它的作用是：

- 给定温度
- 判断材料处于固态、液态还是部分融化

逻辑上它做了这几件事：

1. 定义 `solidus`
2. 定义 `liquidus`
3. 温度低于 `solidus` 的点，液相分数为 `0`
4. 温度高于 `liquidus` 的点，液相分数为 `1`
5. 中间区域线性插值

这就是当前项目里 `f_l` 的来源。

你以后看到：

- `max_liquid_fraction`
- `D_eff(T, f_l)`

本质上都和这个函数有关。

---

## 4. `apparent_heat_capacity(...)` 为什么这么写

这个函数做了两件事：

1. 先根据液相分数在固态热容和液态热容之间插值
2. 再在相变区加上 latent heat 贡献

所以它不是普通热容，而是“把相变热也一起算进去”的有效热容。

这就是焓法 / apparent heat capacity 的代码化形式。

---

## 5. `gaussian_flux(...)` 是一个很好的入门例子

这个函数很适合初学者学，因为它非常“数学公式 -> Python 代码”。

物理上你知道脉冲包络是高斯：

$$
q''(t)\propto \exp\left(-\frac{(t-t_{peak})^2}{2\sigma^2}\right)
$$

代码里就是：

```python
return prefactor * np.exp(-0.5 * ((time - pulse.peak_time) / sigma) ** 2)
```

这里你要学会两件事：

1. NumPy 允许你直接对整个数组做公式计算
2. Python 科学代码里，很多时候代码几乎就是公式本身

---

## 6. `_assemble_matrix(...)` 怎么读

这是新手最容易害怕的函数，但其实它只是把离散方程组装起来。

建议你读它时只看 4 件事：

### 第一件：`dz`

```python
dz = domain.thickness / (n - 1)
```

表示网格间距。

### 第二件：`capacity`

```python
capacity = material.rho * apparent_heat_capacity(...) / domain.dt
```

表示时间项离散后的系数。

### 第三件：`interface_k`

```python
interface_k = 0.5 * (conductivity[:-1] + conductivity[1:])
```

表示相邻节点之间的等效热导。

### 第四件：`lower / diag / upper`

这三个数组就是稀疏矩阵的三条对角线。

你可以把它想成：

- `lower`：下对角线
- `diag`：主对角线
- `upper`：上对角线

最后用：

```python
matrix = diags(...)
```

把三条对角线拼成稀疏矩阵。

这就是典型的一维隐式离散写法。

---

## 7. `run_simulation(...)` 为什么是整个文件最重要的函数

因为它把所有零件串起来了。

你可以把它读成下面这个流程：

1. 先准备默认输入
2. 检查掺杂参数是否合法
3. 创建深度网格和时间网格
4. 分配温度数组、液相数组、熔深数组
5. 时间步循环开始
6. 每一步先算热源
7. 再做小迭代求新温度
8. 更新液相分数和熔深
9. 最后把所有结果装进 `SimulationResult`

只要你能把这个流程复述出来，就说明你真的开始理解代码了。

---

# Part 5：读懂 `phase2_diffusion.py`

## 1. 这个文件的角色

这个文件的输入不是激光功率，而是：

- 一个已经算好的热历史 `SimulationResult`

它的任务是：

- 根据温度和液相分数，算 P 在 Si 中怎么分布

所以它是一个典型的“后处理 + 传输求解”模块。

---

## 2. 为什么这个文件一开始又定义了 dataclass

这里定义了：

- `DiffusionParameters`
- `DiffusionResult`

这很正常。

因为热模型关心的参数和扩散模型关心的参数并不一样。

热模型关心：

- 熔点
- 热导率
- 热容

扩散模型关心：

- 固相扩散系数参数
- 液相扩散系数参数
- 边界模式
- source 厚度
- 初始 profile

所以单独再定义一个参数包是正确做法。

---

## 3. `CM3_TO_M3 = 1.0e6` 为什么要有

这行看起来不起眼，但很重要。

因为：

- 实验里掺杂浓度通常用 `cm^-3`
- 数值计算里很多长度是 `m`

所以单位必须统一。

1 立方米等于：

$$
10^6 \text{ cm}^3
$$

所以：

- `cm^-3` 转 `m^-3` 要乘 `10^6`

这类单位换算常量，在工程代码里非常重要。

---

## 4. `solid_phosphorus_diffusivity_m2_s(...)` 和 `liquid_phosphorus_diffusivity_m2_s(...)`

这两个函数的写法很像，因为它们都在做同一类事情：

- 把 Arrhenius 公式变成代码

你可以把它们当作“公式函数”。

读这类函数时，重点看：

1. 输入是什么
2. 单位有没有换
3. 公式是不是和你认识的一样

比如：

```python
prefactor_m2_s = params.solid_prefactor_cm2_s * 1.0e-4
```

这里在做：

- `cm^2/s -> m^2/s`

因为：

$$
1\text{ cm}^2 = 10^{-4}\text{ m}^2
$$

---

## 5. `effective_diffusivity_m2_s(...)` 非常值得你仔细读

这个函数只有几行，但它把“部分融化时怎么处理扩散”这个关键建模选择写死了：

```python
return solid_diffusivity * (1.0 - liquid_fraction) + liquid_diffusivity * liquid_fraction
```

这表示：

- 固态部分按固态扩散
- 液态部分按液态扩散
- 中间按液相分数混合

这就是一种非常典型的“模型假设在代码里的落点”。

所以你以后读科研代码时，要特别注意这类函数。  
它们通常不是简单实现，而是在表达建模者的物理选择。

---

## 6. `_surface_exchange_velocity_m_s(...)` 为什么是本项目非常关键的函数

如果让我选这个文件里最关键的函数之一，我会选它。

因为它决定了：

- PSG 到 Si 的额外注入什么时候打开
- 打开后强度有多大
- source 库存怎么限制表面通量

它里面有几个你一定要学会看的判断：

### 判断 1：source 有没有了

```python
if inventory_atoms_m2 <= 0.0 or source_concentration_m3 <= 0.0:
    return 0.0
```

### 判断 2：是不是 `melt_only`

```python
if params.source_exchange_mode == "melt_only" and liquid_fraction_surface <= params.interface_liquid_threshold:
    return 0.0
```

### 判断 3：表面是否真的还有浓度差

```python
driving_concentration_m3 = source_concentration_m3 - surface_concentration_m3
if driving_concentration_m3 <= 0.0:
    return 0.0
```

这就是典型的工程代码风格：

- 先排除所有“不该注入”的情况
- 再计算真正的通量速度

---

## 7. `_initial_active_profile_m3(...)` 是怎么把物理公式写进代码的

这个函数很适合材料学生练习“公式翻译成代码”。

它做的事情是：

1. 检查 profile 类型是不是 `erfc_emitter`
2. 把表面浓度和结深转换成 `erfc` 参数
3. 生成一个初始 profile

这里最值得学的是：

- 代码不是直接拿一个“现成扩散长度”
- 而是通过 `erfcinv` 从“表面浓度 + junction depth”反推参数

这说明科研代码里很常见的一件事：

> 你不一定总是从最标准的数学参数出发，  
> 也可能从实验上更容易给的参数出发，然后反推数学参数。

---

## 8. `_assemble_diffusion_matrix(...)` 怎么读

它和热模型的矩阵组装非常像。

但多了一个重要东西：

- 表面交换项

你读这个函数时，可以重点找三个量：

### `surface_diffusion`

表示表面节点和第二个节点之间的扩散耦合。

### `surface_exchange`

表示表面 reservoir 和第一个节点之间的交换耦合。

### `coeff_bottom`

表示底部的零通量边界离散。

如果你能把这三个量的物理意义对上，这个函数就不会显得神秘。

---

## 9. `run_diffusion(...)` 是怎么组织整个扩散过程的

这个函数可以理解成：

1. 先创建所有数组
2. 建初始 profile
3. 记录初始库存
4. 时间步循环
5. 每一步：
   - 先算当前 `D_eff`
   - 再算表面 reservoir 浓度
   - 再算表面交换速度
   - 再组扩散矩阵
   - 再解线性系统
   - 再更新库存和结深
6. 最后把结果打包成 `DiffusionResult`

这就是一个非常标准的“科研求解器主循环”。

---

# Part 6：读懂 `phase3_stack_thermal.py`

## 1. 这个文件为什么存在

如果没有它，我们的热模型就只有裸 Si。  
但现实里表面有 PSG，所以就必须把表层单独建出来。

这个文件做的事情是：

1. 定义 PSG 的热学参数
2. 定义 stack 的光学参数
3. 建 PSG / Si 总深度网格
4. 分层计算热容、热导率、密度、热源
5. 最后再把 Si 子域切出来给扩散模块

---

## 2. `_psg_mask(...)` 是什么

这类函数对初学者很有启发。

```python
return depth < psg.thickness
```

这表示：

- 返回一个布尔数组
- 哪些深度点属于 PSG，就标成 `True`

这种“mask”在 NumPy 代码里非常常见。

后面你会看到：

```python
silicon_mask = ~_psg_mask(depth, psg)
```

这里的 `~` 表示逻辑取反，也就是：

- 非 PSG 的部分就是 Si

---

## 3. 分层物性函数怎么读

比如：

- `_stack_apparent_heat_capacity(...)`
- `_stack_thermal_conductivity(...)`
- `_stack_density(...)`

它们的共同结构都是：

1. 先用 PSG 值把整个数组填满
2. 再用 mask 找到 Si 区域
3. 把 Si 区域替换成 Si 的值

这是一种非常常见、也非常值得初学者学会的 NumPy 写法。

它的好处是：

- 不用写很多层 `for` 循环
- 代码更短
- 含义也更清楚

---

## 4. `layered_volumetric_heat_source(...)` 是整个 stack 模型的核心

这个函数是“分层热源”的代码实现。

你可以按这个顺序读：

1. 先算表面反射后的入射热流
2. 如果 PSG 存在，就在 PSG 里按指数衰减吸收
3. 剩余部分乘上传输系数，进入 Si
4. Si 再按自己的吸收深度吸收

这其实就是把分层 Beer-Lambert 模型翻译成了代码。

---

## 5. `silicon_subdomain_view(...)` 是一个非常好的模块化例子

它做的事情很简单：

- 从整个 stack 结果里切出 Si 的那部分

但它非常重要，因为它说明了良好的代码设计：

- 热模型可以看整个 stack
- 扩散模型只拿 Si 子域

这样两个模块职责清楚，不会混在一起。

这就是你以后写科研代码应该学习的风格：

- 先分清模块边界
- 再把模块串起来

---

# Part 7：读懂扫描脚本和验证脚本

## 1. `run_phase3_power_scan.py` 是怎么工作的

这个脚本本质上就是：

```python
for power_w in powers:
    rows.append(_run_single_power(...))
```

也就是：

- 一次跑一个功率点
- 再把每个功率点的结果汇总

这是非常典型的“科研批处理”脚本。

它值得初学者学习的地方是：

1. 怎么把单点求解封装成函数
2. 怎么把多次结果整理成表
3. 怎么自动画趋势图

---

## 2. `run_phase3_physics_validation.py` 为什么特别值得学

这个脚本不是在“造新结果”，而是在“审查旧结果”。

这是一种非常成熟的科研编程习惯。

它让你学会：

1. 一个模型不只是“能跑”
2. 还要“会检查自己”

如果你以后自己做研究，这是非常值得学的思维方式。

---

# Part 8：如果你要自己改代码，先从哪里下手

## 1. 想改工艺输入

优先改：

- [run_phase3.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3.py)

因为这里是参数入口。

---

## 2. 想改热源公式

优先看：

- [phase1_thermal.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase1_thermal.py)
- [phase3_stack_thermal.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py)

---

## 3. 想改扩散口径

优先看：

- [phase2_diffusion.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py)

特别要看：

- `effective_diffusivity_m2_s(...)`
- `_surface_exchange_velocity_m_s(...)`
- `_assemble_diffusion_matrix(...)`
- `run_diffusion(...)`

---

## 4. 想判断结果靠不靠谱

优先看：

- [run_phase3_physics_validation.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3_physics_validation.py)

这比盯一张图更重要。

---

# Part 9：你现在最应该学会的 5 件事

如果你读完这份教程，只学会下面 5 件事，就已经很值了。

1. 知道入口脚本和核心模块应该怎么分开看
2. 知道 dataclass 在科研代码里为什么重要
3. 知道热方程和扩散方程怎么离散成矩阵
4. 知道一条结果曲线为什么不能脱离它的定义去解释
5. 知道模型一定要做物理验证，而不是只看“能不能跑”

---

# Part 10：物理参考文献

这份“代码教学”虽然以代码为主，但背后用到的物理模型并不是凭空编出来的。  
当前项目中最核心的物理参考文献，建议你至少知道它们支持哪一部分。

`[R1]` J. Crank, *The Mathematics of Diffusion*  
支持内容：

- 扩散方程
- `erfc` 型 profile
- 基础扩散数学

链接：

- [Crank PDF](https://people.bath.ac.uk/ensdasr/PAPERS/Crank-The-Mathematics-of-Diffusion.pdf)

`[R2]` M. A. Green, optical parameters of intrinsic silicon at 300 K  
支持内容：

- `532 nm` 下 Si 的反射率和吸收深度

链接：

- [PDF copy](https://subversion.xray.aps.anl.gov/AGIPD_TCAD/PyTCADTools/Attenuation/Silicon_absorption_coeff_visible_photon.pdf)

`[R3]` T. Lill et al., *Materials* 2017, 10, 189  
支持内容：

- precursor-layer laser doping
- 表面 source / 热史 / 轮廓建模思路

链接：

- [MDPI](https://www.mdpi.com/1996-1944/10/2/189)

`[R4]` V. R. Voller, M. Cross, N. C. Markatos, enthalpy method for phase change  
支持内容：

- 焓法 / apparent heat capacity / fixed-grid 相变

链接：

- [Reference page](https://experts.umn.edu/en/publications/an-enthalpy-method-for-convectiondiffusion-phase-change)

`[R5]` V. R. Voller, C. R. Swaminathan, fixed grid techniques review  
支持内容：

- 为什么 fixed-grid 相变法适合入门和工程数值实现

链接：

- [Review PDF](https://ccc.illinois.edu/PDF%20Files/Publications/90_Fixed%20Grid%20Techniques%20for%20Phase%20Change%20Problems-%20A%20Review.pdf)

`[R6]` A. Hassan et al., *Materials* 2021, 14, 2322  
支持内容：

- 统一 precursor 激光掺杂模型

链接：

- [MDPI](https://www.mdpi.com/1996-1944/14/9/2322)

`[R7]` T. Lill et al., *Solar* 2022, 2(2), 15  
支持内容：

- 激光掺杂与熔化阈值关系

链接：

- [MDPI Solar](https://www.mdpi.com/2673-9941/2/2/15)

`[R8]` J. Lei et al., phosphosilicate glass deposition model in `POCl3`  
支持内容：

- PSG 工艺背景
- `POCl3 -> PSG -> Si` 体系理解

链接：

- [PNNL page](https://www.pnnl.gov/publications/model-phosphosilicate-glass-deposition-pocl3-control-phosphorus-dose-si)

---

# 最后一段建议

如果你真的想靠这套项目学会科研建模，不要只停在“读懂”。

你接下来最有收获的练习是：

1. 自己改一个输入参数
2. 自己重新跑一个 case
3. 自己读 summary
4. 自己解释结果变化
5. 再去看验证脚本是否支持你的解释

当你能做到这一步，你就已经从“会看代码”进入“会用模型思考问题”了。

---

# 附录 A：2026-04-08 新增的 texture 参数怎么读

这次代码里又多了一组很适合初学者学习的参数，因为它们能帮助你理解：

> 程序里的一个“物理想法”，是怎么一步步变成可调参数的。

新增入口主要在：

- [run_phase3.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/run_phase3.py)
- [phase3_stack_thermal.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase3_stack_thermal.py)
- [phase2_diffusion.py](/C:/Users/User/Desktop/Codex/Diffusion%20Simulation/src/laser_doping_sim/phase2_diffusion.py)

新增的核心参数是：

1. `--texture-reflectance-multiplier`
2. `--texture-interface-area-factor`
3. `--texture-pyramid-sidewall-angle-deg`

你可以这样理解它们：

## 1. `--texture-reflectance-multiplier`

这是一个“把复杂纹理光学折成一个数”的参数。

代码里真正用的是：

```python
effective_surface_reflectance = surface_reflectance * texture_reflectance_multiplier
```

意思是：

- 平面表面原本反射 `R_flat`
- 如果纹理让光更不容易逃出去
- 那么就把有效反射率缩小一点

例如：

- `surface_reflectance = 0.09`
- `texture_reflectance_multiplier = 0.5`

那么：

- `R_eff = 0.045`

这不是说“反射物理就真的这么简单”，而是说：

- 对当前 `1D` 模型来说，这是一个合理的第一步近似

## 2. `--texture-interface-area-factor`

这是“真实表面积 / 投影面积”的比值。

因为制绒以后，表面不再是平的，而是有坡面。  
所以对于同样的俯视面积，真实界面会更大。

这个值在代码里会影响两件事：

1. PSG source 的 projected-area 库存
2. 界面传质强度

也就是说，程序在表达这样一个想法：

> 如果真实界面更大，那么同样一块俯视面积下，既可能有更多 PSG 材料，也可能允许更大的总注入通量。

## 3. `--texture-pyramid-sidewall-angle-deg`

这个参数是一个“方便输入”的几何入口。

如果你不想直接手动给 `A_factor`，可以给一个理想金字塔侧壁角 `theta`，程序就会自动算：

```python
A_factor = 1 / cos(theta)
```

也就是：

```python
A_factor = sec(theta)
```

对于理想的 `54.74°` 金字塔侧壁角，程序会得到大约：

- `A_factor ≈ 1.732`

这正是我们这次 texture 拆解测试里用的面积增强因子。

## 4. 为什么这几个参数适合初学者学习

因为它们非常典型地展示了科研代码里的一个过程：

1. 先有一个物理现象  
   例如“制绒会降低反射”“制绒会增加真实界面面积”
2. 再决定如何降阶  
   例如“先别做 3D，先折成 `R_eff` 和 `A_factor`”
3. 再给出可调参数  
   例如 `texture_reflectance_multiplier`
4. 再把它接进已有求解器  
   一个接热模型，一个接扩散边界

这就是为什么科研代码不只是“把公式打进去”，而是：

> 先做物理抽象，再做数值表达。
