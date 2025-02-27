import asyncio
import json
from ggac_monitor import GGACMonitor


async def test_monitor():
    monitor = GGACMonitor()

    # 第一次运行，会创建缓存
    print("第一次运行:")
    updates = await monitor.check_updates()
    print("首次缓存完成，无更新推送")

    # 模拟数据变化：修改缓存文件，删除一些数据
    for cache_file in monitor.cache_files.values():
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 删除前3条数据，模拟有新内容
            modified_data = data[3:]
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(modified_data, f, ensure_ascii=False, indent=2)

    print("\n模拟数据变化后第二次运行:")
    updates = await monitor.check_updates()

    for category, items in updates.items():
        if items:
            print(f"\n{category}类型更新:")
            for item in items:
                print(f"图片路径: {item['image_path']}")
                print(f"作品链接: {item['url']}")
                print("---")


if __name__ == "__main__":
    asyncio.run(test_monitor())
