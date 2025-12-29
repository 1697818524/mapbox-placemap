/** *
首页地图采用上下两栏布局。顶部为导航栏，提供系统导航与核心功能入口；下方区域采用三栏结构：左侧为地图信息栏，支持区域搜索及相关风景图片的查看；中间为地图显示区域，用于地图的实时渲染与交互；右侧为地图样式栏，用于地图样式与视觉参数的配置。
*/
<template>
  <div class="container">
    <!-- 上栏：导航栏 -->
    <div class="navbar">
      <Navbar />
    </div>
    <div class="main-content">
      <div class="left-sidebar">
        <MapInfo />
      </div>
      <div class="map-container">
        <MapDisplay />
      </div>
      <div class="right-sidebar">
        <MapStyle />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, provide } from 'vue'
import Navbar from '@/components/Navbar.vue'
import MapInfo from '@/components/MapInfo.vue'
import MapDisplay from '@/components/MapDisplay.vue'
import MapStyle from '@/components/MapStyle.vue'
import type mapboxgl from 'mapbox-gl'

// 创建地图实例的引用，提供给子组件使用
const mapRef = ref<{ value: mapboxgl.Map | null }>({ value: null })
provide('mapInstance', mapRef)
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.navbar {
  height: 100px;
  background-color: #FEFEFE;
  flex-shrink: 0;
}
/* 下栏区域，占据剩余部分 */
.main-content {
  display: flex;
  flex-grow: 1;
  background-color: #e0cece;
  flex-direction: row;
  overflow: hidden;
}
.left-sidebar {
  width:300px;
  background-color: aqua;
  flex-shrink: 0;
}
.map-container {
  flex-grow: 1;
  background-color: #eec9c9;
  flex-shrink: 0;
}
.right-sidebar {
  width:400px;
  background-color: #f0f0f0;
  flex-shrink: 0;
}
</style>