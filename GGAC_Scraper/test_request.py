import aiohttp
import asyncio
import json

async def test_request():
    # 测试2D原画请求
    url_2d = "https://www.ggac.com/api/work/list?pageNumber=1&pageSize=48&isPublic=1&isRecommend=1&sortField=recommendUpdateTime&mediaCategory=1"
    
    # 测试3D模型请求
    url_3d = "https://www.ggac.com/api/work/list?pageNumber=1&pageSize=48&isPublic=1&isRecommend=1&sortField=recommendUpdateTime&mediaCategory=2"
    
    async with aiohttp.ClientSession() as session:
        # 测试2D原画
        print("\n测试2D原画请求:")
        async with session.get(url_2d, ssl=False) as response:
            if response.status == 200:
                data = await response.json()
                print(f"状态码: {response.status}")
                print(f"返回数据: {json.dumps(data, ensure_ascii=False, indent=2)[:200]}...")
            else:
                print(f"请求失败: {response.status}")
        
        # 测试3D模型
        print("\n测试3D模型请求:")
        async with session.get(url_3d, ssl=False) as response:
            if response.status == 200:
                data = await response.json()
                print(f"状态码: {response.status}")
                print(f"返回数据: {json.dumps(data, ensure_ascii=False, indent=2)[:200]}...")
            else:
                print(f"请求失败: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_request()) 