"""
图片搜索服务：优先百度图片 JSON API；无结果时用 Wikimedia Commons（全球可访问）兜底。
"""
import asyncio
import json
import re
import urllib.request
import urllib.parse
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from typing import Any, List, Optional, Tuple

from app.models.image import ImageResult
from app.utils.ssl_context import get_ssl_context

_executor = ThreadPoolExecutor(max_workers=4)
_SSL_CTX = get_ssl_context()


def _urlopen(url: str, timeout: float = 15, headers: Optional[dict] = None,
             data: Optional[bytes] = None) -> bytes:
    """同步 HTTP 请求，返回 response body bytes。"""
    req = urllib.request.Request(url, data=data or None, headers=headers or {})
    kwargs = {"timeout": timeout}
    if url.startswith("https"):
        kwargs["context"] = _SSL_CTX
    with urllib.request.urlopen(req, **kwargs) as resp:
        return resp.read()


async def _urlopen_async(url: str, timeout: float = 15, headers: Optional[dict] = None,
                         data: Optional[bytes] = None) -> bytes:
    """异步包装 _urlopen。"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, _urlopen, url, timeout, headers, data)


class ImageSearchService:
    """图片搜索服务"""

    _RASTER_SUFFIXES = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff", ".bmp")
    _MIDDLE_URL_RE = re.compile(r'"middleURL"\s*:\s*"((?:[^"\\]|\\.)*)"')

    def __init__(self):
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
        self.timeout = 15
        self.commons_timeout = 30.0
        self.commons_user_agent = (
            "PlaceSenseMap/1.0 (mapbox-placemap; Wikimedia Commons image search fallback; "
            "+https://wikimediafoundation.org/)"
        )

    @staticmethod
    def _normalize_media_url(raw: Any) -> Optional[str]:
        if not isinstance(raw, str):
            return None
        u = raw.strip()
        if not u:
            return None
        if u.startswith("//"):
            u = "https:" + u
        if u.startswith("http://") or u.startswith("https://"):
            return u
        return None

    def _pick_baidu_urls(self, item: dict) -> Tuple[Optional[str], Optional[str]]:
        """从百度单条记录解析主图与缩略图 URL。"""
        full_candidates: List[str] = []
        thumb_candidates: List[str] = []

        def push(raw: Any, as_thumb: bool) -> None:
            u = self._normalize_media_url(raw)
            if not u:
                return
            if as_thumb:
                thumb_candidates.append(u)
            else:
                full_candidates.append(u)

        for key in ("middleURL", "objURL", "hoverURL"):
            push(item.get(key), False)
        push(item.get("thumbURL"), True)

        replace_url = item.get("replaceUrl")
        if isinstance(replace_url, list):
            for chunk in replace_url:
                if isinstance(chunk, dict):
                    push(chunk.get("ObjURL"), False)
                    push(chunk.get("ObjEncodeUrl"), False)

        img_url = full_candidates[0] if full_candidates else None
        thumb_url = thumb_candidates[0] if thumb_candidates else None
        if not img_url and thumb_url:
            img_url = thumb_url
        if not thumb_url and img_url:
            thumb_url = img_url
        return img_url, thumb_url

    @staticmethod
    def _baidu_unescape_url_fragment(frag: str) -> str:
        """解析百度 JSON 字符串片段中的 URL（不要求整个响应可 json.loads）。"""
        try:
            return json.loads(f'"{frag}"')
        except json.JSONDecodeError:
            return frag.replace("\\/", "/").replace('\\"', '"').replace("\\\\", "\\")

    def _baidu_extract_urls_regex(self, raw: str, count: int) -> List[ImageResult]:
        """百度返回含非法转义 JSON 时，从原文中提取 middleURL。"""
        images: List[ImageResult] = []
        for m in self._MIDDLE_URL_RE.finditer(raw):
            if len(images) >= count:
                break
            frag = m.group(1)
            url = self._normalize_media_url(self._baidu_unescape_url_fragment(frag))
            if not url:
                continue
            try:
                images.append(ImageResult(url=url, thumbnail=url, title=None, width=None, height=None))
            except Exception:
                continue
        if images:
            print(f"[图片搜索] 正则兜底提取百度 middleURL {len(images)} 条")
        return images

    async def search(self, keyword: str, count: int = 9) -> List[ImageResult]:
        if not keyword or not keyword.strip():
            return []

        count = min(count, 50)

        print(f"\n{'='*60}")
        print("[图片搜索] 开始搜索")
        print(f"[图片搜索] 关键词: {keyword}")
        print(f"[图片搜索] 请求数量: {count}")

        baidu = await self._search_baidu(keyword, count)
        if baidu:
            print(f"[图片搜索] 百度返回 {len(baidu)} 张，直接使用")
            print(f"[图片搜索] {'='*60}\n")
            return baidu

        print("[图片搜索] 百度无可用图片，尝试 Wikimedia Commons 兜底…")
        commons = await self._search_wikimedia_commons(keyword.strip(), count)
        print(f"[图片搜索] Commons 返回 {len(commons)} 张")
        print(f"[图片搜索] {'='*60}\n")
        return commons

    async def _search_baidu(self, keyword: str, count: int) -> List[ImageResult]:
        if self._is_english(keyword):
            search_word = f"{keyword} scenery"
        else:
            search_word = f"{keyword} 风景"

        print(f"[图片搜索] 百度搜索词: {search_word}")

        try:
            # Step 1: 访问百度首页获取 cookie
            home_headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
            try:
                await _urlopen_async("https://image.baidu.com/", timeout=self.timeout, headers=home_headers)
            except Exception:
                print("[图片搜索] 百度首页请求失败，继续尝试 API")

            # Step 2: 调用百度图片 JSON API
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
            full_url = api_url + "?" + urllib.parse.urlencode(params)
            api_headers = {
                "User-Agent": self.user_agent,
                "Referer": "https://image.baidu.com/",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
            body = await _urlopen_async(full_url, timeout=self.timeout, headers=api_headers)
            text = body.decode("utf-8", errors="replace")

            data: Optional[dict] = None
            try:
                parsed = json.loads(text)
                data = parsed if isinstance(parsed, dict) else None
            except Exception:
                data = None

            if data is None:
                start = text.find("{")
                end = text.rfind("}")
                if start >= 0 and end > start:
                    chunk = text[start : end + 1]
                    try:
                        loaded = json.loads(chunk)
                        data = loaded if isinstance(loaded, dict) else None
                    except json.JSONDecodeError:
                        print("[图片搜索] 百度 JSON 含非法转义，跳过完整解析")
                        data = None

            if data is None:
                return self._baidu_extract_urls_regex(text, count)

            data_list = data.get("data") or []
            if not data_list:
                print(f"[图片搜索] 百度 data 为空 keys={list(data.keys())}，尝试正则提取")
                reg = self._baidu_extract_urls_regex(text, count)
                if reg:
                    return reg
                return []

            images: List[ImageResult] = []
            for item in data_list:
                if not isinstance(item, dict):
                    continue

                img_url, thumbnail_url = self._pick_baidu_urls(item)
                if not img_url:
                    continue

                title = item.get("fromPageTitle") or item.get("title") or item.get("keyword")
                width = item.get("width")
                height = item.get("height")

                try:
                    images.append(
                        ImageResult(
                            url=img_url,
                            thumbnail=thumbnail_url,
                            title=str(title)[:500] if title else None,
                            width=int(width) if isinstance(width, (int, float)) else None,
                            height=int(height) if isinstance(height, (int, float)) else None,
                        )
                    )
                except Exception as e:
                    print(f"[图片搜索] 跳过无效百度条目: {e}")
                    continue

                if len(images) >= count:
                    break

            return images

        except urllib.error.URLError as e:
            print(f"[图片搜索] 百度网络错误: {e}")
            return []
        except Exception as e:
            print(f"[图片搜索] 百度解析异常: {e!r}")
            import traceback
            traceback.print_exc()
            return []

    def _commons_is_raster(self, title: str) -> bool:
        t = title.lower()
        if ":" in t:
            t = t.split(":", 1)[-1]
        return any(t.endswith(ext) for ext in self._RASTER_SUFFIXES)

    async def _search_wikimedia_commons(self, keyword: str, count: int) -> List[ImageResult]:
        """Wikimedia Commons：无需 Key，适合百度不可用时的兜底。"""
        api = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": keyword,
            "gsrnamespace": "6",
            "gsrlimit": str(min(max(count, 10), 50)),
            "prop": "imageinfo",
            "iiprop": "url|thumburl|dimensions",
            "iiurlwidth": "480",
        }
        full_url = api + "?" + urllib.parse.urlencode(params)
        headers = {
            "User-Agent": self.commons_user_agent,
            "Accept": "application/json",
            "Api-User-Agent": self.commons_user_agent,
        }
        try:
            raw = await _urlopen_async(full_url, timeout=self.commons_timeout, headers=headers)
            body = json.loads(raw.decode("utf-8"))
        except Exception as e:
            print(f"[图片搜索] Commons 请求失败: {type(e).__name__} {e!r}")
            return []

        pages = (body.get("query") or {}).get("pages") or {}
        if not pages:
            print("[图片搜索] Commons query.pages 为空")
            return []

        out: List[ImageResult] = []
        for _pid, page in pages.items():
            if not isinstance(page, dict):
                continue
            title = page.get("title") or ""
            if not self._commons_is_raster(str(title)):
                continue
            infos = page.get("imageinfo")
            if not isinstance(infos, list) or not infos:
                continue
            info = infos[0]
            if not isinstance(info, dict):
                continue
            url = self._normalize_media_url(info.get("url"))
            thumb = self._normalize_media_url(info.get("thumburl"))
            if not url:
                continue
            if not thumb:
                thumb = url
            w = info.get("width")
            h = info.get("height")
            try:
                out.append(
                    ImageResult(
                        url=url,
                        thumbnail=thumb,
                        title=str(title).replace("File:", "")[:500],
                        width=int(w) if isinstance(w, (int, float)) else None,
                        height=int(h) if isinstance(h, (int, float)) else None,
                    )
                )
            except Exception:
                continue
            if len(out) >= count:
                break

        return out

    def _is_english(self, text: str) -> bool:
        if not text:
            return False
        english_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        total_chars = sum(1 for c in text if c.isalpha())
        if total_chars == 0:
            return False
        return english_chars / total_chars > 0.5
