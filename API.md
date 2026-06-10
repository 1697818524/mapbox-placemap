# PlaceMap 接口文档

本文档记录前后端正在使用的 API。以后新增、删除或修改接口时，必须同步更新本文档。

## 基础信息

- 后端服务：FastAPI
- 开发地址：`http://127.0.0.1:8000`
- 前端开发代理：`/api` -> `http://127.0.0.1:8000`
- OpenAPI 文档：`http://127.0.0.1:8000/docs`
- 前端接口封装目录：`frontend/src/api/`

通用错误格式通常位于 FastAPI `detail` 中：

```json
{
  "detail": {
    "success": false,
    "message": "错误说明",
    "error_code": "ERROR_CODE",
    "details": null
  }
}
```

## 健康检查

### `GET /`

返回后端基础信息。

响应示例：

```json
{
  "message": "地方感地图生成 API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### `GET /health`

检查后端是否可用。

响应示例：

```json
{
  "status": "ok"
}
```

## 图片接口

前端封装：`frontend/src/api/image.ts`

### `GET /api/images/search`

搜索当地图片。

Query 参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `keyword` | string | 是 | 搜索关键词，通常是地点名 |
| `count` | number | 否 | 返回数量，默认 `9`，范围 `1-50` |

响应：`ImageResult[]`

```json
[
  {
    "url": "https://example.com/image.jpg",
    "thumbnail": "https://example.com/thumb.jpg",
    "title": "图片标题",
    "width": 1920,
    "height": 1080
  }
]
```

### `GET /api/images/proxy`

代理远程图片，用于前端同源预览，避免部分图床 Referer 限制。

Query 参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `url` | string | 是 | 原始远程图片 URL |

响应：图片二进制内容。

限制：目前只允许代理常见图片域名后缀，如 `baidu.com`、`bdstatic.com`、`bdimg.com`、`wikimedia.org`。

### `POST /api/images/collect`

采集搜索图片，把远程图片下载到后端入库目录。

请求体：

```json
{
  "location": "Shanghai, China",
  "urls": [
    "https://example.com/image-1.jpg",
    "https://example.com/image-2.jpg"
  ]
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `location` | string | 是 | 地点名 |
| `urls` | string[] | 是 | 待下载图片 URL，最多 20 张 |

响应：

```json
{
  "location": "Shanghai, China",
  "image_ids": ["img_xxx"],
  "items": [
    {
      "image_id": "img_xxx",
      "filename": "img_xxx.jpg",
      "path": "backend/data/ingest/Shanghai,_China/img_xxx.jpg",
      "source": "search",
      "original_url": "https://example.com/image-1.jpg"
    }
  ]
}
```

### `POST /api/images/upload`

上传本地图片并入库。

Content-Type：`multipart/form-data`

Query 参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `location` | string | 是 | 地点名 |

Form 字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `files` | File[] | 是 | 图片文件，最多 20 张 |

响应结构同 `/api/images/collect`，`source` 通常为 `upload`。

## Pipeline 接口

前端封装：`frontend/src/api/pipeline.ts`

Pipeline 的 job 状态：

- `queued`
- `running`
- `succeeded`
- `failed`
- `cancelled`

Pipeline 阶段：

- `ingest`
- `shadow`
- `semantic`
- `superpixel`
- `cluster`
- `scheme`

### `POST /api/pipeline/jobs`

创建 pipeline job。

请求体：

```json
{
  "location": "Shanghai, China",
  "image_ids": ["img_xxx", "img_yyy"],
  "options": {
    "enable_shadow": true,
    "enable_semantic": true,
    "enable_superpixel": true,
    "enable_cluster": true,
    "enable_scheme": true,
    "semantic_model": "oneformer_cityscapes",
    "slic_n_segments": 240,
    "slic_compactness": 10,
    "cluster_k_min": 6,
    "cluster_k_max": 12,
    "scheme_count": 5,
    "enable_ga_scheme": false,
    "ga_population": 40,
    "ga_generations": 25,
    "scheme_background_semantic": "green"
  }
}
```

必填字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `location` | string | 地点名 |
| `image_ids` | string[] | 已入库图片 id，1-20 个 |

`options` 可省略，后端使用默认值。

响应：

```json
{
  "job_id": "job_20260610_xxx",
  "status": "queued",
  "message": "Pipeline job created"
}
```

### `GET /api/pipeline/jobs/{job_id}`

查询 job 状态。

响应字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `job_id` | string | 任务 id |
| `status` | string | 当前任务状态 |
| `location` | string | 地点名 |
| `image_ids` | string[] | 输入图片 id |
| `options` | object | 创建任务时的配置 |
| `current_stage` | string/null | 当前阶段 |
| `progress` | number | 总进度，0-100 |
| `stages` | object[] | 各阶段进度 |
| `error_code` | string/null | 失败代码 |
| `error_message` | string/null | 失败原因 |
| `palette_csv_count` | number | `cluster` 目录下 `palette_*.csv` 数量 |

### `GET /api/pipeline/jobs/{job_id}/artifacts`

查询 job 产物。

响应：

```json
{
  "job_id": "job_xxx",
  "items": [
    {
      "artifact_id": "artifact_xxx",
      "type": "palette_csv",
      "stage": "cluster",
      "path": "backend/data/jobs/job_xxx/cluster/palette_k12_water.csv",
      "url": null,
      "image_id": null,
      "extra": {}
    }
  ]
}
```

常见 `type`：

- `input_image`
- `shadow_image`
- `semantic_raw_id`
- `semantic_5class_id`
- `superpixel_label`
- `record_csv`
- `palette_csv`
- `scheme_json`

### `GET /api/pipeline/jobs/{job_id}/schemes`

读取 job 目录下已经生成的方案 JSON。

响应：

```json
{
  "job_id": "job_xxx",
  "schemes": [
    {
      "id": "scheme_job_xxx_rule_01",
      "layers": [
        {
          "id": "water",
          "color": "#CCDAD2",
          "weight": 0,
          "semantic": "water"
        }
      ],
      "scores": {
        "semantic_fit": 0.9,
        "readability": 0.7,
        "diversity": 0.3,
        "harmony": null,
        "place_representativeness": null
      }
    }
  ]
}
```

### `GET /api/pipeline/jobs/{job_id}/palette-semantics`

读取当前 job 聚类调色板中实际存在的候选语义。前端生成方案弹窗会用它判断局部模式下哪些语义没有候选色，并把这些语义选项置灰。

响应：

```json
{
  "job_id": "job_xxx",
  "semantics": ["green", "landmark", "water"]
}
```

说明：`semantics` 来自 `backend/data/jobs/{job_id}/cluster/palette_*.csv` 中的 `semantic` 字段。

### `POST /api/pipeline/jobs/{job_id}/run`

异步执行 pipeline job。接口立即返回 `202` 和当前 job 快照，后台继续执行。

前端应轮询 `GET /api/pipeline/jobs/{job_id}` 查看进度。

### `POST /api/pipeline/jobs/{job_id}/run-sync`

同步执行 pipeline job。接口会阻塞直到任务完成，适合调试，不适合大样本长期运行。

### `POST /api/pipeline/jobs/{job_id}/mock-start`

开发调试接口，把 job 状态模拟为 `running`。

## 方案生成接口

前端封装：`frontend/src/api/scheme.ts`

### `POST /api/schemes/generate`

基于当前地图样式和图片候选色生成多套配色方案。

请求体：

```json
{
  "currentScheme": {
    "layers": [
      {
        "id": "background",
        "color": "#F3EFEC",
        "weight": 0,
        "semantic": "base"
      },
      {
        "id": "water",
        "color": "#CCDAD2",
        "weight": 0,
        "semantic": "water"
      }
    ]
  },
  "count": 5,
  "job_id": "job_20260610_xxx",
  "population": 40,
  "generations": 25,
  "semantic_mode": "local",
  "layer_semantics": {
    "background": "base",
    "water": "water",
    "road-level-1": "roadnet",
    "road-level-2": "roadnet",
    "road-level-3": "roadnet",
    "building": "architecture",
    "landuse": "green"
  }
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `currentScheme.layers` | object[] | 是 | 当前地图样式要素 |
| `count` | number | 是 | 生成方案数量，1-20 |
| `job_id` | string/null | 否 | 使用指定 pipeline job 的聚类调色板 |
| `population` | number | 否 | 遗传算法种群数，默认 40，范围 8-200 |
| `generations` | number | 否 | 迭代次数，默认 25，范围 1-200 |
| `semantic_mode` | `local`/`global` | 否 | `local` 只使用对应语义候选，`global` 可使用所有语义候选 |
| `layer_semantics` | object | 否 | 局部模式下，前端样式 id 到语义的映射 |

当前主要样式 id：

- `background`
- `water`
- `road-level-1`
- `road-level-2`
- `road-level-3`
- `building`
- `landuse`

当前语义值：

- `base`
- `water`
- `roadnet`
- `architecture`
- `green`
- `landmark`

响应：

```json
{
  "schemes": [
    {
      "id": "scheme_job_xxx_rule_01",
      "layers": [
        {
          "id": "background",
          "color": "#F3EFEC",
          "weight": 0,
          "semantic": "base"
        },
        {
          "id": "water",
          "color": "#CCDAD2",
          "weight": 0,
          "semantic": "water"
        }
      ],
      "scores": {
        "semantic_fit": 0.928,
        "readability": 0.687,
        "diversity": 0.05,
        "harmony": null,
        "place_representativeness": null
      }
    }
  ]
}
```

## 维护提醒

接口改动时请同步检查：

- 后端模型：`backend/app/models/`
- 后端路由：`backend/app/routers/`
- 前端封装：`frontend/src/api/`
- 前端调用处：`frontend/src/components/`、`frontend/src/views/`
- 本文档：`API.md`
