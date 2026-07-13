# -*- coding: utf-8 -*-

import sys
from redis_db import MiniRedis


def format_keys_output(keys):
    if not keys:
        return "(empty array)"
    return "\n".join(f"{i}) \"{k}\"" for i, k in enumerate(keys, start=1))


def parse_int(token):
    try:
        return int(token)
    except ValueError:
        return None


def split_arguments(line):
    tokens = []
    current = []
    in_quotes = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            in_quotes = not in_quotes
        elif ch == ' ' and not in_quotes:
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(ch)
        i += 1
    if current:
        tokens.append("".join(current))
    return tokens


def dispatch(db, tokens):
    cmd = tokens[0].upper()

    # 인자 개수 예외 표준 규격정의 (명령어: (정확한 토큰 개수, 에러 메시지))
    SPECS = {
        "SET": (3, "(error) ERR wrong number of arguments for 'SET' command"),
        "GET": (2, "(error) ERR wrong number of arguments for 'GET' command"),
        "DEL": (2, "(error) ERR wrong number of arguments for 'DEL' command"),
        "EXISTS": (2, "(error) ERR wrong number of arguments for 'EXISTS' command"),
        "DBSIZE": (1, "(error) ERR wrong number of arguments for 'DBSIZE' command"),
        "KEYS": (1, "(error) ERR wrong number of arguments for 'KEYS' command"),
        "TTL": (2, "(error) ERR wrong number of arguments for 'TTL' command"),
        "EXPIRE": (3, "(error) ERR wrong number of arguments for 'EXPIRE' command"),
    }

    if cmd in SPECS:
        expected_len, err_msg = SPECS[cmd]
        if len(tokens) != expected_len:
            return err_msg

    # 각 커맨드 라우팅 실행
    if cmd == "SET":
        return db.cmd_set(tokens[1], tokens[2])
    elif cmd == "GET":
        return db.cmd_get(tokens[1])
    elif cmd == "DEL":
        return db.cmd_del(tokens[1])
    elif cmd == "EXISTS":
        return db.cmd_exists(tokens[1])
    elif cmd == "DBSIZE":
        return db.cmd_dbsize()
    elif cmd == "KEYS":
        return format_keys_output(db.cmd_keys())
    elif cmd == "TTL":
        return db.cmd_ttl(tokens[1])
    elif cmd == "EXPIRE":
        seconds = parse_int(tokens[2])
        if seconds is None:
            return "(error) ERR value is not an integer or out of range"
        return db.cmd_expire(tokens[1], seconds)

    elif cmd == "CONFIG":
        if len(tokens) != 4 or tokens[1].upper() != "SET" or tokens[2].lower() != "maxmemory":
            return "(error) ERR wrong number of arguments for 'config|set' command"
        val = parse_int(tokens[3])
        if val is None or val < 0:
            return "(error) ERR value is not an integer or out of range"
        return db.cmd_config_set_maxmemory(val)

    elif cmd == "INFO":
        if len(tokens) != 2 or tokens[1].lower() != "memory":
            return "(error) ERR wrong number of arguments for 'info' command"
        return db.cmd_info_memory()

    else:
        return f"(error) ERR unknown command '{tokens[0]}'"


def main():
    db = MiniRedis()
    print("Mini Redis CLI (exit/quit 으로 종료)")

    while True:
        try:
            line = input("mini-redis> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        line = line.strip()
        if not line:
            continue

        if line.lower() in ("exit", "quit"):
            break

        tokens = split_arguments(line)
        if not tokens:
            continue

        result = dispatch(db, tokens)
        print(result)


if __name__ == "__main__":
    main()