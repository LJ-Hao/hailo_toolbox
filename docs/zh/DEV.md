# Hailo Toolbox 开发者指南

本文档面向开发者，介绍如何为 Hailo Toolbox 实现自定义模型的推理处理模块。

## 概述

Hailo Toolbox 采用模块化架构，通过注册机制管理各个处理模块。要支持新的自定义模型，您需要实现相应的处理模块并注册到系统中。

## 核心模块说明

### 模块分类

| 模块类型 | 是否必需 | 作用 | 实现复杂度 |
|----------|----------|------|------------|
| **PreProcessor** | 🔶 可选 | 图像预处理，转换为模型输入格式 | 简单 |
| **PostProcessor** | ✅ 必需 | 模型输出后处理，解析推理结果 | 中等 |
| **EventProcessor** | 🔶 可选 | 事件处理，基于预测结果执行扩展功能 | 简单-中等 |
| **Visualizer** | 🔶 可选 | 结果可视化，在图像上绘制检测框等 | 简单 |
| **CollateInfer** | 🔶 可选 | 推理结果整理，格式化模型原始输出 | 简单 |
| **Source** | ❌ 无需 | 数据源管理，已有通用实现 | - |

### 模块职责详解

#### PreProcessor（预处理器）- 可选实现
- **作用**: 将输入图像转换为模型所需格式
- **输入**: 原始图像 (H, W, C) BGR格式
- **输出**: 预处理后的张量，通常为 (N, C, H, W) 格式
- **说明**: 系统已内置通用预处理器，可通过 `PreprocessConfig` 配置。只有特殊需求时才需要自定义实现。
- **主要任务**:
  - 图像尺寸调整
  - 颜色空间转换 (BGR→RGB)
  - 数据归一化和标准化
  - 维度转换 (HWC→CHW)

#### PostProcessor（后处理器）- 必需实现
- **作用**: 处理模型原始输出，转换为可用的结果
- **输入**: 模型推理输出字典
- **输出**: 结构化的检测/分类结果列表
- **说明**: 每个模型的输出格式不同，必须实现对应的后处理逻辑。
- **主要任务**:
  - 解码模型输出
  - 置信度过滤
  - 非极大值抑制 (NMS)
  - 坐标转换

#### EventProcessor（事件处理器）- 可选实现
- **作用**: 基于模型预测结果执行扩展功能和业务逻辑
- **输入**: 后处理器输出的结构化结果
- **输出**: 处理后的结果或触发的事件
- **说明**: 用于实现基于AI预测结果的业务逻辑，如统计、报警、数据记录等。
- **主要任务**:
  - 目标计数统计（如行人数量、车辆数量）
  - 异常事件检测和报警
  - 数据记录和日志输出
  - 业务规则判断和执行
  - 与外部系统集成（数据库、API等）

#### Visualizer（可视化器）- 可选实现
- **作用**: 在图像上绘制推理结果
- **输入**: 原始图像 + 后处理结果
- **输出**: 带有可视化标注的图像
- **主要任务**:
  - 绘制边界框
  - 显示类别标签和置信度
  - 渲染分割掩码或关键点

#### CollateInfer（结果整理）- 可选实现
- **作用**: 整理推理引擎的原始输出
- **输入**: 推理引擎原始输出字典
- **输出**: 格式化后的输出字典
- **主要任务**:
  - 维度调整
  - 数据类型转换
  - 多输出合并

## 事件处理器详解

### 概述

事件处理器（EventProcessor）是一个可选的扩展模块，允许开发者基于模型预测结果执行自定义的业务逻辑。它在推理流水线中位于后处理器之后，可以接收结构化的预测结果并执行各种扩展功能。

### 典型应用场景

#### 1. 目标计数统计
```python
@CALLBACK_REGISTRY.registryEventProcessor("person_counter")
class PersonCounterProcessor:
    def __init__(self, config=None):
        self.person_count = 0
        self.total_frames = 0
        
    def __call__(self, results):
        self.total_frames += 1
        
        # 统计检测到的人数
        current_person_count = sum(1 for obj in results if obj.get('class') == 'person')
        self.person_count += current_person_count
        
        # 每100帧输出一次统计
        if self.total_frames % 100 == 0:
            avg_persons = self.person_count / self.total_frames
            print(f"平均每帧人数: {avg_persons:.2f}")
```

#### 2. 异常检测和报警
```python
@CALLBACK_REGISTRY.registryEventProcessor("security_monitor")
class SecurityMonitorProcessor:
    def __init__(self, config=None):
        self.alert_threshold = config.get('alert_threshold', 3) if config else 3
        self.consecutive_alerts = 0
        
    def __call__(self, results):
        # 检测是否有异常情况（如人数过多）
        person_count = sum(1 for obj in results if obj.get('class') == 'person')
        
        if person_count > self.alert_threshold:
            self.consecutive_alerts += 1
            if self.consecutive_alerts >= 5:  # 连续5帧都超过阈值
                self.send_alert(f"检测到异常聚集: {person_count}人")
                self.consecutive_alerts = 0
        else:
            self.consecutive_alerts = 0
            
    def send_alert(self, message):
        # 发送报警（可以是邮件、短信、API调用等）
        print(f"🚨 ALERT: {message}")
        # 这里可以集成实际的报警系统
```

#### 3. 数据记录和分析
```python
@CALLBACK_REGISTRY.registryEventProcessor("data_logger")
class DataLoggerProcessor:
    def __init__(self, config=None):
        self.log_file = config.get('log_file', 'detection_log.csv') if config else 'detection_log.csv'
        self.init_log_file()
        
    def init_log_file(self):
        import csv
        with open(self.log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'frame_id', 'object_count', 'objects'])
    
    def __call__(self, results):
        import csv
        import datetime
        
        timestamp = datetime.datetime.now().isoformat()
        frame_id = getattr(self, 'frame_counter', 0)
        self.frame_counter = frame_id + 1
        
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, 
                frame_id, 
                len(results), 
                str(results)
            ])
```

#### 4. 业务规则执行
```python
@CALLBACK_REGISTRY.registryEventProcessor("traffic_monitor")
class TrafficMonitorProcessor:
    def __init__(self, config=None):
        self.vehicle_count = 0
        self.traffic_state = "normal"
        
    def __call__(self, results):
        # 统计车辆数量
        vehicles = [obj for obj in results if obj.get('class') in ['car', 'truck', 'bus']]
        current_vehicle_count = len(vehicles)
        
        # 更新交通状态
        if current_vehicle_count > 20:
            self.traffic_state = "heavy"
        elif current_vehicle_count > 10:
            self.traffic_state = "moderate"
        else:
            self.traffic_state = "light"
            
        # 执行相应的业务逻辑
        self.update_traffic_light_timing()
        
    def update_traffic_light_timing(self):
        # 根据交通状态调整信号灯时间
        if self.traffic_state == "heavy":
            print("调整信号灯: 延长绿灯时间")
        elif self.traffic_state == "light":
            print("调整信号灯: 缩短绿灯时间")
```

### 实现要点

#### 1. 基本结构
```python
@CALLBACK_REGISTRY.registryEventProcessor("your_processor_name")
class YourEventProcessor:
    def __init__(self, config=None):
        """
        初始化事件处理器
        
        Args:
            config: 配置参数，可以为None
        """
        self.config = config
        # 初始化您的状态变量
        
    def __call__(self, results):
        """
        处理预测结果
        
        Args:
            results: 后处理器输出的结构化结果
            
        Returns:
            可选：返回处理后的结果或状态信息
        """
        # 实现您的业务逻辑
        pass
```

#### 2. 状态管理
事件处理器通常需要维护状态信息：
- 帧计数器
- 历史数据
- 统计信息
- 配置参数

#### 3. 性能考虑
- 避免在事件处理器中执行耗时操作
- 对于I/O操作，考虑使用异步处理
- 定期清理历史数据以避免内存泄漏

### 配置示例

```python
# 在创建InferenceEngine时传入事件处理器配置
event_processor_config = {
    'alert_threshold': 5,
    'log_file': 'custom_log.csv',
    'enable_alerts': True
}

engine = InferenceEngine(
    model="model.hef",
    source="video.mp4",
    task_name="custom",
    event_processor_config=event_processor_config,
    show=True
)
```

通过事件处理器，您可以轻松地将AI推理结果与实际业务需求结合，实现智能化的应用逻辑。

## 注册机制

### 回调类型枚举

```python
from hailo_toolbox.inference.core import CallbackType

class CallbackType(Enum):
    PRE_PROCESSOR = "pre_processor"    # 预处理器
    POST_PROCESSOR = "post_processor"  # 后处理器
    EVENT_PROCESSOR = "event_processor" # 事件处理器
    VISUALIZER = "visualizer"          # 可视化器
    COLLATE_INFER = "collate_infer"    # 推理结果整理
    SOURCE = "source"                  # 数据源（通常无需自定义）
```

### 注册方式

```python
from hailo_toolbox.inference.core import CALLBACK_REGISTRY

# 方式1: 装饰器注册（推荐）
@CALLBACK_REGISTRY.registryPreProcessor("my_model")
def my_preprocess(image):
    return processed_image

# 方式2: 多名称注册（一个实现支持多个模型）
@CALLBACK_REGISTRY.registryPostProcessor("model_v1", "model_v2")
class MyPostProcessor:
    def __call__(self, results): pass

# 方式3: 事件处理器注册
@CALLBACK_REGISTRY.registryEventProcessor("my_model")
class MyEventProcessor:
    def __call__(self, results): pass

# 方式4: 直接注册
CALLBACK_REGISTRY.register_callback("my_model", CallbackType.PRE_PROCESSOR, preprocess_func)
```

## 快速实现示例

以下是一个完整的自定义模型实现示例：

```python
"""
自定义模型实现示例
适用于目标检测类型的模型
"""
from hailo_toolbox.inference.core import InferenceEngine, CALLBACK_REGISTRY
from hailo_toolbox.process.preprocessor.preprocessor import PreprocessConfig
import yaml
import numpy as np
import cv2

# 必须实现
@CALLBACK_REGISTRY.registryPostProcessor("custom")
class CustomPostProcessor:
    def __init__(self, config):
        self.config = config
        self.get_classes()

    def get_classes(self):
        with open("examples/ImageNet.yaml", "r") as f:
            self.classes = yaml.load(f, Loader=yaml.FullLoader)

    def __call__(self, results, original_shape=None):
        class_name = []
        for k, v in results.items():
            class_name.append(self.classes[np.argmax(v)])
        return class_name

# 可选实现 - 事件处理器
@CALLBACK_REGISTRY.registryEventProcessor("custom")
class CustomEventProcessor:
    def __init__(self, config=None):
        self.config = config
        self.frame_count = 0
        self.detection_history = []

    def __call__(self, results):
        """
        基于预测结果执行业务逻辑
        
        Args:
            results: 后处理器输出的结构化结果
            
        Returns:
            处理后的结果或None
        """
        self.frame_count += 1
        
        # 示例1: 简单的结果日志输出
        print(f"Frame {self.frame_count}: Detected classes: {results}")
        
        # 示例2: 统计检测历史
        self.detection_history.append(len(results))
        
        # 示例3: 异常检测逻辑
        if len(results) > 5:  # 如果检测到超过5个对象
            print(f"⚠️  Alert: High object count detected: {len(results)}")
        
        # 示例4: 周期性统计报告
        if self.frame_count % 100 == 0:
            avg_detections = np.mean(self.detection_history[-100:])
            print(f"📊 Statistics: Average detections in last 100 frames: {avg_detections:.2f}")
        
        # 示例5: 可以返回处理后的结果或触发事件
        return {
            'frame_id': self.frame_count,
            'detection_count': len(results),
            'results': results
        }

# 可选实现 - 可视化器
@CALLBACK_REGISTRY.registryVisualizer("custom")
class CustomVisualizer:
    def __init__(self, config):
        self.config = config

    def __call__(self, original_frame, results):
        for v in results:
            cv2.putText(
                original_frame,
                f"CLASS: {v}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2,
            )
        return original_frame


if __name__ == "__main__":
    # 配置输入shape
    preprocess_config = PreprocessConfig(
        target_size=(224, 224),
    )

    engine = InferenceEngine(
        model="https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.15.0/hailo8/efficientnet_s.hef",
        source="/home/hk/github/hailo_tools/sources/test640.mp4",
        preprocess_config=preprocess_config,
        task_name="custom",
        show=True,
    )
    engine.run()
```

## 使用自定义模型

实现并注册模块后，就可以使用自定义模型了：

```python
from hailo_toolbox.inference import InferenceEngine

# 创建推理引擎
engine = InferenceEngine(
    model="models/my_custom_model.hef",  # 或 .onnx
    source="test_video.mp4",
    task_name="my_detection_model",      # 与注册时的名称一致
    show=True,
    save_dir="output/"
)

# 运行推理
engine.run()
```

## 最小实现要求

如果您只想快速验证模型，最少只需实现后处理器：

```python
# 最简后处理器
@CALLBACK_REGISTRY.registryPostProcessor("simple_model")
def simple_postprocess(results, original_shape=None):
    # 返回空结果（用于测试）
    return []

# 使用内置预处理器配置
from hailo_toolbox.process.preprocessor.preprocessor import PreprocessConfig

preprocess_config = PreprocessConfig(
    target_size=(640, 640),  # 模型输入尺寸
    normalize=False           # 是否归一化
)

engine = InferenceEngine(
    model="model.hef",
    source="video.mp4", 
    task_name="simple_model",
    preprocess_config=preprocess_config  # 使用内置预处理器
)
engine.run()
```

## 调试技巧

1. **添加日志**: 在关键步骤添加日志输出
```python
import logging
logger = logging.getLogger(__name__)

def __call__(self, image):
    logger.info(f"Input shape: {image.shape}")
    processed = self.process(image)
    logger.info(f"Output shape: {processed.shape}")
    return processed
```

2. **保存中间结果**: 调试时保存预处理后的图像
```python
def __call__(self, image):
    processed = self.process(image)
    # 调试时保存
    if self.debug:
        cv2.imwrite("debug_preprocessed.jpg", processed[0].transpose(1,2,0)*255)
    return processed
```

3. **单步测试**: 先用单张图像测试各个模块
```python
# 测试预处理
preprocessor = MyPreProcessor()
test_image = cv2.imread("test.jpg")
processed = preprocessor(test_image)
print(f"Preprocessed shape: {processed.shape}")
```

## 常见问题

**Q: 如何确定模型的输入输出格式？**
A: 可以使用 ONNX 工具查看模型信息，或参考模型的官方文档。

**Q: 预处理器输出的维度不对怎么办？**
A: 检查模型期望的输入格式，通常为 (N, C, H, W) 或 (N, H, W, C)。

**Q: 后处理器如何处理多输出模型？**
A: 遍历 results 字典中的所有输出，根据每个输出的含义分别处理。

**Q: 可以不实现可视化器吗？**
A: 可以，可视化器是可选的。不实现时系统会使用默认的空实现。

**Q: 可以不实现预处理器吗？**
A: 可以，系统提供了内置的通用预处理器。通过 `PreprocessConfig` 配置即可满足大多数模型的预处理需求。

**Q: 什么时候需要自定义预处理器？**
A: 当模型有特殊的预处理需求时，比如特殊的归一化方式、数据增强、或复杂的输入格式转换。

**Q: 事件处理器是做什么的？**
A: 事件处理器是一个可选模块，用于基于AI预测结果执行自定义业务逻辑，如目标计数、异常报警、数据记录等。它在后处理器之后执行。

**Q: 事件处理器会影响推理性能吗？**
A: 如果实现得当，影响很小。建议避免在事件处理器中执行耗时操作，对于复杂的业务逻辑可以考虑异步处理。

**Q: 如何在事件处理器中访问原始图像？**
A: 目前事件处理器只接收后处理结果。如果需要访问原始图像，可以在可视化器中实现相关逻辑，或者考虑扩展事件处理器的接口。

通过以上指南，您应该能够快速为自定义模型实现必要的处理模块。建议先实现最小功能版本（只需后处理器），验证流程后再逐步完善各个模块的功能。