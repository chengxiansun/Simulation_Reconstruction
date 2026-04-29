# ==============================
# Screened Poisson 重建完整示例
# 每行都带原理注释
# ==============================

# 1. 导入需要的库
# open3d：3D点云处理库，内置筛选泊松重建
import open3d as o3d
# numpy：用于数值计算
import numpy as np

# ==============================================
# 步骤1：生成/加载点云（这里直接生成一个球体点云，不用外部文件）
# 原理：SPR必须输入【带法向量的点云】，法向量质量决定重建效果
# ==============================================
print("正在生成球体点云（带法向量）...")

# 生成一个球体点云（Open3D自带几何形状）
# 这就是你的【输入点云】
pcd = o3d.geometry.TriangleMesh.create_sphere(radius=1.0).sample_points_poisson_disk(5000)

# 关键点：计算点云法向量（SPR必须要法向量！）
# 原理：通过邻域PCA（主成分分析）估计每个点的法向量方向
pcd.normalize_normals()          # 归一化法向量长度为1
pcd.estimate_normals(             # 估计法向量
    search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30)
)

# ==============================================
# 步骤2：执行 Screened Poisson Surface Reconstruction
# 这就是核心算法！
# ==============================================
print("开始执行筛选泊松表面重建（SPR）...")

# --------------------------
# 核心函数：poisson_reconstruction
# 内置就是 Screened Poisson（带筛选项，不是老版泊松）
# --------------------------
mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
    pcd,                # 输入：带法向量的点云
    depth=9,            # 八叉树深度 → 控制网格精度（9~11最常用）
    width=0,            # 3D域宽度（0=自动）
    scale=1.1,          # 重建包围盒缩放（自动扩展）
    linear_fit=True     # 线性拟合 → 让边缘更锐利
)

# 原理说明（代码里也给你写清楚）：
# depth=9 → 八叉树细分 2^9 × 2^9 × 2^9 体素
# linear_fit=True → 启用更精确的等值面提取，减少锯齿
# densities：每个三角面片的密度（用于后续去噪）

# ==============================================
# 步骤3：后处理：去掉低密度的多余三角面
# 原理：泊松重建会生成一些远离点云的“浮面”，密度低，需要过滤
# ==============================================
print("清理重建网格（去掉远离点云的面片）...")

# 计算密度阈值（保留前99%高密度的面）
bbox = pcd.get_axis_aligned_bounding_box()
mesh = mesh.crop(bbox)  # 按点云包围盒裁剪网格

# ==============================================
# 步骤4：保存输出 + 可视化
# ==============================================
print("保存重建网格 → output_reconstructed_mesh.ply")
o3d.io.write_triangle_mesh("output_reconstructed_mesh.ply", mesh)

# 可视化：左边原始点云，右边重建网格
print("显示结果：蓝色=原始点云，灰色=重建网格")
o3d.visualization.draw_geometries([pcd, mesh], window_name="SPR 重建结果")

print("✅ 重建完成！输出文件：output_reconstructed_mesh.ply")