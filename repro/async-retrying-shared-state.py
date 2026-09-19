# 复现：两个协程共用一个异步重试实例，互相偷走对方的尝试次数
import asyncio

from tenacity import AsyncRetrying, stop_after_attempt

needs = {"C": 3, "D": 3}
used = {"C": 0, "D": 0}


async def run(inst, tag):
    seen = []
    async for attempt in inst:
        with attempt:
            used[tag] += 1
            seen.append(attempt.retry_state.attempt_number)
            if used[tag] < needs[tag]:
                raise ValueError("第 %s 轮第 %d 次失败" % (tag, used[tag]))
    return seen


async def main():
    print("=== 1) 共用一个实例（上限 3，每个任务自己需要 3 次尝试）")
    inst = AsyncRetrying(stop=stop_after_attempt(3))
    r = await asyncio.gather(run(inst, "C"), run(inst, "D"), return_exceptions=True)
    print("并发结果 ->", [(x if not isinstance(x, Exception) else type(x).__name__) for x in r])
    print("各自实际执行的次数 ->", used)

    print("=== 2) 对照：两个任务各自一个实例")
    used["C"] = used["D"] = 0
    a, b = AsyncRetrying(stop=stop_after_attempt(3)), AsyncRetrying(stop=stop_after_attempt(3))
    r2 = await asyncio.gather(run(a, "C"), run(b, "D"), return_exceptions=True)
    print("对照结果 ->", r2, "| 各自次数", used)

    print("=== 3) 同一个实例顺序跑两轮")
    inst3 = AsyncRetrying(stop=stop_after_attempt(3))
    used["C"] = 0
    first = await run(inst3, "C")
    used["C"] = 0
    second = await run(inst3, "C")
    print("第一轮 ->", first, "第二轮 ->", second)


asyncio.run(main())
