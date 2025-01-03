import numpy as np
import matplotlib.pyplot as plt

# 给定参数
x1, y1 = 0, 0  # 起点坐标
c = -0.1  # 曲率
d = 0  # 初始朝向（度）
l = 10  # 曲线长度

# 将曲率转换为半径
r = 1 / c

# 将初始朝向转换为弧度
d_rad = np.deg2rad(d)

# 计算圆心坐标
h = x1 - r * np.sin(d_rad)
k = y1 + r * np.cos(d_rad)

# 计算圆心角（弧度）
theta = l / r

# 参数方程
# def parametric_equation(t):
#     theta = np.deg2rad(l / r)  # 将长度转换为角度
#     angle = d_rad + t * theta
#     x = h + r * np.cos(angle)
#     y = k + r * np.sin(angle)
#     return x, y

# 根据公式计算参数方程
# def parametric_equation(t):
#     x = h + r * np.cos(d_rad + t * theta)
#     y = k + r * np.sin(d_rad + t * theta)
#     return x, y

def parametric_equation(t):
    x = x1 + r * np.sin( t * theta)
    y = y1 + r * (1 - np.cos(t * theta))
    return x, y

# 取 0 到 1 之间 100 个值
t_values = np.linspace(0, 1, 100)

# 计算曲线上的点
x_values, y_values = [], []
for t in t_values:
    x, y = parametric_equation(t)
    x_values.append(x)
    y_values.append(y)

# 绘制曲线
plt.figure(figsize=(8, 8))
plt.plot(x_values, y_values, label='Curve')
plt.scatter([x1], [y1], color='red', label='Start Point')
plt.xlabel('X')
plt.ylabel('Y')
plt.title('Curve with Given Point, Curvature, and Initial Direction')
plt.legend()
plt.axis('equal')
plt.grid(True)
plt.show()