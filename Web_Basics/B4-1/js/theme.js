const themeModule = {
    currentTheme: localStorage.getItem("theme") || "light",

    init() {
        const themeToggle = document.getElementById("theme-toggle");
        if (!themeToggle) return;

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
        if (themeToggle) {
            themeToggle.textContent = theme === "dark" ? "🌙" : "☀️";
        }
        localStorage.setItem("theme", theme);
    }
};