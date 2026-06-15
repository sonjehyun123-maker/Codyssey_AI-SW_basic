const githubModule = {
    githubId: "sonjehyun123-maker",
    allProjects: [],
    currentFilter: "all",

    async init() {
        await this.fetchRepos();
        this.bindFilterEvents();
    },

    async fetchRepos() {
        const container = document.getElementById("project-container");
        if (!container) return;

        try {
            const response = await fetch(`https://api.github.com/users/${this.githubId}/repos?sort=updated`);
            if (!response.ok) throw new Error(`에러 발생 (코드: ${response.status})`);

            this.allProjects = await response.json();
            this.render(this.allProjects);

        } catch (error) {
            console.error(error);
            container.innerHTML = `
                <div style="text-align:center; width:100%;">
                    <p style="color: #ef4444;">프로젝트를 불러올 수 없습니다. (API 한도 초과 또는 네트워크 오류)</p>
                    <button id="retry-btn" class="btn" style="margin-top:10px; border:none; cursor:pointer;">다시 시도</button>
                </div>
            `;
            const retryBtn = document.getElementById("retry-btn");
            if (retryBtn) retryBtn.addEventListener("click", () => this.fetchRepos());
        }
    },

    render(projectsList) {
        const container = document.getElementById("project-container");
        if (!container) return;

        if (projectsList.length === 0) {
            container.innerHTML = `<p style="text-align:center; width:100%;">표시할 저장소가 없습니다.</p>`;
            return;
        }

        container.innerHTML = projectsList.map(({ name, description, html_url, language, stargazers_count }) => `
            <article class="project-card">
                <h3>${name}</h3>
                <p>${description || "설명이 없는 프로젝트입니다."}</p>
                <div style="margin-top: 10px; font-size: 14px; opacity: 0.8;">
                    <span>🛠️ ${language || "Etc"}</span> | <span>⭐ ${stargazers_count}</span>
                </div>
                <a href="${html_url}" target="_blank" rel="noopener noreferrer" class="btn" style="display:inline-block; margin-top:15px; font-size:14px; padding:5px 10px;">
                    GitHub 보기
                </a>
            </article>
        `).join("");
    },

    bindFilterEvents() {
        const filterButtons = document.querySelectorAll(".filter-btn");
        filterButtons.forEach(btn => {
            btn.addEventListener("click", (e) => {
                filterButtons.forEach(b => b.classList.remove("active"));
                e.target.classList.add("active");

                this.currentFilter = e.target.dataset.lang;
                this.filterProjects();
            });
        });
    },

    filterProjects() {
        if (this.currentFilter === "all") {
            this.render(this.allProjects);
            return;
        }

        const filtered = this.allProjects.filter(repo => {
            const lang = (repo.language || "").toLowerCase();
            if (this.currentFilter === "c") return lang === "c" || lang === "c++";
            if (this.currentFilter === "javascript") return lang === "javascript";
            if (this.currentFilter === "other") return lang !== "c" && lang !== "c++" && lang !== "javascript";
            return true;
        });
        this.render(filtered);
    }
};