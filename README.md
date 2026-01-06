# 地方感地图生成项目

## 项目简介

本项目是一个基于地理视觉特征的地方感地图生成系统。系统通过搜索地点获取相关风景图片，对图片进行颜色分析提取经典配色方案，并运用双目标遗传算法生成优化的地图配色方案，实现基于地方视觉特征的地图样式个性化定制。

### 核心流程

1. **地点搜索**：用户搜索目标地点，系统通过 Mapbox Geocoding API 获取地理位置信息
2. **图片获取**：基于搜索地点，系统从百度图片搜索获取相关风景图片
3. **配色提取**：对获取的风景图片进行颜色分析，提取经典配色方案
4. **方案生成**：运用双目标遗传算法，基于提取的配色方案生成多个优化的地图配色方案
5. **样式应用**：将生成的配色方案应用到 Mapbox 地图的各个图层，实现个性化地图展示

## 项目结构

```
├── frontend/                    # 前端项目（Vue 3 + TypeScript）
│   ├── src/                    # 源代码目录
│   │   ├── api/                # API 请求模块
│   │   ├── components/         # Vue 组件
│   │   ├── composables/        # 组合式函数
│   │   ├── stores/             # Pinia 状态管理
│   │   └── ...
│   └── package.json
│
├── backend/                    # 后端项目（FastAPI + Python）
│   ├── app/                    # 应用主目录
│   │   ├── main.py            # FastAPI 应用入口
│   │   ├── config.py           # 配置文件
│   │   ├── models/             # 数据模型（Pydantic）
│   │   │   ├── image.py       # 图片相关模型
│   │   │   └── scheme.py      # 配色方案模型
│   │   ├── routers/           # API 路由
│   │   │   ├── images.py      # 图片搜索路由
│   │   │   └── schemes.py     # 配色方案生成路由
│   │   ├── services/          # 业务逻辑服务层
│   │   │   ├── image_search.py      # 图片搜索服务
│   │   │   ├── color_extraction.py  # 颜色提取服务
│   │   │   └── genetic_algorithm.py # 双目标遗传算法服务
│   │   └── utils/             # 工具函数
│   │       ├── image_utils.py # 图片处理工具
│   │       └── color_utils.py # 颜色处理工具
│   ├── requirements.txt        # Python 依赖包
│   └── ARCHITECTURE.md         # 后端架构文档
│
└── README.md                   # 项目说明
```

> 📖 详细的前端架构设计请参考 [frontend/ARCHITECTURE.md](./frontend/ARCHITECTURE.md)  
> 📖 详细的后端架构设计请参考 [backend/ARCHITECTURE.md](./backend/ARCHITECTURE.md)

## 快速开始

### 🚀 一键启动（推荐）

在项目根目录执行以下命令，可同时启动前后端：

1. **安装根目录依赖**（首次运行需要）：
```bash
npm install
```

2. **安装前后端依赖**（首次运行需要）：
```bash
npm run install:all
```

3. **同时启动前后端**：
```bash
npm run dev
```

启动后：
- 📱 **前端地址**: http://localhost:3000
- 🔧 **后端地址**: http://localhost:8000
- 📚 **API文档**: http://localhost:8000/docs

> 💡 使用 `concurrently` 工具同时运行前后端，日志会以不同颜色区分前后端输出

### 📦 分别启动（可选）

如果需要单独启动前后端，可以按照以下方式：

#### 后端服务

1. 进入后端目录：
```bash
cd backend
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 启动服务：
```bash
python -m app.main
# 或
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务将在 http://localhost:8000 启动

API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### 前端项目

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

3. 配置环境变量（可选）：
创建 `.env` 文件：
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_MAPBOX_TOKEN=your_mapbox_token_here
```

4. 启动开发服务器：
```bash
npm run dev
```

前端将在 http://localhost:3000 启动

## 功能特性

- 🗺️ 地图展示和交互（基于 Mapbox）
- 🎨 地图样式自定义（颜色方案配置）
- 🔍 地点搜索（Mapbox Geocoding）
- 🖼️ 图片搜索（百度图片搜索）
- 🌐 国际化支持（中文/英文）

## 技术栈

### 前端
- Vue 3
- TypeScript
- Element Plus
- Mapbox GL JS
- Pinia
- Vue I18n

### 后端
- FastAPI - Web 框架
- Python 3.8+
- httpx - HTTP 客户端（图片搜索）
- BeautifulSoup4 - HTML 解析
- Pillow (PIL) - 图片处理
- NumPy - 数值计算
- scikit-learn - K-means 聚类（颜色提取）
- pymoo - 多目标优化算法（遗传算法）

