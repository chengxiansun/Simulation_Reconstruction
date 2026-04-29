https://github.com/wasserth/TotalSegmentator.git  
## TotalSegmentator 仓库介绍
TotalSegmentator 是一个用于**CT/MR 影像中主要解剖结构分割**的开源工具，核心目标是对医学影像中 100+ 解剖结构（如器官、骨骼、血管、肌肉等）进行高精度分割，支持多平台（Ubuntu/Mac/Windows）、CPU/GPU 运行，且适配 CT 和 MR 两种模态影像。

该项目由巴塞尔大学医院放射科研究团队开发，核心基于 nnUNet（目前最先进的医学影像分割框架）构建，训练数据集包含 1228 例 CT 数据和 616 例 MR 数据（可公开下载），同时提供了丰富的子任务（如肺血管、肝脏段、牙齿分割等），部分子任务需授权使用。

### 核心功能与特点
1. **多模态支持**：适配 CT（默认）和 MR 影像（需指定 `--task total_mr`）；
2. **丰富的分割任务**：默认任务包含 117 类 CT 解剖结构/50 类 MR 解剖结构，还支持肺血管、肝脏病变、牙齿、面部结构等细分任务；
3. **易用性**：一行命令即可完成分割，支持 NIfTI/DICOM 输入；
4. **高性能**：CPU 下可通过 `--fast`/`--roi_subset` 加速，GPU 下推理效率更高。

---

## 模型构建、训练与推理流程
### 一、模型构建基础
TotalSegmentator 完全基于 **nnUNet v2** 构建，核心设计逻辑是：
1. 将全解剖结构分割拆分为 5 个子任务（器官、脊椎、心脏、肌肉、肋骨），分别训练 5 个 nnUNet 模型（避免单模型类别过多导致性能下降）；
2. 采用 nnUNet 原生的 3D FullRes 配置（3D 全分辨率网络），禁用镜像增强（`nnUNetTrainerNoMirroring`）以适配解剖结构的对称性；
3. 模型权重分为开源（Apache-2.0）和授权两类，开源权重可自动下载，授权权重需申请许可证。

### 二、模型训练流程
仓库中 `train_nnunet.sh` 是核心训练脚本，完整流程如下：

#### 1. 数据预处理：转换为 nnUNet 格式
通过 `convert_dataset_to_nnunet.py` 将 TotalSegmentator 原始数据集（Zenodo 下载）转换为 nnUNet 要求的标准化格式：
- 输入：原始数据集路径、目标 nnUNet 数据集路径、类别映射（如 `class_map_part_organs` 对应器官类）；
- 输出：生成 nnUNet 标准的 `imagesTr`（训练影像）、`labelsTr`（训练标签）、`imagesTs`（测试影像）、`labelsTs`（测试标签），以及 `dataset.json`（数据集元信息）、`splits_final.json`（训练/验证集划分）；
- 关键操作：将多类别标签合并为单通道分割掩码（背景=0，各类别从 1 开始编码）。

```bash
# 示例：转换器官类数据集
python convert_dataset_to_nnunet.py \
/mnt/nor/wasserthalj_data/TotalSegmentator/zenodo_upload/Totalsegmentator_dataset \
/mnt/nor/nnunet/raw_v2/Dataset101_TotalSegmentator_public_part1 \
class_map_part_organs
```

#### 2. 模型训练
使用 nnUNet v2 训练命令，针对 5 个子任务分别训练 3D FullRes 模型：
- 禁用镜像增强（`-tr nnUNetTrainerNoMirroring`），避免解剖结构左右翻转导致标注错位；
- 数据集 ID 对应 5 个子任务（101=器官、102=脊椎、103=心脏、104=肌肉、105=肋骨）。

```bash
# 示例：训练器官类模型（ID 101）
nnUNetv2_train 101 3d_fullres 0 -tr nnUNetTrainerNoMirroring
```

#### 3. 测试集推理与评估
- 推理：用训练好的模型对测试集（`imagesTs`）推理，生成预测标签（`labelsTs_predicted`）；
- 评估：通过 `evaluate.py` 计算 Dice 系数（医学分割核心指标），验证模型性能。

```bash
# 示例：器官类模型推理
cd /mnt/nor/nnunet/raw_v2/Dataset101_TotalSegmentator_public_part1
nnUNetv2_predict -i imagesTs -o labelsTs_predicted -d 101 -c 3d_fullres -tr nnUNetTrainerNoMirroring --disable_tta -f 0

# 示例：计算 Dice 分数
python ~/dev/TotalSegmentator/resources/evaluate.py labelsTs labelsTs_predicted class_map_part_organs
```

### 三、模型推理流程
#### 1. 权重准备
- 开源权重：运行时自动下载（`download_pretrained_weights.py` 可批量下载所有开源权重）；
- 授权权重：需设置许可证（`set_license_number`），验证通过后使用。

#### 2. 推理命令（用户侧）
TotalSegmentator 封装了 nnUNet 推理逻辑，提供简洁的 CLI 接口：
```bash
# CT 影像分割（默认任务：117 类解剖结构）
TotalSegmentator -i ct.nii.gz -o segmentations

# MR 影像分割（指定 total_mr 任务）
TotalSegmentator -i mri.nii.gz -o segmentations --task total_mr

# CPU 加速（fast 模式）
TotalSegmentator -i ct.nii.gz -o segmentations --fast
```

#### 3. 推理核心逻辑（底层）
1. 环境配置：通过 `config.py` 设置 nnUNet 环境变量（`nnUNet_raw`/`nnUNet_preprocessed`/`nnUNet_results`），指向权重目录；
2. 影像预处理：自动处理输入（NIfTI/DICOM 转标准化格式，适配 nnUNet 要求）；
3. 模型调用：加载对应任务的 nnUNet 模型，执行推理（支持 TTA 增强推理，CPU 下可禁用）；
4. 后处理：将 nnUNet 输出的合并掩码拆分为单类别 NIfTI 文件，保存到输出目录。

### 四、关键细节补充
1. **数据集**：公开数据集包含 117 类 CT 标注（v2 版本从 104 类扩展），MR 数据集包含 50 类标注，标注质量有优化但仍存在部分问题（如肋骨末端标注不完整、结肠/小肠标注模糊）；
2. **训练优化**：
   - 分 5 个子任务训练，避免单模型类别过多；
   - 采用 3D FullRes 配置，适配医学影像的 3D 空间特征；
   - 禁用镜像增强，适配解剖结构的生理对称性；
3. **部署**：支持 Docker 部署（提供 Dockerfile），可构建服务端（Flask）对外提供分割接口；
4. **扩展**：支持自定义子任务（如肺结节、肾脏囊肿），部分子任务需引用对应论文。

---

## 总结
TotalSegmentator 是基于 nnUNet 封装的开箱即用医学影像分割工具，核心流程为：  
`原始数据集 → 转换为 nnUNet 格式 → 分任务训练 3D FullRes 模型 → 推理/评估 → 封装为易用的 CLI 工具`  

其优势在于依托 nnUNet 的强鲁棒性，适配多模态/多设备，同时提供丰富的细分任务；不足是部分子任务模型训练数据量较小，鲁棒性略低，且部分高级功能需授权。