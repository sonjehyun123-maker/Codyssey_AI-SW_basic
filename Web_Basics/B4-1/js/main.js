// 기본 UI 인터랙션 바인딩
const initCoreUI = () => {
    const menuButton = document.querySelector(".menu-btn");
    const navMenu = document.querySelector(".nav-menu");
    const header = document.querySelector("header");
    const scrollTopBtn = document.getElementById("scroll-top");

    // 햄버거 메뉴 토글
    menuButton.addEventListener("click", () => {
        navMenu.classList.toggle("active");
    });

    // 메뉴 클릭 시 네비게이션 닫기
    document.querySelectorAll(".nav-menu a").forEach(link => {
        link.addEventListener("click", () => {
            navMenu.classList.remove("active");
        });
    });

    // 스크롤 연동 기능
    window.addEventListener("scroll", () => {
        const scrollY = window.scrollY;

        // 상단 네비게이션 스타일 변환 (60px 기준)
        if (scrollY > 60) {
            header.classList.add("scrolled");
        } else {
            header.classList.remove("scrolled");
        }

        // 스크롤 탑 버튼 활성화 (300px 기준)
        if (scrollY > 300) {
            scrollTopBtn.style.display = "flex";
        } else {
            scrollTopBtn.style.display = "none";
        }
    });

    // 탑 버튼 클릭 이벤트
    scrollTopBtn.addEventListener("click", () => {
        window.scrollTo({ top: 0, behavior: "smooth" });
    });
};

// DOM 구축이 완료되면 분할된 모든 모듈 초기화
document.addEventListener("DOMContentLoaded", () => {
    initCoreUI();
    themeModule.init();
    githubModule.init();
    formModule.init();
    animationModule.init();
});