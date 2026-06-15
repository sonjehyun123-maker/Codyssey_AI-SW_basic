const initCoreUI = () => {
    const menuButton = document.querySelector(".menu-btn");
    const navMenu = document.querySelector(".nav-menu");
    const scrollTopBtn = document.getElementById("scroll-top");

    if (menuButton && navMenu) {
        menuButton.addEventListener("click", () => {
            navMenu.classList.toggle("active");
        });
    }

    document.querySelectorAll(".nav-menu a").forEach(link => {
        link.addEventListener("click", () => {
            if (navMenu) navMenu.classList.remove("active");
        });
    });

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

document.addEventListener("DOMContentLoaded", () => {
    initCoreUI();
    themeModule.init();
    githubModule.init();
    formModule.init();
    animationModule.init();
});