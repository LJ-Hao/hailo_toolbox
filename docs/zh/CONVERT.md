# Hailo 模型转换指南

本文档将手把手教您如何将常见的深度学习模型转换为 Hailo 硬件可以运行的 `.hef` 格式。即使您是初学者，也能轻松完成模型转换。

## 什么是模型转换？

简单来说，模型转换就是把您训练好的模型"翻译"成 Hailo AI 芯片能够理解的语言。就像把中文翻译成英文一样。

### 为什么需要转换？

- **兼容性**: 不同的 AI 芯片有不同的"语言"，需要转换才能运行
- **优化**: 转换过程会针对 Hailo 芯片进行优化，提升运行速度
- **压缩**: 转换后的模型通常更小，占用更少存储空间

## 支持的模型格式

### 输入格式（您的模型）

| 框架 | 文件格式 | 常见用途 | 示例文件名 |
|------|----------|----------|------------|
| **ONNX** | `.onnx` | 通用格式，推荐 | `yolov8n.onnx` |
| **TensorFlow** | `.h5` | Keras 模型 | `model.h5` |
| **TensorFlow** | `saved_model.pb` | TensorFlow 保存的模型 | `saved_model.pb` |
| **TensorFlow Lite** | `.tflite` | 移动端模型 | `model.tflite` |
| **PyTorch** | `.pt` | TorchScript 模型 | `model.pt` |
| **PaddlePaddle** | 推理模型 | 百度飞桨模型 | `inference.pdmodel` |

### 输出格式（转换后）

- **`.hef`**: Hailo Executable Format，Hailo 专用的优化格式

## 准备工作

### 1. 确认系统要求

```bash
# 检查操作系统（必须是 Linux）
uname -a

# 检查 Python 版本（需要 3.8-3.11）
python3 --version
```

### 2. 安装必要软件

```bash
# 安装 Hailo Toolbox
pip install -e .

# 验证安装
hailo-toolbox --version
```

### 3. 准备模型文件

确保您有：
- ✅ 模型文件（如 `model.onnx`）
- ✅ 知道模型的输入尺寸（如 640x640）
- ✅ 校准数据集（推荐，可选）

## 基础转换教程

### 第一步：最简单的转换

如果您有一个 ONNX 模型，最简单的转换命令是：

```bash
hailo-toolbox convert your_model.onnx
```

**解释**:
- `hailo-toolbox convert`: 启动转换工具
- `your_model.onnx`: 您的模型文件名

转换完成后，会在同一目录生成 `your_model.hef` 文件。

### 第二步：指定输出目录

为了更好地管理文件，建议指定输出目录：

```bash
hailo-toolbox convert your_model.onnx --output-dir ./converted_models
```

这样转换后的文件会保存在 `converted_models` 文件夹中。

### 第三步：指定硬件架构

根据您的 Hailo 设备选择对应的架构：

```bash
# Hailo-8 芯片（最常见）
hailo-toolbox convert your_model.onnx --hw-arch hailo8

# Hailo-8L 芯片
hailo-toolbox convert your_model.onnx --hw-arch hailo8l

# Hailo-15 芯片
hailo-toolbox convert your_model.onnx --hw-arch hailo15

# Hailo-15L 芯片
hailo-toolbox convert your_model.onnx --hw-arch hailo15l
```

## 高级转换选项

### 使用校准数据集（推荐）

校准数据集可以提高转换后模型的精度：

```bash
hailo-toolbox convert your_model.onnx \
    --hw-arch hailo8 \
    --calib-set-path ./calibration_images \
    --output-dir ./converted_models
```

**校准数据集要求**:
- 📁 包含代表性图像的文件夹
- 🖼️ 图像格式：JPG、PNG 等
- 📊 数量：建议 100-1000 张
- 🎯 内容：与实际使用场景相似的图像

### 指定输入尺寸

如果转换时出现尺寸相关错误，可以手动指定：

```bash
hailo-toolbox convert your_model.onnx \
    --input-shape 640,640,3 \
    --hw-arch hailo8
```

**输入尺寸格式**:
- `640,640,3`: 宽度,高度,通道数
- `224,224,3`: 常见的分类模型尺寸
- `320,320,3`: 轻量级检测模型尺寸

### 使用随机校准（快速测试）

如果没有校准数据集，可以使用随机数据：

```bash
hailo-toolbox convert your_model.onnx \
    --use-random-calib-set \
    --hw-arch hailo8
```

⚠️ **注意**: 随机校准的精度可能较低，仅适合快速测试。

## 实际转换示例

### 示例 1: YOLOv8 目标检测模型

```bash
# 下载 YOLOv8 ONNX 模型（假设您已有）
# 转换命令
hailo-toolbox convert yolov8n.onnx \
    --hw-arch hailo8 \
    --input-shape 640,640,3 \
    --calib-set-path ./coco_samples \
    --output-dir ./converted_models \
    --save-onnx
```

**参数说明**:
- `--input-shape 640,640,3`: YOLOv8 的标准输入尺寸
- `--calib-set-path ./coco_samples`: 使用 COCO 数据集样本校准
- `--save-onnx`: 保存优化后的 ONNX 文件

### 示例 2: 图像分类模型

```bash
hailo-toolbox convert efficientnet.onnx \
    --hw-arch hailo8 \
    --input-shape 224,224,3 \
    --calib-set-path ./imagenet_samples \
    --output-dir ./converted_models
```

### 示例 3: 快速测试转换

```bash
# 最快的转换方式（用于快速验证）
hailo-toolbox convert test_model.onnx \
    --use-random-calib-set \
    --hw-arch hailo8
```

## 转换参数详解

### 必需参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `model` | 输入模型文件路径 | `yolov8n.onnx` |

### 常用可选参数

| 参数 | 默认值 | 说明 | 示例 |
|------|--------|------|------|
| `--hw-arch` | `hailo8` | 硬件架构 | `hailo8`, `hailo15` |
| `--output-dir` | 模型同目录 | 输出目录 | `./models` |
| `--input-shape` | 自动检测 | 输入尺寸 | `640,640,3` |
| `--calib-set-path` | 无 | 校准数据集路径 | `./calib_images` |
| `--use-random-calib-set` | `False` | 使用随机校准 | - |
| `--save-onnx` | `False` | 保存优化的ONNX | - |
| `--profile` | `False` | 生成性能报告 | - |

## 常见问题解决

### Q1: 转换时提示"找不到模型文件"

**问题**: `FileNotFoundError: model.onnx not found`

**解决方法**:
```bash
# 检查文件是否存在
ls -la your_model.onnx

# 使用绝对路径
hailo-toolbox convert /full/path/to/your_model.onnx
```

### Q2: 转换时提示需要校准数据集

**问题**: `calibration dataset required`

**解决方法**:
```bash
# 方法1: 使用随机校准（快速）
hailo-toolbox convert model.onnx --use-random-calib-set

# 方法2: 准备校准数据集
mkdir calibration_images
# 放入一些代表性图像
hailo-toolbox convert model.onnx --calib-set-path ./calibration_images
```

### Q3: 转换速度很慢

**原因**: 模型转换是计算密集型任务，需要时间

**优化建议**:
- 使用较少的校准图像（100张左右）
- 使用随机校准进行快速测试
- 确保系统有足够内存

### Q4: 转换后的模型很大

**解决方法**:
```bash
# 检查文件大小
ls -lh *.hef

# 如果太大，可以尝试：
# 1. 使用更小的输入尺寸
hailo-toolbox convert model.onnx --input-shape 320,320,3

# 2. 检查是否有不必要的输出节点
hailo-toolbox convert model.onnx --end-nodes output1,output2
```

## 验证转换结果

### 检查转换是否成功

```bash
# 检查生成的文件
ls -la *.hef

# 查看文件信息
file your_model.hef
```

### 快速测试转换后的模型

```bash
# 使用转换后的模型进行推理测试
hailo-toolbox infer your_model.hef \
    --source test_image.jpg \
    --task-name yolov8det \
    --show
```

## 性能优化建议

### 1. 校准数据集优化

- **数量**: 100-500张图像通常足够
- **质量**: 选择与实际场景相似的图像
- **多样性**: 包含不同光照、角度、背景的图像

### 2. 输入尺寸选择

```bash
# 高精度（较慢）
--input-shape 640,640,3

# 平衡（推荐）
--input-shape 416,416,3

# 高速度（较快）
--input-shape 320,320,3
```

### 3. 硬件架构选择

- **Hailo-8**: 高性能，适合复杂模型
- **Hailo-8L**: 低功耗版本
- **Hailo-15**: 最新架构，更高性能

## 转换流程图

```
[原始模型] → [转换工具] → [校准] → [优化] → [HEF模型]
    ↓            ↓          ↓        ↓         ↓
 .onnx文件   hailo-toolbox  校准数据  硬件优化  .hef文件
```

## 总结

模型转换的基本流程：

1. **准备模型文件** (.onnx 格式推荐)
2. **准备校准数据** (可选但推荐)
3. **运行转换命令** 
4. **验证转换结果**
5. **测试推理性能**

**记住这个万能命令**:
```bash
hailo-toolbox convert your_model.onnx \
    --hw-arch hailo8 \
    --calib-set-path ./calibration_images \
    --output-dir ./converted_models
```

转换成功后，您就可以在 Hailo 设备上高速运行您的 AI 模型了！

---

**下一步**: 学习如何使用转换后的模型进行推理，请参考 [模型推理指南](INFERENCE.md)。
