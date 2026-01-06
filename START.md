# 🚀 快速启动指南

## 前置要求

- **Node.js** >= 16.0.0
- **Python** >= 3.8
- **npm** 或 **yarn**

## 首次启动步骤

### 1. 安装根目录依赖

```bash
npm install
```

这会安装 `concurrently` 工具，用于同时运行前后端。

### 2. 安装前后端依赖

```bash
# 同时安装前后端依赖
npm run install:all

# 或者分别安装
npm run install:backend   # 安装 Python 依赖
npm run install:frontend  # 安装 Node.js 依赖
```

### 3. 配置环境变量（可选）

#### 前端配置

在 `frontend/` 目录创建 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_MAPBOX_TOKEN=your_mapbox_token_here
```

#### 后端配置

在 `backend/` 目录创建 `.env` 文件（可选，有默认值）：

```env
HOST=0.0.0.0
PORT=8000
DEBUG=True
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 4. 启动开发服务器

```bash
npm run dev
```

## 🎉 启动成功

启动后，你会看到类似以下的输出：

```
[后端] INFO:     Started server process [12345]
[后端] INFO:     Waiting for application startup.
[后端] INFO:     Application startup complete.
[后端] INFO:     Uvicorn running on http://0.0.0.0:8000
[前端] VITE v7.x.x  ready in xxx ms
[前端] ➜  Local:   http://localhost:3000/
```

访问地址：
- 📱 **前端**: http://localhost:3000
- 🔧 **后端**: http://localhost:8000
- 📚 **API文档**: http://localhost:8000/docs

## 📝 可用命令

| 命令 | 说明 |
|------|------|
| `npm run dev` | 同时启动前后端（开发模式） |
| `npm run dev:backend` | 仅启动后端 |
| `npm run dev:frontend` | 仅启动前端 |
| `npm run install:all` | 安装所有依赖 |
| `npm run install:backend` | 安装后端依赖 |
| `npm run install:frontend` | 安装前端依赖 |
| `npm run build` | 构建前端生产版本 |

## 🛠️ 故障排除

### 问题1：端口被占用

如果端口 3000 或 8000 已被占用，可以：

**修改前端端口**（`frontend/vite.config.ts`）：
```typescript
server: {
  port: 3001,  // 改为其他端口
}
```

**修改后端端口**（`backend/.env`）：
```env
PORT=8001  # 改为其他端口
```

记得同时更新前端的 `VITE_API_BASE_URL`。

### 问题2：Python 模块未找到

确保已安装后端依赖：
```bash
cd backend
pip install -r requirements.txt
```

### 问题3：Node 模块未找到

确保已安装前端依赖：
```bash
cd frontend
npm install
```

### 问题4：CORS 错误

确保后端配置了正确的前端地址（`backend/app/config.py` 或 `.env`）：
```python
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]
```

## 💡 开发提示

1. **热重载**：前后端都支持热重载，修改代码后自动刷新
2. **日志区分**：使用 concurrently 时，前后端日志会用不同颜色显示
3. **停止服务**：按 `Ctrl+C` 停止所有服务
4. **单独调试**：可以使用 `npm run dev:backend` 或 `npm run dev:frontend` 单独启动某个服务

## 📚 更多信息

- 前端架构文档：`frontend/ARCHITECTURE.md`
- 后端架构文档：`backend/ARCHITECTURE.md`
- 项目主文档：`README.md`
