const themeModule = {
    currentTheme: localStorage.getItem("theme") || "dark",

    init() {
        const themeToggle = document.getElementById("theme-toggle");
        if (!themeToggle) return;
        
        this.apply(this.currentTheme);

        themeToggle.addEventListener("click", () => {
            this.currentTheme = this.currentTheme === "light" ? "dark" : "light";
            this.apply(this.currentTheme);
        });
    },

    apply(theme) {
        const themeToggle = document.getElementById("theme-toggle");
        document.documentElement.setAttribute("data-theme", theme);
        if (themeToggle) {
            themeToggle.textContent = theme === "dark" ? "🌙" : "☀️";
        }
        localStorage.setItem("theme", theme);
    }
};