# 后端项目说明

## 后端技术路线计划书（V1）

本计划书面向“地方感地图生成”后端实现，目标是把地点搜索、图片处理、语义与超像素融合、颜色聚类、遗传算法优化串成一条可复用、可观测、可扩展的服务化流水线。

### 1. 目标与范围

#### 1.1 业务目标

1. 支持用户基于地点检索与**自选**图片（搜索勾选子集、本地上传、**混用**，单次最多 **20 张**）构建计算批次；**不以长期保存用户原图为默认**（见 §1.3）。
2. 自动完成图像预处理、语义分析、颜色候选提取与方案优化。
3. 输出可直接应用到 Mapbox 图层的多套配色方案（schemes）。

#### 1.2 技术范围

- 后端职责：
  - 图片输入编排与校验（**目标**：见 §1.3，以临时输入 + 计算为主；**当前**：搜索落盘采集 + 上传至 ingest）
  - 图像算法流水线编排（去阴影、语义分割、超像素、聚类）
  - 多目标优化（遗传算法/NSGA-II）
  - 任务管理与结果服务（进度、日志、产物、方案）
- 不在本期范围：
  - 前端复杂交互设计
  - 生产级多租户权限系统

#### 1.3 图片输入与存储原则（产品定稿）

**用户侧图片来源（可多选混用）**

1. 地点搜索返回的图片列表中，用户**仅勾选一部分**参与后续计算（不要求整页全用）。  
2. 用户可**自行上传**本地图片，与搜索结果**混用**在同一批次内。  
3. 单次提交参与流水线计算的图片数量 **上限 20 张**（前后端均需校验：张数、总大小、超时策略）。

**服务端角色：以「计算服务」为主，不长期保存用户素材**

- **目标**：服务器**不**把用户图当作持久化素材库写入 `data/ingest` 等长期目录；仅在**单次任务生命周期**内持有输入（内存或临时目录），算完后**删除或自然过期**；持久化对象限于**任务元数据、算法中间产物、scheme JSON** 等可再生成或体积可控的数据（策略可再评审：中间产物也可改为仅内存流式输出 + 只落 schemes）。  
- **与当前实现的差距**：现版通过 `POST /api/images/collect` **下载 URL 至 `data/ingest/{location}/`**，pipeline 再按 `location` + `image_id` 解析本地路径，属于**落盘型 ingest**；前端当前为**整列表 URL 采集**，尚无「勾选子集 + 上传混选 + 20 张上限」的完整产品链路。  
- **演进方向（实现时可择一或组合）**  
  - **A**：`POST /api/pipeline/jobs` 扩展为 `multipart/form-data`（多文件 + 可选 URL 列表 + `options`），输入写入 **`data/jobs/{job_id}/input_tmp`**（或系统 `temp`），任务结束 **cleanup**。  
  - **B**：仍收 URL，但流水线内**按需下载到临时路径**，阶段结束删除，**不**写入长期 `data/ingest`。  
  - **C**：客户端直传对象存储，服务端仅持 **短期可读 URL** 拉流计算，不落自有磁盘副本。  
- **约束**：无论何种形态，均需考虑外链防盗链、版权合规、大文件内存峰值与并发限流。

#### 1.4 多目标配色优化任务需求（任务书定稿）

本节为 **scheme 阶段** 在「已有分语义聚类候选色」前提下，对 **NSGA-II + 双目标** 的正式需求，实现见 `app/services/color_objectives.py`、`app/services/ga_optimize.py`，由 `PipelineOptions` 开关控制。

**（1）触发条件**

- 创建任务时 `options.enable_ga_scheme == true`。  
- 且本 job 的 `cluster/` 目录下存在 **`palette_*.csv`**（与聚类阶段产物一致）。  
- 若不满足、或 NSGA **正常返回但解集为空**，**必须回退**至规则版 `scheme_generate`，保证流水线仍产出 schemes。若 NSGA **执行抛异常**，当前实现将 scheme 阶段标为失败并中断任务（与「空结果回退」不同）。

**（2）决策变量（编码）**

- 对每个在 `cluster` 中出现的**粗语义** \(s\)，在该公司候选簇中选取 **一个簇下标**（离散基因）。  
- 染色体长度 = 语义种类数；基因取值范围 = 该语义下行数（簇数）。  
- 解码后得到每语义 **一个代表色（RGB→HEX）** 及该簇 **`count`（像素量）**；`_load_palettes_from_cluster_dir` 已按 **count 降序** 排列候选；f1/f2 按簇大小对色对与语义一致性 **加权**（与实现一致）。

**（3）双目标（均最大化）**

| 符号 | 名称 | 定义要点 |
|------|------|----------|
| **f1** | **颜色和谐度** | 各语义代表色在 **CIELab→LCh** 下取色相，对**无序色对**与经典色相间隔模板（0°/30°/…/180°）匹配；权重为各语义所选簇的 **`count` 归一化**，色对按 **乘积 w_i·w_j** 加权平均。 |
| **f2** | **地方表征性** | 对齐 **`my_work/obj_cal/calculate_object1`**：**图-底**、**前景差异**、**CSV 语义一致性**；每语义代表色取 **count 最大** 簇，一致性项按各类 **count 总和** 加权；输出 `overall` ∈ [0,1]。 |

**（4）算法与输出**

- 使用 **NSGA-II**：非支配排序 + 拥挤度距离；交叉（均匀）+ 离散变异；精英策略与文献一致。  
- 从 **Pareto 第一前沿** 按拥挤度选取 **`scheme_count`** 个个体，解码为 **`ColorSchemeWithId`** 落盘。  
- **`SchemeScores`** 须写入 **`harmony`**（f1）、**`place_representativeness`**（f2），并保留既有字段兼容前端（如 `semantic_fit`/`readability` 可作映射字段）。

**（5）可配置参数（`PipelineOptions`）**

- `enable_ga_scheme`（默认 `false`）  
- `ga_population`（默认 `40`）、`ga_generations`（默认 `25`）  
- `scheme_background_semantic`（默认 **`green`**）：f2 中图-底关系的「底」语义，须落在当前染色体解码后的语义集合中，否则实现上回退为该集合字典序首项。

**（6）非功能需求**

- **确定性**：建议对 `job_id` 派生随机种子，便于同 job 复现。  
- **性能**：种群与代数默认偏保守，避免与 OneFormer 同进程时内存峰值叠加；后续可迁 worker。  
- **文档与联调**：Swagger 中 `PipelineJobCreateRequest.options` 须暴露上述字段；前端创建任务时若需默认走 GA，须在 `createJob` 中显式传 `options`（当前 UI 可为空＝规则版）。

### 2. 现状评估

- 已有能力（相对本计划书初稿已推进）：
  - FastAPI：`images`（搜索 / 上传 / 采集）、`pipeline`（创建任务、异步 `run`、同步 `run-sync`、产物、`GET .../schemes`）、`schemes`（`POST /generate` 规则版）
  - 流水线阶段：ingest → shadow → semantic（OneFormer）→ 五类语义 + 超像素 + records → 分语义 KMeans 聚类 → schemes 落盘（**默认规则版**；**可选** `enable_ga_scheme` 时走 **NSGA-II 双目标**，见 §1.4）
  - 任务元数据与产物索引：`JobRepository` + `data/jobs/_meta/jobs.json`；长任务默认 **BackgroundTasks**（非独立 worker 进程）
  - 前端：搜图 → 采集 → 跑 pipeline → 轮询进度 → 拉取 schemes 写入 store；配色项带 **图层 id + hex + 占比 + 粗语义 `semantic`**
- 仍待对齐计划或演进：
  - **NSGA-III / pymoo 化**、更多目标（如 my_work 中美学/KDE 目标）与算子调参（当前为 **NSGA-II + 双目标已实现**，见 §1.4）
  - **独立队列**（Celery/RQ）、任务取消、checkpoint 续跑、幂等缓存
  - **产物静态访问 URL**（`ArtifactItem.url`）、数据库持久化 Job
  - **肘部法 / LAB 聚类** 等与 `my_work/sample_process` 完全对齐的可选升级
  - **§1.3 输入模型**：勾选子集、上传与搜索混用、**20 张上限**、**不落盘长期保存用户原图**（改为 job 级临时目录或纯流式）

### 3. 总体架构设计

#### 3.1 分层架构

1. API 层（routers）
   - 请求校验、参数标准化、响应协议统一
2. 服务层（services）
   - 业务编排与算法调用
3. 任务层（workers）
   - 长任务异步执行与状态更新
4. 存储层（storage/repositories）
   - 文件管理、任务元数据、结果持久化

#### 3.2 推荐目录扩展

```text
backend/app/
├── routers/
│   ├── images.py
│   ├── pipeline.py      # 新增：任务创建/状态查询
│   └── schemes.py       # 新增：方案生成/查询
├── services/
│   ├── image_search.py
│   ├── image_ingest.py  # 新增：下载/上传/去重
│   ├── shadow_process.py
│   ├── semantic_segment.py
│   ├── superpixel.py
│   ├── semantic_assign.py
│   ├── palette_cluster.py
│   ├── color_objectives.py  # 和谐度 + 地方表征性（objective1 移植）
│   └── ga_optimize.py       # NSGA-II 离散染色体
├── workers/
│   └── tasks.py         # 可选：Celery/RQ 异步入口（当前用 FastAPI BackgroundTasks 代替）
└── repositories/
    └── job_repo.py      # 新增：任务状态与结果索引
```

### 4. 数据流与算法流水线

#### 4.1 端到端流程

1. 地点输入（Mapbox geocoding）与图片采集（搜索/上传）。
2. 预处理：`code.py` 去阴影，保留前后图。
3. 语义分割：OneFormer 生成 Cityscapes 语义图。
4. 语义对齐：Cityscapes 类别映射到 my_work 五类语义。
   - 约定：`sky -> water`（用于五类语义槽位兼容）
5. 超像素分割：SLIC 生成超像素标签。
6. 超像素语义赋值：对每个超像素做多数投票。
7. 分语义聚类：按五类语义分别提取候选色集。
8. 配色方案生成：**默认规则版**（按聚类调色板或 HSL 扰动）。若 `PipelineOptions.enable_ga_scheme=true` 且 `cluster/` 下存在 `palette_*.csv`，则使用 **NSGA-II** 在离散候选（每语义选一簇）上双目标优化：**f1 色相模板和谐度**（`app/services/color_objectives.py`）、**f2 地方表征性**（移植 `my_work/obj_cal/calculate_object1` 的图-底+差异+语义一致性）；输出 Pareto 第一前沿截断为 `scheme_count` 套方案。`scheme_background_semantic` 默认 `green`（图-底中的「底」语义）。
9. 输出 `schemes`（JSON，每项 layer 含 `id` / `color` / `weight` / 可选 `semantic`）+ 可选评分 + 全链路产物索引。

#### 4.2 产物目录规范（按 job）

```text
data/jobs/{job_id}/
├── input/              # 规划：任务级输入暂存（见 §1.3）；当前实现 ingest 阶段从 data/ingest/{location}/ 按 image_id 解析源图，产物索引中的 path 指向该路径
├── shadow/             # 去阴影结果
├── semantic_raw/       # Cityscapes 19类结果
├── semantic_5class/    # my_work 五类语义结果
├── superpixel/         # 超像素标签与可视化
├── records/            # superpixel-semantic records (csv/json)
├── cluster/            # 每语义类别聚类调色板
└── schemes/            # 规则版/后续 GA 输出方案（JSON）
```

#### 4.3 语义、记录与配色方案数据契约（V1）

本小节为**已定稿的字段语义**，实现以 `app/models/scheme.py`、`app/models/pipeline.py`、`app/services/semantic_assign.py` 为准。

**（1）语义两档**

| 层级 | 含义 | 落盘或中间表示 |
|------|------|----------------|
| **Cityscapes 19 类** | OneFormer 上色语义图，像素 RGB 对应官方调色板 | `semantic_raw/{image_id}.png`（RGB）；解码为 `train_id` 0–18 |
| **工程五类 + unknown** | 用于聚类、记录表、与 Mapbox 图层分组对齐 | `semantic_5class/{image_id}_id.png`（单通道 id 0–4）；`255` 表示 unknown；**约定 `sky -> water`**（与 Cityscapes 无独立 water 类兼容） |

五类 **字符串名**（与聚类 CSV、`coarse_semantic` 列一致）：`architecture`、`roadnet`、`green`、`landmark`、`water`。映射表见 `semantic_assign.CITYSCAPES_TO_COARSE_ID` / `COARSE_ID_TO_NAME`。

**（2）超像素—语义记录（records）**

- 文件：`records/all_superpixel_semantics.csv`
- 列：`image_id`, `segment`, `R`, `G`, `B`, `coarse_id`, `coarse_semantic`
- 含义：每个超像素块内对五类 id 图做**多数投票**得 `coarse_semantic`，RGB 为该块在原图上的均值。

**（3）分语义聚类调色板（cluster）**

- 文件：`cluster/palette_k{k}_{semantic}.csv`
- 列：`semantic`, `cluster_id`, `R`, `G`, `B`, `count`
- 含义：在同一 `semantic` 下对 records 中的 RGB 做 KMeans；`semantic` 为上述五类字符串（`unknown` 不参与）。

**（4）配色方案 `schemes`（API 与落盘 JSON 一致）**

- **`ColorScheme`**：`layers: ColorSchemeItem[]`
- **`ColorSchemeItem`**（每一项表示「一个可配色的地图图层条目」）：
  - **`id`**：**Mapbox 图层 id**（如 `water`、`road-street`、`building`）。仅用于与样式图层关联及前端套色，**不参与**聚类/GA 等数值计算。
  - **`color`**：HEX 字符串（如 `#RRGGBB`）。
  - **`weight`**：占比（权重），默认可与图层数均分。
  - **`semantic`**：可选；粗语义类型，取值与五类字符串一致。用于**展示、追溯与分割结果对齐**；算法实现**可不读取**该字段，仅通过 `id -> semantic` 映射表推断亦可。
- **`ColorSchemeWithId`**：多套方案之一，含 **`id`**（方案 id）、`layers`、`scores`（规则版填 `semantic_fit` / `readability` / `diversity`；**GA 开启时另含** `harmony`、`place_representativeness`，见 §1.4）。
- **图层 id → `semantic` 映射**：前后端共用同一套字典（后端 `scheme_generate.LAYER_ID_TO_SEMANTIC`，前端 `config/placemapSemantics.ts`），保证与 MapStyle 可配置图层一致。

**（5）任务与产物索引**

- **`PipelineJob`**：`job_id`, `status`, `location`, `image_ids`, `options`, `current_stage`, `progress`, `stages[]`, 错误与时间戳。
- **`ArtifactItem`**：`artifact_id`, `type`（见 `ArtifactType` 枚举）, `stage`, `path`（本地路径）, 可选 `url`（静态访问未接时多为空）, `image_id`, `extra`。

#### 4.4 与 `my_work` 参考逻辑的对照（演进路线）

仓库 **`my_work`**（与 `mapbox-placemap` 同级，如 `e:\code\my_work`）承载较早的「颜色优化 + 地区风格预处理」试验代码，本项目的**阶段划分与数据形态**尽量与其对齐，便于迁移算法与目标函数。

| 维度 | `my_work/sample_process`（典型地区预处理） | `my_work` 根目录（Flask 颜色优化） | **本仓库 `mapbox-placemap`（当前）** |
|------|---------------------------------------------|-------------------------------------|----------------------------------------|
| 语义 | 细粒度→粗粒度映射、独立颜色对照表 | CSV 支持 `sem` 列与类型筛选 | Cityscapes 19 → **五类**（`semantic_assign`），无单独对照表文件 |
| 超像素 | SLIC、记录 `all_superpixel_semantics` | — | SLIC + 同上 CSV 列结构 |
| 聚类 | 肘部法 + **LAB** KMeans、按语义输出 `palette_k*` | — | **RGB** KMeans、`k` 由样本量启发式；输出 `palette_k*_{semantic}.csv` |
| 优化 | — | **LAB** 映射、**NSGA-III**、多目标（美学/地方偏好/情感等）、KDE 可视化 | **规则版 scheme** + **可选 NSGA-II 双目标**（`ga_optimize` / `color_objectives`，见 §1.4）；演进项：NSGA-III、更多目标，逻辑可对齐 `main_v2_optimized.py`、`obj_cal/` |
| 输入 | 地区目录 `img` + `seg_img` | 图 + 同名 CSV（`r,g,b` 等） | **地点 + 搜索/上传图** → ingest → job |

**迁移建议（写入后续里程碑即可）**

1. **聚类**：可选引入肘部法、`LAB` 空间与 `sample_process` 的 `ElbowClustering` 思路，与现有 `palette_cluster` 并存或替换。
2. **优化**：将 `my_work` 中 `selected_colors` / `target_colors` 或 `palette_entries` 与当前 **`ColorSchemeItem`**（含 `semantic`）对接；目标函数与 NSGA 版本（II vs III）需单独评审后落库。
3. **可视化**：KDE、调色板汇总图可作为 **artifact 扩展类型** 或独立静态路由，不阻塞 API V1。

### 5. API 路线图（后端）

#### 5.1 输入层接口

> **与 §1.3 对齐**：下列接口为**当前落盘实现**；演进后应增加「仅任务临时目录 / multipart 直传 job」等形态，并统一 **≤20 张** 校验。

- `POST /api/images/upload`
  - 上传多张图片，返回 `image_ids`（当前写入 `data/ingest/{location}/`）
- `POST /api/images/collect`
  - 输入：地点 + 搜索图 URL 列表
  - 输出：落盘后的 `image_ids`（**计划改为**不落长期 ingest，见 §1.3）

#### 5.2 任务层接口

- `POST /api/pipeline/jobs`
  - 输入：`location`, `image_ids`, `options`
  - 输出：`job_id`、`status`
- `GET /api/pipeline/jobs/{job_id}`
  - 返回：阶段状态、进度、错误信息
- `GET /api/pipeline/jobs/{job_id}/artifacts`
  - 返回：中间与最终产物索引
- `POST /api/pipeline/jobs/{job_id}/run`
  - **异步**：`202`，后台执行流水线（FastAPI `BackgroundTasks`）
- `POST /api/pipeline/jobs/{job_id}/run-sync`
  - **同步**：阻塞至结束，便于脚本/调试
- `GET /api/pipeline/jobs/{job_id}/schemes`
  - 读取已落盘的 `scheme_json` 产物，返回 `job_id` + `schemes[]`（结构与 `ColorSchemeWithId` 一致）

#### 5.3 方案层接口

- `POST /api/schemes/generate`
  - 输入：`currentScheme`（`layers[]` 每项含 `id`, `color`, `weight`，可选 `semantic`）、`count`、可选 **`job_id`**（有则优先用该任务 `cluster/` 下聚类调色板）
  - 输出：`schemes[]`（`ColorSchemeWithId`，可含 `scores`）
- `GET /api/schemes/{scheme_id}`（**未实现**，仍可作为统一资源入口的演进项）

### 6. 任务编排与执行策略

> **当前实现**：阶段状态写入 `PipelineJob.stages` 与 `ArtifactItem` 列表；**无** checkpoint 续跑与幂等缓存；长任务由 **`POST .../run` + BackgroundTasks** 承担（见 §5.2）。

1. 任务模型：
   - `queued -> running -> succeeded/failed/cancelled`
2. 阶段化执行：
   - 每阶段写 checkpoint，失败可续跑（**目标**，未实现）
3. 幂等与缓存：
   - 相同输入签名复用历史结果，减少重复计算（**目标**，未实现）
4. 执行器建议：
   - 本地开发：FastAPI BackgroundTasks 或 RQ（**BackgroundTasks 已用**）
   - 中期演进：Celery + Redis

### 7. 质量保障与可观测

#### 7.1 指标

- 每阶段耗时（去阴影/语义/超像素/聚类/**scheme 规则版 / NSGA-II**）
- 任务成功率与失败原因分布
- 每语义类别样本数与候选色数量
- 方案评分分布：`SchemeScores` 中 **harmony**、**place_representativeness**（GA 开启时）；规则版仍为 semantic_fit / readability / diversity 等

#### 7.2 日志与追踪

- 统一 job_id 全链路日志
- 每个阶段记录输入摘要和输出摘要
- 算法参数版本化，保证可复现

### 8. 里程碑计划

#### M1：基础可跑通（1周）

- 完成上传接口与图片采集入库
- 打通去阴影 + 单图语义分割
- 建立 job 目录与状态接口

#### M2：语义与颜色中间层（1周）

- 完成 Cityscapes -> 五类语义映射
- 完成超像素与语义投票融合
- 输出 records 与基础统计

#### M3：候选色与方案生成（1周）

- 完成分语义聚类服务
- 完成 schemes 生成接口（规则版 + **可选 NSGA-II 双目标**，见 §1.4）

#### M4：优化与联调（1周）

- **进行中/可选**：NSGA-III、第三目标、与 `my_work` 美学模块对齐；**已完成基线**：NSGA-II + f1 和谐度 + f2 地方表征性
- 完成前后端联调与参数调优（含 **`enable_ga_scheme` 与 `ga_*` 参数** 暴露）
- 补充测试与错误恢复机制

### 9. 风险与应对

1. 图片来源不稳定（外部搜索接口波动）
   - 应对：失败重试 + 本地缓存 + 用户上传兜底
2. 语义类别缺失（Cityscapes 无 water）
   - 应对：映射策略固定为 `sky -> water`，并在文档标注
3. 计算耗时长
   - 应对：异步任务 + 阶段缓存 + 批处理
4. 方案质量主观波动
   - 应对：引入可解释评分与人工可选方案池

### 10. 验收标准（V1）

1. 输入 20 张图以内，能稳定生成至少 3 套可用 schemes。
2. 全流程可追踪，每个阶段有可读日志和产物。
3. 失败任务可定位到具体阶段；**自动重试接口**仍为演进项（见 §6）。
4. API 文档完整，前端可独立联调。
5. **（GA 任务）** 在 `enable_ga_scheme=true` 且存在 `cluster/palette_*.csv` 时：产出 schemes 的 `scores` 中含 **`harmony`** 与 **`place_representativeness`**；前沿解互不支配（抽样检查 f1/f2）；无聚类产物或优化失败时 **自动回退规则版** 且任务仍为 `succeeded`（除非 scheme 阶段整体异常）。

### 11. 本周执行清单（可直接开发）

以下清单按“先跑通、再完善”排序，建议按 Day1-Day5 推进。

#### Day 1：任务骨架与目录规范

**目标：** 建立 job 生命周期和产物目录，保证后续流程可追踪。

- 新增文件：
  - `app/models/pipeline.py`
  - `app/repositories/job_repo.py`
  - `app/routers/pipeline.py`
- 关键工作：
  - 定义 `PipelineJob`、`PipelineJobStatus`、`PipelineStageProgress` 模型
  - 实现任务创建与状态查询：
    - `POST /api/pipeline/jobs`
    - `GET /api/pipeline/jobs/{job_id}`
  - 实现 job 目录初始化：
    - `data/jobs/{job_id}/{input,shadow,semantic_raw,semantic_5class,superpixel,records,cluster,schemes}`

#### Day 2：图片输入链路（搜索 + 上传）

**目标：** 统一图片输入，沉淀为可复用 `image_ids`。

- 新增文件：
  - `app/services/image_ingest.py`
  - `app/routers/uploads.py`（或扩展 `images.py`）
- 关键工作：
  - 增加上传接口：`POST /api/images/upload`
  - 增加采集接口：`POST /api/images/collect`
  - 下载/上传后的文件统一落盘到 job 输入目录
  - 增加最小去重（按 URL 或文件 hash）

#### Day 3：预处理 + 语义分割阶段

**目标：** 打通图像算法前两阶段，拿到语义输出。

- 新增文件：
  - `app/services/shadow_process.py`
  - `app/services/semantic_segment.py`
- 关键工作：
  - 封装 `code.py` 为服务调用（输入图 -> 去阴影图）
  - 封装 OneFormer 推理（输出 `semantic_raw`）
  - 增加 Cityscapes 到五类语义映射（约定 `sky -> water`）
  - 保存：
    - 原始 19 类 id 图
    - 五类 id 图（及可选彩色可视化）

#### Day 4：超像素融合 + 颜色候选聚类

**目标：** 从语义图中得到可优化的颜色候选集。

- 新增文件：
  - `app/services/superpixel.py`
  - `app/services/semantic_assign.py`
  - `app/services/palette_cluster.py`
- 关键工作：
  - SLIC 超像素分割并保存 labels
  - 每个超像素做语义多数投票，生成 records：
    - `image_id, segment, R, G, B, coarse_id, coarse_semantic`（见 §4.3）
  - 按五类语义分别聚类，输出候选色 CSV/JSON

#### Day 5：方案生成接口（v1）

**目标：** 给前端可消费的 schemes 结果。

- 涉及文件（**规则版 + NSGA-II 已落地**，见 §1.4）：
  - `app/routers/schemes.py`
  - `app/services/scheme_generate.py`（规则版）
  - `app/services/color_objectives.py`、`app/services/ga_optimize.py`
  - `app/models/scheme.py`
- 关键工作（与 §4.3、§1.4 一致）：
  - `POST /api/schemes/generate`：`currentScheme`、`count`、可选 `job_id`
  - **`POST /api/pipeline/jobs`**：`options.enable_ga_scheme`、`ga_population`、`ga_generations`、`scheme_background_semantic` 等（见 §12.2 扩展）
  - 单套方案结构 **`ColorSchemeWithId`**：`id`（方案 id）、`layers[]`、`scores?`（含 **`harmony` / `place_representativeness`** 当 GA 开启）
  - **`ColorSchemeItem`**：`id`（Mapbox 图层 id）、`color`、`weight`、**`semantic?`**（粗语义五类字符串）
  - Pipeline 成功后落盘 `schemes/*.json`，并提供 **`GET /api/pipeline/jobs/{job_id}/schemes`** 聚合读取
  - `GET /api/pipeline/jobs/{job_id}/artifacts`（产物索引）

#### 本周交付物（Definition of Done）

1. 从地点到 schemes 的最小闭环可跑通（20 张图以内）。
2. 每个阶段有中间产物可查、有状态可看、有错误可定位。
3. API 可在 Swagger 中完整调试。
4. 前端可拿到 3+ 套候选配色方案进行预览。

#### 参数建议（V1 默认值）

- SLIC：
  - `n_segments=300~600`（按分辨率自适应）
  - `compactness=10`
- 聚类：
  - 每语义 `k=6~20` 自动选取
- **NSGA-II（与实现一致，任务书）**：
  - `ga_population=40`（可调）
  - `ga_generations=25`（可调）
  - 交叉概率约 0.9、基因变异概率约 0.15（见 `ga_optimize.py`，后续可抽为 `PipelineOptions`）
- 历史参考（泛 GA 文献，非当前代码硬编码）：
  - `population=50`、`generations=80`、`mutation_rate=0.1`、`crossover_rate=0.8`

#### 风险提示（本周重点规避）

1. 算法阶段串联耗时长：必须异步执行，禁止同步阻塞 API。
2. 外部图源不稳定：搜索失败时要允许“纯上传模式”继续执行。
3. 语义类别不平衡：当某语义像素过少时要允许降级跳过，不阻断全流程。

### 12. Day1 详细字段设计（pipeline 模型与 API 契约）

本节提供可直接编码的字段定义，优先保证“可创建任务、可查进度、可查产物”。

#### 12.1 枚举定义（建议）

- `PipelineJobStatus`
  - `queued`
  - `running`
  - `succeeded`
  - `failed`
  - `cancelled`
- `PipelineStageName`
  - `ingest`
  - `shadow`
  - `semantic`
  - `superpixel`
  - `cluster`
  - `scheme`
- `ArtifactType`
  - `input_image`
  - `shadow_image`
  - `semantic_raw_id`
  - `semantic_5class_id`
  - `superpixel_label`
  - `record_csv`
  - `palette_csv`
  - `scheme_json`

#### 12.2 数据模型（Pydantic）

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class PipelineOptions(BaseModel):
    enable_shadow: bool = True
    enable_semantic: bool = True
    enable_superpixel: bool = True
    enable_cluster: bool = True
    enable_scheme: bool = True
    semantic_model: str = "oneformer_cityscapes"
    slic_n_segments: int = 400
    slic_compactness: float = 10.0
    cluster_k_min: int = 6
    cluster_k_max: int = 20
    scheme_count: int = 5
    # §1.4 NSGA-II 双目标（和谐度 + 地方表征性）
    enable_ga_scheme: bool = False
    ga_population: int = 40
    ga_generations: int = 25
    scheme_background_semantic: str = "green"

class PipelineJobCreateRequest(BaseModel):
    location: str = Field(..., min_length=1)
    image_ids: List[str] = Field(..., min_length=1)
    options: PipelineOptions = PipelineOptions()

class PipelineStageProgress(BaseModel):
    stage: str
    status: str
    progress: float = Field(0, ge=0, le=100)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    message: Optional[str] = None

class PipelineJob(BaseModel):
    job_id: str
    status: str
    location: str
    image_ids: List[str]
    options: PipelineOptions
    current_stage: Optional[str] = None
    progress: float = Field(0, ge=0, le=100)
    stages: List[PipelineStageProgress] = []
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

class ArtifactItem(BaseModel):
    artifact_id: str
    type: str
    stage: str
    path: str
    url: Optional[str] = None
    image_id: Optional[str] = None
    extra: Dict[str, Any] = {}

class PipelineArtifactsResponse(BaseModel):
    job_id: str
    items: List[ArtifactItem]
```

#### 12.3 API 契约（v1）

##### A. 创建任务

- `POST /api/pipeline/jobs`
- Request Body:

```json
{
  "location": "fuzimiao",
  "image_ids": ["img_001", "img_002"],
  "options": {
    "enable_shadow": true,
    "enable_semantic": true,
    "enable_superpixel": true,
    "enable_cluster": true,
    "enable_scheme": true,
    "semantic_model": "oneformer_cityscapes",
    "slic_n_segments": 400,
    "slic_compactness": 10.0,
    "cluster_k_min": 6,
    "cluster_k_max": 20,
    "scheme_count": 5,
    "enable_ga_scheme": false,
    "ga_population": 40,
    "ga_generations": 25,
    "scheme_background_semantic": "green"
  }
}
```

> **`enable_scheme` 须为 `true`** 才会进入 scheme 阶段；在此前提下若 `enable_ga_scheme: true` 且满足 §1.4 条件则走 NSGA-II，否则规则版。详见 **§1.4**。

- Response 200:

```json
{
  "job_id": "job_20260429_001",
  "status": "queued",
  "message": "Pipeline job created"
}
```

##### B. 查询任务状态

- `GET /api/pipeline/jobs/{job_id}`
- Response 200:

```json
{
  "job_id": "job_20260429_001",
  "status": "running",
  "location": "fuzimiao",
  "current_stage": "semantic",
  "progress": 46.5,
  "stages": [
    {"stage": "ingest", "status": "succeeded", "progress": 100},
    {"stage": "shadow", "status": "succeeded", "progress": 100},
    {"stage": "semantic", "status": "running", "progress": 39.5}
  ],
  "created_at": "2026-04-29T17:22:00+08:00",
  "updated_at": "2026-04-29T17:24:31+08:00"
}
```

##### C. 查询任务产物

- `GET /api/pipeline/jobs/{job_id}/artifacts`
- Response 200:

```json
{
  "job_id": "job_20260429_001",
  "items": [
    {
      "artifact_id": "art_001",
      "type": "semantic_5class_id",
      "stage": "semantic",
      "path": "data/jobs/job_20260429_001/semantic_5class/img_001_id.png",
      "url": "/static/jobs/job_20260429_001/semantic_5class/img_001_id.png",
      "image_id": "img_001",
      "extra": {"width": 1024, "height": 768}
    }
  ]
}
```

##### D. 错误码建议

- `PIPELINE_JOB_NOT_FOUND`
- `PIPELINE_INVALID_OPTIONS`
- `PIPELINE_STAGE_FAILED`
- `PIPELINE_ARTIFACT_NOT_FOUND`

#### 12.4 JobRepository 最小接口（建议）

```python
class JobRepository:
    def create_job(self, payload: PipelineJobCreateRequest) -> PipelineJob: ...
    def get_job(self, job_id: str) -> PipelineJob: ...
    def update_job_status(self, job_id: str, status: str, **kwargs) -> None: ...
    def update_stage(self, job_id: str, stage: str, status: str, progress: float, message: str | None = None) -> None: ...
    def add_artifact(self, job_id: str, artifact: ArtifactItem) -> None: ...
    def list_artifacts(self, job_id: str) -> list[ArtifactItem]: ...
```

#### 12.5 Day1 完成判定（Checklist）

- [ ] 可以创建 pipeline 任务并返回 `job_id`
- [ ] 可以查询状态并看到 stage 级进度
- [ ] 可以查询产物索引（即使只有 input/shadow 也可）
- [ ] Swagger 可完整调试上述 3 个接口
- [ ] README 的字段与代码模型一致

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件（参考 `.env.example`）：

```env
HOST=0.0.0.0
PORT=8000
DEBUG=True

CORS_ORIGINS=http://localhost:3000,http://localhost:5173

BAIDU_IMAGE_SEARCH_URL=https://image.baidu.com/search/index
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
REQUEST_TIMEOUT=10

MAX_IMAGE_SIZE=2048
MAX_IMAGES_PER_SEARCH=50
```

### 3. 启动服务

```bash
# 方式1：直接运行
python -m app.main

# 方式2：使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务将在 http://localhost:8000 启动

### 4. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 接口

### 图片搜索

```
GET /api/images/search?keyword={keyword}&count={count}
```

**参数：**
- `keyword` (必需): 搜索关键词
- `count` (可选): 返回图片数量，默认9，最大50

**响应示例：**
```json
[
  {
    "url": "https://example.com/image.jpg",
    "thumbnail": "https://example.com/thumb.jpg",
    "title": "风景图片",
    "width": 1920,
    "height": 1080
  }
]
```

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置文件
│   ├── models/              # 数据模型
│   │   ├── image.py
│   │   └── common.py
│   ├── routers/             # API 路由
│   │   └── images.py
│   ├── services/            # 业务逻辑服务
│   │   └── image_search.py
│   └── utils/               # 工具函数
│       └── image_utils.py
├── requirements.txt          # 依赖包
└── README.md                # 本文件
```

## 开发说明

### 代码规范

- 使用 Python 3.8+
- 遵循 PEP 8 代码规范
- 使用类型提示（Type Hints）
- 使用 Pydantic 进行数据验证

### 测试

```bash
# 运行测试（待实现）
pytest
```

## 注意事项

1. 百度图片搜索接口可能会变化，如果搜索失败，可能需要更新解析逻辑
2. 建议添加请求缓存机制，避免频繁请求
3. 生产环境建议添加请求限流和错误重试机制
