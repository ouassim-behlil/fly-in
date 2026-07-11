import time
from functools import wraps
from typing import Any, Callable
import tracemalloc


def timeit(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = end - start
        print(f"{func.__name__} executed in {elapsed:.6f} seconds")
        return result
    return wrapper


def measure_memory(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        tracemalloc.start()
        result = func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"{func.__name__} memory: current={current/1024:.2f} KB, peak={peak/1024:.2f} KB")
        return result
    return wrapper