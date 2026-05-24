"""一次性脚本：验证图片搜索是否有返回。"""
import asyncio

from app.services.image_search import ImageSearchService


async def main() -> None:
    rows = await ImageSearchService().search("Shanghai", 5)
    print("count", len(rows))
    for i, img in enumerate(rows[:3], 1):
        print(i, str(img.url)[:120])


if __name__ == "__main__":
    asyncio.run(main())
