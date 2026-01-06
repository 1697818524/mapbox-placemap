# 后端项目架构规划

## 📁 项目结构

```
backend/
├── app/                          # 应用主目录
│   ├── __init__.py              # 应用初始化
│   ├── main.py                  # FastAPI 应用入口
│   ├── config.py                # 配置文件（环境变量、常量）
│   │
│   ├── models/                  # 数据模型（Pydantic）
│   │   ├── __init__.py
│   │   ├── image.py             # 图片相关模型
│   │   ├── scheme.py            # 配色方案模型
│   │   └── common.py            # 通用模型（响应、错误等）
│   │
│   ├── routers/                  # API 路由
│   │   ├── __init__.py
│   │   ├── images.py            # 图片搜索路由
│   │   └── schemes.py           # 配色方案生成路由
│   │
│   ├── services/                 # 业务逻辑服务层
│   │   ├── __init__.py
│   │   ├── image_search.py      # 图片搜索服务（百度图片）
│   │   ├── color_extraction.py  # 图片颜色提取服务
│   │   └── genetic_algorithm.py # 双目标遗传算法服务
│   │
│   ├── utils/                    # 工具函数
│   │   ├── __init__.py
│   │   ├── image_utils.py       # 图片处理工具（下载、格式转换等）
│   │   ├── color_utils.py       # 颜色处理工具（RGB/HEX转换、颜色空间转换等）
│   │   └── algorithm_utils.py   # 算法辅助工具
│   │
│   └── exceptions/               # 自定义异常
│       ├── __init__.py
│       └── custom_exceptions.py
│
├── requirements.txt              # Python 依赖包
├── .env.example                  # 环境变量示例
├── .gitignore                    # Git 忽略文件
└── ARCHITECTURE.md               # 架构文档（本文件）
```

## 🔧 模块说明

### 1. 应用入口 (`app/main.py`)

- FastAPI 应用实例创建
- 路由注册
- 中间件配置（CORS、异常处理等）
- 启动配置

### 2. 数据模型 (`app/models/`)

#### `image.py`
- `ImageSearchRequest`: 图片搜索请求模型
- `ImageResult`: 图片搜索结果模型
- `ColorExtractionRequest`: 颜色提取请求模型
- `ColorPalette`: 提取的配色方案模型

#### `scheme.py`
- `ColorSchemeItem`: 颜色方案项（对应前端）
- `ColorScheme`: 颜色方案（对应前端）
- `GenerateSchemesRequest`: 生成方案请求
- `GenerateSchemesResponse`: 生成方案响应
- `ColorSchemeWithId`: 带ID的颜色方案

#### `common.py`
- `APIResponse`: 统一API响应格式
- `ErrorResponse`: 错误响应格式

### 3. API 路由 (`app/routers/`)

#### `images.py`
- `GET /api/images/search`: 图片搜索接口
  - 参数：`keyword` (str), `count` (int)
  - 返回：`List[ImageResult]`
- `POST /api/images/extract-colors`: 从图片URL提取配色
  - 参数：`image_urls` (List[str])
  - 返回：`ColorPalette`

#### `schemes.py`
- `POST /api/schemes/generate`: 生成配色方案
  - 参数：`currentScheme` (ColorScheme), `count` (int)
  - 返回：`GenerateSchemesResponse`

### 4. 业务服务 (`app/services/`)

#### `image_search.py`
- `BaiduImageSearchService`: 百度图片搜索服务
  - `search(keyword: str, count: int) -> List[ImageResult]`
  - 使用 `httpx` 和 `BeautifulSoup4` 解析百度图片搜索结果

#### `color_extraction.py`
- `ColorExtractionService`: 颜色提取服务
  - `extract_from_urls(image_urls: List[str]) -> ColorPalette`
  - `extract_from_image(image: Image) -> List[Color]`
  - 使用 `PIL` (Pillow) 和 `numpy` 进行图片处理
  - 实现 K-means 聚类或主色调提取算法
  - 提取经典配色（5-10种主要颜色）

#### `genetic_algorithm.py`
- `GeneticAlgorithmService`: 双目标遗传算法服务
  - `generate_schemes(current_scheme: ColorScheme, count: int, color_palette: ColorPalette) -> List[ColorSchemeWithId]`
  - 双目标优化：
    1. **目标1**: 配色方案与提取颜色的相似度（颜色和谐度）
    2. **目标2**: 地图图层间的对比度和可读性
  - 使用 `deap` 或 `pymoo` 库实现遗传算法
  - 返回多个 Pareto 最优解

### 5. 工具函数 (`app/utils/`)

#### `image_utils.py`
- `download_image(url: str) -> Image`: 下载图片
- `resize_image(image: Image, max_size: int) -> Image`: 调整图片大小
- `validate_image_format(image: Image) -> bool`: 验证图片格式

#### `color_utils.py`
- `hex_to_rgb(hex: str) -> Tuple[int, int, int]`: HEX转RGB
- `rgb_to_hex(rgb: Tuple[int, int, int]) -> str`: RGB转HEX
- `rgb_to_lab(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]`: RGB转LAB颜色空间
- `color_distance(color1: Tuple, color2: Tuple, space: str = 'lab') -> float`: 计算颜色距离
- `color_harmony_score(colors: List[Color]) -> float`: 计算颜色和谐度

#### `algorithm_utils.py`
- `fitness_function_1(...)`: 目标1的适应度函数
- `fitness_function_2(...)`: 目标2的适应度函数
- `crossover(...)`: 交叉操作
- `mutation(...)`: 变异操作

## 📦 依赖包 (requirements.txt)

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
httpx>=0.25.0
beautifulsoup4>=4.12.0
pillow>=10.0.0
numpy>=1.24.0
scikit-learn>=1.3.0  # 用于K-means聚类
pymoo>=0.6.0  # 多目标优化算法库（或使用deap）
pydantic>=2.0.0
python-dotenv>=1.0.0
```

## 🔄 API 接口设计

### 1. 图片搜索接口

```python
GET /api/images/search?keyword={keyword}&count={count}

Response:
[
  {
    "url": "https://example.com/image.jpg",
    "thumbnail": "https://example.com/thumb.jpg",
    "title": "图片标题",
    "width": 1920,
    "height": 1080
  },
  ...
]
```

### 2. 颜色提取接口（可选，可集成到方案生成中）

```python
POST /api/images/extract-colors

Request Body:
{
  "image_urls": ["https://example.com/image1.jpg", ...]
}

Response:
{
  "colors": [
    {"hex": "#FF5733", "rgb": [255, 87, 51], "weight": 0.25},
    ...
  ],
  "dominant_colors": ["#FF5733", "#33FF57", ...]
}
```

### 3. 配色方案生成接口

```python
POST /api/schemes/generate

Request Body:
{
  "currentScheme": {
    "layers": [
      {"id": "water", "color": "#4A90E2", "weight": 0.1},
      ...
    ]
  },
  "count": 5
}

Response:
{
  "schemes": [
    {
      "id": "scheme-001",
      "layers": [
        {"id": "water", "color": "#5A9FE2", "weight": 0.1},
        ...
      ]
    },
    ...
  ]
}
```

## 🎯 核心算法流程

### 双目标遗传算法流程

1. **初始化种群**
   - 基于当前配色方案和提取的配色创建初始个体
   - 每个个体代表一个配色方案

2. **适应度评估**
   - **目标1**: 计算配色方案与提取颜色的相似度
     - 使用 LAB 颜色空间计算颜色距离
     - 考虑各图层的权重
   - **目标2**: 计算图层间的对比度和可读性
     - 确保相邻图层有足够的颜色对比
     - 考虑地图的可读性要求

3. **选择、交叉、变异**
   - 使用 NSGA-II 或类似的多目标优化算法
   - 保持 Pareto 前沿的多样性

4. **迭代优化**
   - 运行多代遗传算法
   - 返回 Pareto 最优解集

5. **结果返回**
   - 从 Pareto 前沿中选择 `count` 个方案
   - 为每个方案生成唯一ID

## 🔐 配置管理

### 环境变量 (.env)

```env
# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=False

# CORS配置
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# 图片搜索配置
BAIDU_IMAGE_SEARCH_URL=https://image.baidu.com/search/index
USER_AGENT=Mozilla/5.0...

# 图片处理配置
MAX_IMAGE_SIZE=2048
COLOR_EXTRACTION_K=8  # K-means聚类数量
MAX_COLORS_PER_PALETTE=10

# 遗传算法配置
POPULATION_SIZE=50
GENERATIONS=100
MUTATION_RATE=0.1
CROSSOVER_RATE=0.8
```

## 🚀 开发计划

### Phase 1: 基础框架
- [ ] 创建 FastAPI 应用结构
- [ ] 实现基础路由和模型
- [ ] 配置 CORS 和异常处理

### Phase 2: 图片搜索
- [ ] 实现百度图片搜索服务
- [ ] 实现图片下载和缓存
- [ ] 测试图片搜索接口

### Phase 3: 颜色提取
- [ ] 实现图片颜色提取算法
- [ ] 实现 K-means 聚类
- [ ] 测试颜色提取功能

### Phase 4: 遗传算法
- [ ] 实现双目标适应度函数
- [ ] 实现遗传算法核心逻辑
- [ ] 集成颜色提取和方案生成
- [ ] 测试方案生成接口

### Phase 5: 优化和测试
- [ ] 性能优化
- [ ] 错误处理完善
- [ ] 单元测试和集成测试
- [ ] API 文档完善
