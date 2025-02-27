import asyncio
from GGAC_Scraper.ggac_api import GGACAPI

api = GGACAPI()


async def test_featured_2d_works_recommended():
    featured_2d_works_recommended = await api.get_works(
        category="featured",
        media_type="2d",
        sort_by="recommended",
        page=1,
        size=48,
    )

    print(featured_2d_works_recommended)


async def test_featured_3d_works_recommended():
    featured_3d_works_recommended = await api.get_works(
        category="featured",
        media_type="3d",
        sort_by="recommended",
        page=1,
        size=48,
    )

    print(featured_3d_works_recommended)


if __name__ == "__main__":
    # asyncio.run(test_featured_2d_works_recommended())
    asyncio.run(test_featured_3d_works_recommended())
