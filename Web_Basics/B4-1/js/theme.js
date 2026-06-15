// 테마 관련 독립 상태 및 로직
const themeModule = {
    currentTheme: localStorage.getItem("theme") || "light",

    init() {
        const themeToggle = document.getElementById("theme-toggle");
        
        // 시스템 기본 테마 감지 (보너스 요구사항)
        if (!localStorage.getItem("theme")) {
            const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
            this.currentTheme = prefersDark ? "dark" : "light";
        }
        
        this.apply(this.currentTheme);

        themeToggle.addEventListener("click", () => {
            this.currentTheme = this.currentTheme === "light" ? "dark" : "light";
            this.apply(this.currentTheme);
        });
    },

    apply(theme) {
        const themeToggle = document.getElementById("theme-toggle");
        document.documentElement.setAttribute("data-theme", theme);
        themeToggle.textContent = theme === "dark" ? "🌙" : "☀️";
        localStorage.setItem("theme", theme);
    }
};