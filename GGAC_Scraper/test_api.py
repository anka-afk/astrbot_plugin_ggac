import asyncio
from ggac_api import GGACAPI


async def main():
    """主测试函数，所有操作都在同一个事件循环中进行"""
    # 在函数内部创建API实例
    api = GGACAPI()

    # 异步登录
    success = await api.login(username="", password="")

    if not success:
        print("登录失败")
        return

    # 测试获取3D作品
    print("\n获取精选3D作品:")
    featured_3d_works = await api.get_works(
        category="featured",
        media_type="3d",
        sort_by="recommended",
        page=1,
        size=1,
    )
    print(featured_3d_works)

    # 测试获取2D作品
    print("\n获取精选2D作品:")
    featured_2d_works = await api.get_works(
        category="featured", media_type="2d", sort_by="recommended", page=1, size=1
    )
    print(featured_2d_works)


if __name__ == "__main__":
    asyncio.run(main())
