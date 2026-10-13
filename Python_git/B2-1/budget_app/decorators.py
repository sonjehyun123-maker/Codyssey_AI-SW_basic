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
            print("[힌트] 지정한 경로가 올바른지, 파일이 존재하는지 확인해 주세요.")
            sys.exit(1)
        except PermissionError as e:
            print(f"[오류] 파일 접근 권한이 없습니다: {e.filename}")
            print("[힌트] 파일 읽기/쓰기 권한 및 다른 프로세스 점유 여부를 확인해 주세요.")
            sys.exit(1)
        except UnicodeDecodeError:
            print("[오류] 파일 인코딩을 해석할 수 없습니다.")
            print("[힌트] 파일이 UTF-8 인코딩인지 확인해 주세요.")
            sys.exit(1)
        except ValueError as e:
            print(f"[오류] 유효하지 않은 값 또는 입력입니다: {e}")
            print("[힌트] 입력 데이터 형식 및 숫자/날짜 범위를 확인해 주세요.")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n[취소] 사용자에 의해 작업이 취소되었습니다.")
            sys.exit(130)
        except Exception as e:
            print(f"[오류] 시스템 예외 발생: {type(e).__name__} - {e}")
            print("[힌트] 입력 인자 및 시스템 환경 설정을 점검해 주세요. 문제가 지속되면 관리자에게 문의하세요.")
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
