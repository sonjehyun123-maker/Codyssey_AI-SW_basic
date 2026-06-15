const animationModule = {
    init() {
        const observerOptions = {
            root: null,
            threshold: 0.1
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("appear");
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        document.querySelectorAll(".fade-in").forEach(section => {
            observer.observe(section);
        });
    }
};