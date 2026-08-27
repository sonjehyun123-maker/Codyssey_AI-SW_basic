import functools
import sys
import time
from typing import Callable


class AppError(Exception):
    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.message = message
        self.hint = hint


def handle_errors(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AppError as e:
            print(f"[오류] {e.message}")
            if e.hint:
                print(f"[힌트] {e.hint}")
            sys.exit(1)
        except FileNotFoundError as e:
            print(f"[오류] 파일을 찾을 수 없습니다: {e.filename}")
            print("[힌트] 경로를 다시 확인해 주세요.")
            sys.exit(1)
        except Exception as e:
            print(f"[오류] {e}")
            sys.exit(1)
    return wrapper


def log_execution(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[LOG] {func.__name__} 실행", file=sys.stderr)
        return func(*args, **kwargs)
    return wrapper


def measure_time(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[TIME] {func.__name__} {elapsed:.4f}s", file=sys.stderr)
        return result
    return wrapper
