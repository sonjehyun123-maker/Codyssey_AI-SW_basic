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
            if (!response.ok) throw new Error(`API 로드 실패`);

            this.allProjects = await response.json();
            this.render(this.allProjects);

        } catch (error) {
            console.error(error);
            container.innerHTML = `<p style="text-align:center; width:100%; color:#ef4444;">GitHub 프로젝트를 동적으로 가져오지 못했습니다.</p>`;
        }
    },

    render(projectsList) {
        const container = document.getElementById("project-container");
        if (!container) return;

        if (projectsList.length === 0) {
            container.innerHTML = `<p style="text-align:center; width:100%;">보유 중인 프로젝트 저장소가 없습니다.</p>`;
            return;
        }

        container.innerHTML = projectsList.map(({ name, description, html_url, language, stargazers_count }) => `
            <article class="project-card">
                <div>
                    <h3 style="color: var(--primary-color); margin-bottom: 10px; font-size: 18px; font-weight: bold;">${name}</h3>
                    <p style="font-size: 14px; opacity: 0.8; margin-bottom: 15px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; min-height: 66px;">
                        ${description || "설명이 없는 프로젝트입니다."}
                    </p>
                    <div style="font-size: 13px; opacity: 0.6; display: flex; gap: 12px; margin-bottom: 20px;">
                        <span>🛠️ ${language || "Etc"}</span>
                        <span>⭐ ${stargazers_count}</span>
                    </div>
                </div>
                <a href="${html_url}" target="_blank" rel="noopener noreferrer" class="btn" style="margin-top: 0; font-size: 13px; padding: 6px 12px; text-align: center; width: fit-content;">
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