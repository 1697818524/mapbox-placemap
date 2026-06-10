# PlaceMap 项目文档

PlaceMap 是一个“地方感地图生成”应用：用户搜索地点、收集当地图片或上传自己的图片，系统从图片集中提取语义与色彩候选，再把候选色迁移到 Mapbox 地图样式上，生成多套可比较的地方感配色方案。

## 当前项目逻辑

核心流程如下：

1. 地点搜索：前端通过 Mapbox 定位地点并显示地图。
2. 图片集构建：用户可以搜索当地图片，也可以上传本地图片；两类图片会合并为同一个样本图片集。
3. 样本入库：后端把远程图片下载到 `backend/data/ingest/{location}/`，上传图片也保存到同一类目录，并返回 `image_ids`。
4. Pipeline 构建：后端创建 pipeline job，按配置执行阴影处理、语义分割、超像素、语义分配、调色板聚类、方案生成等阶段。
5. 样式生成：前端点击“生成方案”后弹出参数面板，用户可设置种群数、迭代次数，以及“局部/全局”候选色使用方式。
6. 地图应用：方案生成后，前端把方案颜色写入 Mapbox style 的目标图层，右侧样式面板和地图同步变化。

当前参与方案生成的主要地图样式要素是：

| 控制项 | 前端 id | 默认语义 | Mapbox 目标 |
| --- | --- | --- | --- |
| 背景 | `background` | `base` | 背景/陆地底色 |
| 水体 | `water` | `water` | 水面、水道 |
| 一级道路 | `road-level-1` | `roadnet` | 高速、主干路 |
| 二级道路 | `road-level-2` | `roadnet` | 二级/三级道路、街道 |
| 三级道路 | `road-level-3` | `roadnet` | 小路、人行道、路径 |
| 建筑 | `building` | `architecture` | 建筑面 |
| 绿地/土地 | `landuse` | `green` | 土地利用、绿地 |

标签图层默认不参与方案生成。土地覆盖、国家公园等较杂要素目前隐藏，不作为主流程要素。

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Pinia、Element Plus、Mapbox GL JS
- 后端：FastAPI、Pydantic、OpenCV、Pillow、scikit-image、scikit-learn
- 运行编排：根目录 `npm` scripts 使用 `concurrently` 同时启动前后端

## 目录结构

```text
mapbox-placemap/
├─ README.md                 # 项目结构、运行方式、开发约定
├─ API.md                    # 接口文档；接口改动时必须同步维护
├─ PLAN.md                   # 功能计划/阶段记录
├─ START.md                  # 旧启动说明，可逐步收敛到 README
├─ package.json              # 根目录统一安装/启动脚本
├─ backend/
│  ├─ requirements.txt       # Python 依赖
│  ├─ data/
│  │  ├─ ingest/             # 入库图片
│  │  └─ jobs/               # pipeline job 产物
│  └─ app/
│     ├─ main.py             # FastAPI 入口，注册 images/pipeline/schemes 路由
│     ├─ config.py           # 后端配置和外部模型/脚本路径
│     ├─ models/             # Pydantic 请求/响应模型
│     ├─ routers/            # API 路由
│     ├─ repositories/       # job 元数据与产物索引
│     ├─ services/           # 图片搜索、入库、语义、聚类、方案生成等业务逻辑
│     └─ utils/              # 图片读取等工具
└─ frontend/
   ├─ package.json
   ├─ vite.config.ts         # Vite 配置，开发环境代理 /api 到 127.0.0.1:8000
   └─ src/
      ├─ api/                # 前端接口封装
      ├─ components/         # 地图、样式面板、图片集等组件
      ├─ config/             # API base、Mapbox、样式图层配置
      ├─ stores/             # Pinia 状态
      ├─ views/              # 页面
      └─ router/             # 前端路由
```

## 环境准备

建议使用 Node.js 18+ 和 Python 3.10+。

首次安装：

```powershell
cd D:\任务\JSJ\mapbox-placemap
npm install
npm run install:backend
npm run install:frontend
```

如果需要单独安装：

```powershell
cd D:\任务\JSJ\mapbox-placemap\backend
pip install -r requirements.txt

cd D:\任务\JSJ\mapbox-placemap\frontend
npm install
```

## 运行方式

推荐从项目根目录同时启动前后端：

```powershell
cd D:\任务\JSJ\mapbox-placemap
npm run dev
```

默认地址：

- 前端：`http://127.0.0.1:3000/`
- 后端：`http://127.0.0.1:8000/`
- 后端 OpenAPI：`http://127.0.0.1:8000/docs`

也可以分开启动：

```powershell
cd D:\任务\JSJ\mapbox-placemap\backend
python -m app.main

cd D:\任务\JSJ\mapbox-placemap\frontend
npm run dev
```

前端开发环境通过 `frontend/vite.config.ts` 把 `/api` 代理到 `http://127.0.0.1:8000`。如果生产环境需要指定后端地址，设置：

```powershell
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
```

## 构建和检查

前端构建：

```powershell
cd D:\任务\JSJ\mapbox-placemap\frontend
npm run build
```

后端语法检查：

```powershell
cd D:\任务\JSJ\mapbox-placemap\backend
python -m compileall app
```

## 关键配置

后端配置在 `backend/app/config.py`：

- `HOST` / `PORT`：后端监听地址和端口，默认 `0.0.0.0:8000`
- `CORS_ORIGINS`：允许访问后端的前端地址
- `PIPELINE_PYTHON_EXE`：执行外部脚本的 Python
- `SHADOW_SCRIPT_PATH`：阴影处理脚本路径
- `ONEFORMER_SCRIPT_PATH`：语义分割脚本路径
- `ONEFORMER_MODEL_DIR`：OneFormer 本地模型目录
- `ONEFORMER_DEVICE`：默认 `cuda`

前端地图样式配置在：

- `frontend/src/config/mapStyleLayers.ts`：右侧样式面板显示哪些地图要素，以及它们对应哪些 Mapbox layer。
- `frontend/src/config/placemapSemantics.ts`：前端样式 id 到后端语义的映射。
- `frontend/src/config/apiBase.ts`：前端请求后端的 base URL。

## 开发约定

1. 接口变更必须同步更新 `API.md`。
2. 新增或改名地图样式要素时，同时检查：
   - `frontend/src/config/mapStyleLayers.ts`
   - `frontend/src/config/placemapSemantics.ts`
   - `backend/app/services/scheme_generate.py`
   - `API.md` 中的方案生成字段说明
3. Pipeline 产物路径和字段变化时，同时检查：
   - `backend/app/models/pipeline.py`
   - `backend/app/routers/pipeline.py`
   - `frontend/src/api/pipeline.ts`
   - `API.md`
4. 前端样式调整后尽量在 `http://127.0.0.1:3000/` 真实查看，特别是地图和右侧样式面板是否同步。
5. 不要把 `backend/data/jobs/` 和 `backend/data/ingest/` 中的大量运行产物提交到仓库，除非明确需要示例数据。

