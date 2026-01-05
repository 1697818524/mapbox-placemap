# 项目模块化说明文档

## 📁 目录结构

```
frontend/src/
├── api/                    # API 请求模块
│   ├── index.ts           # API 统一导出
│   ├── mapbox.ts          # Mapbox API
│   └── image.ts           # 图片搜索 API
├── assets/                 # 静态资源
├── components/             # 组件
│   ├── map/               # 地图相关组件
│   └── layout/            # 布局组件
├── composables/           # 组合式函数
│   ├── index.ts           # Composables 统一导出
│   ├── useDebounce.ts     # 防抖函数
│   ├── useGeocoding.ts    # 地理编码搜索
│   └── useMap.ts           # 地图相关逻辑
├── config/                # 配置文件
│   ├── index.ts           # 配置统一导出
│   ├── constants.ts       # 常量配置
│   └── mapbox.ts          # Mapbox 配置
├── i18n/                  # 国际化
├── router/                # 路由
├── stores/                # 状态管理
├── types/                 # 类型定义
│   ├── index.ts           # 类型统一导出
│   ├── api.ts             # API 类型
│   └── map.ts             # 地图类型
├── utils/                 # 工具函数
│   ├── index.ts           # 工具函数统一导出
│   ├── storage.ts         # 本地存储工具
│   └── validation.ts      # 验证工具
└── views/                 # 页面视图
```

## 🔧 模块说明

### 1. API 模块 (`src/api/`)

统一管理所有 API 请求，便于维护和测试。

- `mapbox.ts`: Mapbox 地理编码 API
- `image.ts`: 图片搜索 API

**使用示例：**
```typescript
import { geocodingApi, imageApi } from '@/api'

// 搜索地点
const results = await geocodingApi.search('北京')

// 搜索图片
const images = await imageApi.search('北京', 9, '图片')
```

### 2. Composables 模块 (`src/composables/`)

提取可复用的组合式函数，提高代码复用性。

- `useMap.ts`: 地图初始化和管理
- `useGeocoding.ts`: 地理编码搜索逻辑
- `useDebounce.ts`: 防抖函数

**使用示例：**
```typescript
import { useMap, useGeocoding, useDebounce } from '@/composables'

// 在组件中使用
const mapContainer = ref<HTMLDivElement | null>(null)
const { map } = useMap(mapContainer)
```

### 3. Config 模块 (`src/config/`)

集中管理配置常量，避免硬编码。

- `constants.ts`: 应用常量（地图配置、API 配置等）
- `mapbox.ts`: Mapbox 相关配置

**使用示例：**
```typescript
import { MAP_CONFIG, API_CONFIG } from '@/config'

const center = MAP_CONFIG.DEFAULT_CENTER
const delay = API_CONFIG.DEBOUNCE_DELAY
```

### 4. Utils 模块 (`src/utils/`)

通用工具函数，可在项目任何地方使用。

- `storage.ts`: 本地存储封装（支持类型安全）
- `validation.ts`: 数据验证函数

**使用示例：**
```typescript
import { storage, validators } from '@/utils'

// 存储数据
storage.set('key', { name: 'value' })

// 获取数据
const data = storage.get<{ name: string }>('key')

// 验证数据
if (validators.isValidSearchQuery(query)) {
  // ...
}
```

### 5. Types 模块 (`src/types/`)

统一的类型定义，确保类型安全。

- `api.ts`: API 相关类型
- `map.ts`: 地图相关类型

**使用示例：**
```typescript
import type { GeocodeFeature, ImageResult } from '@/types'

const location: GeocodeFeature = { ... }
```

## 📝 代码规范

### 命名规范

- **组件**: PascalCase (如 `MapDisplay.vue`)
- **文件/目录**: kebab-case (如 `map-display.vue`)
- **变量/函数**: camelCase (如 `searchQuery`)
- **常量**: UPPER_SNAKE_CASE (如 `MAP_CONFIG`)
- **类型/接口**: PascalCase (如 `MapState`)

### 组件结构规范

```vue
<template>
  <!-- 模板内容 -->
</template>

<script setup lang="ts">
// 1. 导入依赖
import { ref, computed, onMounted } from 'vue'

// 2. 导入类型
import type { MapState } from '@/types'

// 3. Props 定义
interface Props {
  // ...
}
const props = defineProps<Props>()

// 4. Emits 定义
const emit = defineEmits<{
  // ...
}>()

// 5. Composables
const { map } = useMap()

// 6. 响应式数据
const count = ref(0)

// 7. 计算属性
const doubled = computed(() => count.value * 2)

// 8. 方法
const handleClick = () => {
  // ...
}

// 9. 生命周期
onMounted(() => {
  // ...
})
</script>

<style scoped>
/* 样式 */
</style>
```

## 🚀 使用建议

1. **优先使用 Composables**: 将可复用的逻辑提取到 composables 中
2. **统一使用配置**: 不要硬编码常量，使用 `config` 模块
3. **类型安全**: 充分利用 TypeScript 类型系统
4. **API 统一管理**: 所有 API 调用都通过 `api` 模块
5. **工具函数复用**: 使用 `utils` 模块中的工具函数

## 🔍 代码检查

项目已配置 ESLint 和 Prettier，运行以下命令进行检查：

```bash
# 检查代码
npm run lint

# 格式化代码
npm run format
```

## 📦 环境变量

在项目根目录创建 `.env` 文件（参考 `.env.example`）：

```env
VITE_MAPBOX_TOKEN=your_mapbox_token_here
VITE_API_BASE_URL=http://localhost:8080/api
VITE_APP_TITLE=地方感地图生成
```

