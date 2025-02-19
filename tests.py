import asyncio, aiohttp
import io
import time


async def send(buffer, i):
    print("Started", i)
    async with aiohttp.ClientSession() as session:
        async with session.post("http://localhost:8000/api/task", data={'file': buffer}) as response:
            assert response.status == 201, await response.text()
            task_id = (await response.json())["id"]
            print(i, "created")
        while True:
            async with session.get("http://localhost:8000/api/task/" + task_id) as response:
                assert response.status == 200, await response.text
                body = await response.json()
                if body["items"]:
                    break
    print(i, "finished", body["items"])


async def main():
    with open('/home/eramir/Загрузки/full-growth-portrait-smiling-successful-businessman_252847-32355.jpg', 'rb') as f:
        image = f.read()

    tasks = []
    for i in range(100):
        buffer = io.BytesIO(image)
        tasks.append(send(buffer, i))
    await asyncio.gather(*tasks)


start_time = time.time()
asyncio.run(main())
print("Elapsed: ", time.time() - start_time)

