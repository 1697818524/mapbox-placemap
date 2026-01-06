# 后端项目说明

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
{
  "success": true,
  "message": "成功搜索到 9 张图片",
  "data": [
    {
      "url": "https://example.com/image.jpg",
      "thumbnail": "https://example.com/thumb.jpg",
      "title": "风景图片",
      "width": 1920,
      "height": 1080
    }
  ]
}
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
