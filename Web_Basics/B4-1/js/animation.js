const animationModule = {
    init() {
        const observerOptions = {
            root: null,
            threshold: 0.2 // 명세서 권장 임계값 준수
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("appear");
                    observer.unobserve(entry.target); // 한 번만 등장하도록 관찰 해제
                }
            });
        }, observerOptions);

        document.querySelectorAll(".fade-in").forEach(section => {
            observer.observe(section);
        });
    }
};