# Git 개념 정리

## Git이란?

Git은 **파일을 저장하는 프로그램이 아니라, 프로젝트의 순간적인 상태(Snapshot)를 기록하는 데이터베이스(DB)** 이다.

즉, 파일 하나만 저장하는 것이 아니라 **프로젝트 전체의 상태**를 하나의 기록(Commit)으로 저장한다.

---

# Git이 저장하는 객체(Object)

Git은 프로젝트를 저장하기 위해 크게 4가지 객체(Object)를 사용한다.

## 1. Blob (Binary Large Object)

파일의 실제 **내용(Content)** 을 저장하는 가장 기본적인 객체이다.

**Blob에는 저장되지 않는 것**
- 파일 이름 ❌
- 폴더 위치 ❌

**Blob에 저장되는 것**
- 파일 안의 글자
- 코드
- 이미지 데이터
- 파일의 실제 내용

예를 들어

```text
print("Hello")
```

라는 파일이 있다면 Blob은

```text
print("Hello")
```

내용만 저장한다.

---

## 2. Tree

디렉토리(폴더)를 저장하는 객체이다.

Blob에서 저장하지 않았던

- 파일 이름
- Blob의 주소(Hash)

를 저장한다.

예를 들어

```text
src/
 ├── main.py
 └── util.py
```

는 Tree에서

```text
Tree

main.py -> Blob A
util.py -> Blob B
```

처럼 저장된다.

즉,

> **파일 이름 + Blob의 위치(Hash)**

를 저장하는 객체이다.

---

## 3. Commit

프로젝트의 전체 상태를 저장하는 객체이다.

Commit에는

- 프로젝트 상태(Tree)
- 부모 Commit
- 작성자
- Commit Message

가 저장된다.

예시

```text
Commit C

parent  -> Commit B
tree    -> Tree3
author  -> Kim
message -> "Fix bug"
```

Commit은 이전 Commit을 부모(parent)로 기억한다.

그래서 Commit들은 연결 리스트처럼 이어진다.

```text
A <- B <- C
```

---

## 4. SHA-1(Hash)

Git은 모든 객체를 **SHA-1 Hash** 로 관리한다.

Blob

Tree

Commit

모두 SHA-1 값을 가진다.

예를 들어

```text
hello
```

라는 데이터는

```text
f572d396fa...
```

같은 Hash를 가진다.

Git은 파일 이름이 아니라

> **SHA-1 Hash**

를 이용하여 객체를 관리한다.

---

# Commit 구조

Commit은 이전 Commit을 부모(parent)로 가진다.

예시

```text
Commit C

parent  -> Commit B
tree    -> Tree3
message -> "Fix bug"
```

Commit들은 부모를 따라 연결된다.

```text
A <- B <- C
```

Git Log는 부모 Commit을 따라가면서 기록을 출력한다.

---

# Branch란?

많은 사람들이 Branch를

> 프로젝트를 복사한 것

이라고 생각하지만 그렇지 않다.

Branch는

> **특정 Commit 하나를 가리키는 포인터(Pointer)**

이다.

예를 들어

```text
A <- B <- C
```

라는 Commit 구조가 있다면

```text
main
 │
 ▼
 C
```

즉,

```
main = Commit C를 가리키는 이름
```

이다.

---

## 새로운 Branch 생성

```bash
git branch feature
```

를 실행하면

프로젝트가 복사되는 것이 아니라

```text
A <- B <- C
          ▲
      main feature
```

처럼

Commit C를 가리키는 포인터 하나가 추가된다.

그래서 Branch 생성은 매우 빠르다.

---

# HEAD란?

HEAD는

> **현재 내가 작업 중인 Branch(또는 Commit)를 가리키는 특수 포인터**

이다.

일반적으로는 Branch를 가리킨다.

```text
HEAD
 │
 ▼
main
 │
 ▼
Commit C
```

즉,

```text
HEAD → main → Commit C
```

이다.

Branch를 변경하면

```bash
git switch feature
```

HEAD가

```text
HEAD
 │
 ▼
feature
```

를 가리키게 된다.

---

# Commit을 하면?

현재 상태

```text
HEAD
 │
 ▼
main
 │
 ▼
Commit C
```

새로운 Commit D를 생성하면

```text
A <- B <- C <- D
```

가 된다.

그리고

```text
HEAD
 │
 ▼
main
 │
 ▼
Commit D
```

가 된다.

즉 Commit은

1. 새로운 Commit 객체 생성
2. 현재 Branch가 새 Commit을 가리키도록 이동

하는 과정이다.

---

# Detached HEAD

HEAD가 Branch가 아니라

직접 Commit을 가리키는 상태이다.

```text
HEAD
 │
 ▼
Commit C
```

이 상태에서 Commit을 생성하면

```text
A <- B <- C <- D
```

가 되지만

어떤 Branch도 D를 가리키지 않는다.

따라서 나중에 해당 Commit을 잃어버릴 수 있다.

---

# Merge

Merge는

> **두 Branch의 작업 내용을 하나로 합치는 작업**

이다.

예를 들어

```text
A <- B <- C
      \
       D <- E
```

를 Merge하면

```text
A <- B <- C ------ M
      \          /
       D <- E ---
```

Merge Commit(M)은

부모가 두 개이다.

```text
parent1 -> Commit C
parent2 -> Commit E
```

그래서 Git의 Commit 구조는

> **DAG(Directed Acyclic Graph)**

라고 불린다.

---

# Fast-forward Merge

Merge 대상이 현재 Branch보다 앞에만 있다면

Merge Commit을 만들 필요가 없다.

예를 들어

```text
A <- B <- C
          \
           D
```

에서 Merge를 하면

```text
A <- B <- C <- D
```

가 된다.

즉,

Branch 포인터만 D로 이동한다.

이를

> **Fast-forward Merge**

라고 한다.

---

# Rebase

Rebase는 Branch를 합치는 것이 아니라

> **현재 Branch의 Commit을 다른 Commit 위에 다시 쌓는 작업**

이다.

예를 들어

```text
A <- B <- C
      \
       D <- E
```

를 Rebase하면

```text
A <- B <- C <- D' <- E'
```

가 된다.

여기서

D'

E'

는 기존 Commit이 아니라

새롭게 생성된 Commit이다.

따라서 Commit Hash도 변경된다.

---

# Git이 빠른 이유

Git은 대부분의 작업에서

파일을 복사하지 않는다.

대부분

**포인터만 이동**

하기 때문에 매우 빠르다.

| 작업 | 실제 동작 |
|------|-----------|
| Branch 생성 | Commit을 가리키는 포인터 생성 |
| Branch 변경 | HEAD가 다른 Branch를 가리킴 |
| Commit | 새로운 Commit 생성 + Branch 이동 |
| Merge | Merge Commit 생성 또는 포인터 이동 |
| Log 조회 | 부모 Commit을 따라 이동 |

---

# Git 핵심 개념 요약

| 개념 | 설명 |
|------|------|
| **Blob** | 파일의 실제 내용 저장 |
| **Tree** | 디렉토리(파일 이름 + Blob Hash) 저장 |
| **Commit** | 프로젝트 상태(Tree) + 부모 Commit + 작성자 + 메시지 저장 |
| **SHA-1** | 모든 객체를 식별하는 고유 Hash |
| **Branch** | 특정 Commit을 가리키는 포인터 |
| **HEAD** | 현재 작업 중인 Branch(또는 Commit)를 가리키는 특수 포인터 |
| **Merge** | 두 Branch를 하나로 합치는 작업 |
| **Fast-forward Merge** | Merge Commit 없이 Branch 포인터만 이동 |
| **Rebase** | Commit을 다른 위치에 새롭게 다시 쌓는 작업 |

---

# 한 줄 요약

- **Blob** → 파일 내용을 저장
- **Tree** → 폴더 구조를 저장
- **Commit** → 프로젝트 전체 상태를 저장
- **Branch** → Commit을 가리키는 포인터
- **HEAD** → 현재 작업 중인 Branch를 가리키는 포인터
- **Merge** → Branch를 합침
- **Rebase** → Commit을 다시 쌓음
- **SHA-1** → 모든 객체를 식별하는 고유 Hash

