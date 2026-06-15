const formModule = {
    init() {
        const form = document.getElementById("contact-form");
        if (!form) return;

        form.addEventListener("submit", (e) => this.handleSubmit(e));
    },

    handleSubmit(e) {
        e.preventDefault();

        const fields = {
            name: { input: document.getElementById("name"), error: document.getElementById("name-error"), msg: "이름을 입력해 주세요." },
            email: { input: document.getElementById("email"), error: document.getElementById("email-error"), msg: "이메일을 입력해 주세요." },
            message: { input: document.getElementById("message"), error: document.getElementById("message-error"), msg: "메시지를 입력해 주세요." }
        };

        let isValid = true;
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        // 에러 초기화
        Object.values(fields).forEach(f => f.error.textContent = "");
        document.getElementById("form-success").textContent = "";

        // 필수 값 검증
        Object.keys(fields).forEach(key => {
            if (!fields[key].input.value.trim()) {
                fields[key].error.textContent = fields[key].msg;
                isValid = false;
            }
        });

        // 이메일 형식 별도 검증
        if (fields.email.input.value.trim() && !emailRegex.test(fields.email.input.value.trim())) {
            fields.email.error.textContent = "올바른 이메일 형식이 아닙니다.";
            isValid = false;
        }

        if (isValid) {
            document.getElementById("form-success").textContent = "🚀 메시지가 성공적으로 전송되었습니다! (Mock)";
            document.getElementById("contact-form").reset();
        }
    }
};