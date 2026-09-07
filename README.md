# Codyssey_AI-SW_basic

> **운영체제 → 자료구조 → 웹 → 데이터베이스 → 클라우드/AI까지, 소프트웨어의 핵심 원리를 직접 구현하며 학습한 기록입니다.**

각 기술을 개별적으로 학습하는 데 그치지 않고, 작은 시스템과 서비스를 직접 구현하며 **기술 간 연결과 내부 동작을 이해하는 것**을 목표로 합니다.

---

## 소개

Python, C, C++을 기반으로 자료구조와 시스템 프로그래밍을 직접 구현하며 학습하고 있습니다.

이 저장소는 **"무엇을 공부했는가"보다 "직접 만들면서 무엇을 이해하게 되었는가"**를 보여주는 데 초점을 맞춥니다.

---

## Featured Projects

기술적으로 가장 의미 있었던 프로젝트입니다.

| 프로젝트                                                  | 설명                                      | 핵심 기술                          |
| ----------------------------------------------------- | --------------------------------------- | ------------------------------ |
| **[Mini Redis](Data_Structures/B3-1/README.md)**      | 자료구조를 직접 구현한 메모리 저장소                    | HashMap · LRU · Min Heap · TTL |
| **[Mini Git](Data_Structures/B3-2/README.md)**        | Git의 Commit 구조와 그래프를 직접 구현              | DAG · Hash · BFS · Sorting     |
| **[Linux System Monitoring Agent](Linux_OS/B1-1.md)** | Linux 시스템 자원을 모니터링하는 관제 프로그램            | Linux · Process · Shell        |
| **[Git AI Helper](Cloud_API/B6-2/README.md)**         | Git 변경사항을 분석해 AI Commit/PR을 생성하는 CLI 도구 | LLM API · Validation · Retry   |

> 각 프로젝트를 클릭하면 구현 과정과 기술적 내용을 확인할 수 있습니다.

---

## 핵심 기술

| 분야                  | 기술                                                    |
| ------------------- | ----------------------------------------------------- |
| **Systems**         | Linux · Process · Resource Monitoring · Git Internals |
| **Data Structures** | HashMap · Linked List · Heap · Graph · LRU · TTL      |
| **Web / Backend**   | HTML · CSS · JavaScript · React · SQL · FastAPI       |
| **AI**              | LLM API · Prompt Engineering · AI Developer Tool      |

---

## 학습 방식

* **직접 구현** — 핵심 자료구조와 시스템 동작을 가능한 한 직접 구현
* **이론과 구현 연결** — 자료구조와 알고리즘의 원리를 코드로 확인
* **트러블슈팅과 재설계** — 문제의 원인을 분석하고 필요하면 기존 설계를 개선

---

## Learning Roadmap

| Stage  | Focus                        | Projects / Topics                                                                         |
| ------ | ---------------------------- | ----------------------------------------------------------------------------------------- |
| **B1** | Linux & OS                   | [시스템 관제](Linux_OS/B1-1.md) · [시스템 프로그래밍](Linux_OS/B1-2.md)                                |
| **B2** | Python & Git                 | [Python 콘솔 프로그램](Python_git/B2-1/B2-1.md) · Git Workflow                                  |
| **B3** | Data Structures & Algorithms | [Mini Redis](Data_Structures/B3-1/README.md) · [Mini Git](Data_Structures/B3-2/README.md) |
| **B4** | Web                          | [Portfolio Website](Web_Basics/B4-1.md) · React                                           |
| **B5** | Database & Backend           | [SQL Database](DB_Backend/B5-1.md) · FastAPI · CRUD · Authentication                      |
| **B6** | Cloud & AI                   | [Cloud Deployment](Cloud_API/B6-1/6-1.md) · [Git AI Helper](Cloud_API/B6-2/README.md)     |
| **B7** | Term Project                 | [AI Chatbot Service](Term_Project/B7-1.md)                                                |

---

## Repository Structure

```text id="z7x8p2"
Codyssey_AI-SW_basic/
│
├── Linux_OS/          # Linux, 프로세스/시스템 프로그래밍
├── Python_git/        # Python, Git
├── Data_Structures/   # Mini Redis, Mini Git
├── Web_Basics/        # Web, React
├── DB_Backend/        # SQL, FastAPI
├── Cloud_API/         # Cloud, AI API
└── Term_Project/      # AI 챗봇 서비스
```

---

## About

**기초 CS 지식을 직접 구현하고, 그 결과를 실제 소프트웨어 개발로 연결하는 과정**을 기록하고 있습니다.

각 프로젝트의 자세한 설계와 구현 내용은 프로젝트별 README에서 확인할 수 있습니다.
