const formModule = {
    init() {
        const form = document.getElementById("contact-form");
        if (!form) return;

        form.addEventListener("submit", (e) => this.handleSubmit(e));
    },

    handleSubmit(e) {
        e.preventDefault();

        const fields = {
            name: { input: document.getElementById("name"), error: document.getElementById("name-error"), msg: "이름을 채워주세요." },
            email: { input: document.getElementById("email"), error: document.getElementById("email-error"), msg: "이메일을 채워주세요." },
            message: { input: document.getElementById("message"), error: document.getElementById("message-error"), msg: "메시지를 채워주세요." }
        };

        let isValid = true;
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        Object.values(fields).forEach(f => { if(f.error) f.error.textContent = ""; });
        const successDiv = document.getElementById("form-success");
        if (successDiv) successDiv.textContent = "";

        Object.keys(fields).forEach(key => {
            if (!fields[key].input.value.trim()) {
                if (fields[key].error) fields[key].error.textContent = fields[key].msg;
                isValid = false;
            }
        });

        if (fields.email.input.value.trim() && !emailRegex.test(fields.email.input.value.trim())) {
            if (fields.email.error) fields.email.error.textContent = "올바른 이메일 포맷이 아닙니다.";
            isValid = false;
        }

        if (isValid) {
            if (successDiv) successDiv.textContent = "🚀 유효성 검사가 완료되었습니다!";
            document.getElementById("contact-form").reset();
        }
    }
};