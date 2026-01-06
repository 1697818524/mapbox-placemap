"""
图片搜索服务（百度图片搜索 JSON API）
"""
import json
import httpx
from typing import List
from app.models.image import ImageResult


class ImageSearchService:
    """图片搜索服务（百度图片搜索）"""

    def __init__(self):
        """初始化图片搜索服务"""
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
        self.timeout = 15

    async def search(self, keyword: str, count: int = 9) -> List[ImageResult]:
        """
        搜索图片

        Args:
            keyword: 搜索关键词（地点名称）
            count: 返回图片数量（最多50张）

        Returns:
            图片搜索结果列表
        """
        if not keyword or not keyword.strip():
            return []

        # 限制返回数量
        count = min(count, 50)

        try:
            print(f"\n{'='*60}")
            print(f"[图片搜索] 开始搜索")
            print(f"[图片搜索] 关键词: {keyword}")
            print(f"[图片搜索] 请求数量: {count}")

            # 构建搜索词：地点 + 风景（英文：location + scenery）
            if self._is_english(keyword):
                search_word = f"{keyword} scenery"
            else:
                search_word = f"{keyword} 风景"

            print(f"[图片搜索] 搜索词: {search_word}")

            # 创建 HTTP 客户端（使用 session 保持 cookie）
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                # 关键：先访问一次主页，让 session 带上 BAIDUID 等 cookie
                print(f"[图片搜索] 访问主页获取 Cookie...")
                headers_home = {
                    "User-Agent": self.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                }
                await client.get("https://image.baidu.com/", headers=headers_home)

                # 构建 JSON API 请求参数
                api_url = "https://image.baidu.com/search/acjson"
                params = {
                    "tn": "resultjson_com",
                    "ipn": "rj",
                    "ct": "201326592",
                    "fp": "result",
                    "cl": "2",
                    "lm": "-1",
                    "ie": "utf-8",
                    "oe": "utf-8",
                    "st": "-1",
                    "word": search_word,
                    "queryWord": search_word,
                    "pn": 0,
                    "rn": count,
                }

                # 发送 JSON API 请求
                headers_api = {
                    "User-Agent": self.user_agent,
                    "Referer": "https://image.baidu.com/",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                    "Connection": "keep-alive",
                    "X-Requested-With": "XMLHttpRequest",
                }

                print(f"[图片搜索] 发送 API 请求...")
                print(f"[图片搜索] URL: {api_url}")
                print(f"[图片搜索] 参数: {params}")

                response = await client.get(api_url, params=params, headers=headers_api)
                response.raise_for_status()

                print(f"[图片搜索] HTTP响应状态码: {response.status_code}")
                print(f"[图片搜索] 响应内容长度: {len(response.text)} 字符")

                # 百度有时会返回"非标准 JSON"（前后夹杂字符），需要容错处理
                text = response.text
                try:
                    data = response.json()
                except Exception:
                    print(f"[图片搜索] JSON解析失败，尝试提取JSON部分...")
                    # 查找第一个 { 和最后一个 }
                    start = text.find("{")
                    end = text.rfind("}")
                    if start >= 0 and end > start:
                        json_text = text[start:end + 1]
                        data = json.loads(json_text)
                        print(f"[图片搜索] ✓ 成功提取JSON部分")
                    else:
                        print(f"[图片搜索] ✗ 无法找到有效的JSON部分")
                        print(f"[图片搜索] 响应前500字符: {text[:500]}")
                        return []

                # 提取可直连的图片 URL
                print(f"[图片搜索] 解析返回数据...")
                print(f"[图片搜索] 返回字段: {list(data.keys())}")

                data_list = data.get("data", [])
                print(f"[图片搜索] data数组长度: {len(data_list)}")

                if not data_list:
                    print(f"[图片搜索] ⚠️  返回的data数组为空")
                    print(f"[图片搜索] 完整响应: {json.dumps(data, ensure_ascii=False, indent=2)[:1000]}")
                    return []

                # 提取图片 URL（优先级：middleURL > thumbURL > hoverURL）
                images = []
                for item in data_list:
                    if not isinstance(item, dict):
                        continue

                    # 尝试多个字段获取图片 URL（优先级顺序）
                    img_url = None
                    thumbnail_url = None
                    for key in ("middleURL", "thumbURL", "hoverURL"):
                        url = item.get(key)
                        if isinstance(url, str) and url.startswith("http"):
                            if not img_url:
                                img_url = url
                            if key == "thumbURL" and not thumbnail_url:
                                thumbnail_url = url
                            if img_url and thumbnail_url:
                                break

                    if not img_url:
                        continue

                    # 获取图片标题和尺寸信息
                    title = item.get("fromPageTitle") or item.get("title") or item.get("keyword")
                    width = item.get("width")
                    height = item.get("height")

                    # 创建图片结果
                    try:
                        image_result = ImageResult(
                            url=img_url,
                            thumbnail=thumbnail_url if thumbnail_url else None,
                            title=title,
                            width=width,
                            height=height,
                        )
                        images.append(image_result)
                    except Exception as e:
                        print(f"[图片搜索] ⚠️  创建图片结果失败，跳过: {e}, URL: {img_url[:80]}")
                        continue

                    if len(images) >= count:
                        break

                print(f"[图片搜索] ✓ 成功提取 {len(images)} 张图片")

                # 最终结果汇总
                print(f"[图片搜索] {'='*60}")
                print(f"[图片搜索] 解析完成: 找到 {len(images)} 张图片")

                if images:
                    print(f"[图片搜索] ✓ 成功获取图片列表 (显示前5张):")
                    for idx, img in enumerate(images[:5], 1):
                        print(f"  [{idx}] URL: {img.url}")
                        if img.title:
                            print(f"      标题: {img.title}")
                        if img.width and img.height:
                            print(f"      尺寸: {img.width}x{img.height}")
                else:
                    print(f"[图片搜索] ✗ 未找到任何图片")

                print(f"[图片搜索] {'='*60}\n")

                return images

        except httpx.TimeoutException:
            print(f"[图片搜索] ✗ 搜索图片超时: {keyword}")
            return []
        except httpx.HTTPError as e:
            print(f"[图片搜索] ✗ 搜索图片HTTP错误: {e}")
            return []
        except Exception as e:
            print(f"[图片搜索] ✗ 搜索图片失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _is_english(self, text: str) -> bool:
        """
        判断文本是否主要是英文

        Args:
            text: 待判断的文本

        Returns:
            如果主要是英文返回True，否则返回False
        """
        if not text:
            return False

        # 统计英文字符数量
        english_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        total_chars = sum(1 for c in text if c.isalpha())

        if total_chars == 0:
            return False

        # 如果英文字符占比超过50%，认为是英文
        return english_chars / total_chars > 0.5
