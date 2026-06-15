// 재현님이 구현하셨던 원본 코어 코드를 그대로 포함하여 확장
const initCoreUI = () => {
    const menuButton = document.querySelector(".menu-btn");
    const navMenu = document.querySelector(".nav-menu");
    const scrollTopBtn = document.getElementById("scroll-top");

    if (menuButton && navMenu) {
        menuButton.addEventListener("click", () => {
            console.log("클릭됨");
            navMenu.classList.toggle("active");
        });
    }

    document.querySelectorAll(".nav-menu a").forEach(link => {
        link.addEventListener("click", () => {
            if(navMenu) navMenu.classList.remove("active");
        });
    });

    // 스크롤 탑 컴포넌트 핸들링
    window.addEventListener("scroll", () => {
        if (!scrollTopBtn) return;
        if (window.scrollY > 300) {
            scrollTopBtn.style.display = "flex";
        } else {
            scrollTopBtn.style.display = "none";
        }
    });

    if (scrollTopBtn) {
        scrollTopBtn.addEventListener("click", () => {
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }
};

// 모든 개별 파일이 정상 로드된 상태에서 중앙 집중식 허브 제어 실행
document.addEventListener("DOMContentLoaded", () => {
    initCoreUI();
    themeModule.init();
    githubModule.init();
    formModule.init();
    animationModule.init();
});