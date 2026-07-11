// ============================================
// 1) 다크 모드: 상태 → 전체 화면 스타일 변경 (localStorage 유지)
// ============================================
const root = document.documentElement;
const themeToggle = document.querySelector('#theme-toggle');
const themeIcon = themeToggle.querySelector('i');

const applyTheme = (theme) => {
  if (theme === 'dark') {
    root.setAttribute('data-theme', 'dark');
    themeIcon.classList.remove('fa-moon');
    themeIcon.classList.add('fa-sun');
  } else {
    root.removeAttribute('data-theme');
    themeIcon.classList.remove('fa-sun');
    themeIcon.classList.add('fa-moon');
  }
};

const savedTheme = localStorage.getItem('theme') ||
  (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
applyTheme(savedTheme);

themeToggle.addEventListener('click', () => {
  const isDark = root.getAttribute('data-theme') === 'dark';
  const next = isDark ? 'light' : 'dark';
  applyTheme(next);
  localStorage.setItem('theme', next);
});

// ============================================
// 2) 햄버거 메뉴 토글
// ============================================
const burger = document.querySelector('#burger');
const navMenu = document.querySelector('#nav-menu');

burger.addEventListener('click', () => {
  const isActive = navMenu.classList.toggle('active');
  burger.classList.toggle('active', isActive);
  burger.setAttribute('aria-expanded', String(isActive));
});

document.querySelectorAll('.nav__link').forEach((link) => {
  link.addEventListener('click', () => {
    navMenu.classList.remove('active');
    burger.classList.remove('active');
    burger.setAttribute('aria-expanded', 'false');
  });
});

// ============================================
// 3) 스크롤 이벤트: 헤더 배경 변경 + 스크롤 탑 버튼 표시
// ============================================
const header = document.querySelector('#site-header');
const scrollTopBtn = document.querySelector('#scroll-top');

const NAV_SCROLL_THRESHOLD = 60;
const SCROLL_TOP_THRESHOLD = 300;

window.addEventListener('scroll', () => {
  const y = window.scrollY;
  header.classList.toggle('scrolled', y > NAV_SCROLL_THRESHOLD);
  scrollTopBtn.classList.toggle('visible', y > SCROLL_TOP_THRESHOLD);
});

scrollTopBtn.addEventListener('click', () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ============================================
// 4) 스크롤 애니메이션 (Intersection Observer)
// ============================================
const REVEAL_THRESHOLD = 0.2;

const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: REVEAL_THRESHOLD }
);

document.querySelectorAll('.reveal').forEach((el) => revealObserver.observe(el));

// ============================================
// 5) 폼 유효성 검사: 입력 → 상태 변경 → 에러 메시지 표시/숨김
// ============================================
const form = document.querySelector('#contact-form');
const successMsg = document.querySelector('#form-success');

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const setFieldError = (fieldId, message) => {
  const field = document.querySelector(`#${fieldId}`);
  const errorEl = document.querySelector(`#${fieldId}-error`);
  const wrapper = field.closest('.form-field');

  wrapper.classList.toggle('invalid', Boolean(message));
  errorEl.textContent = message || '';
};

const validateField = (fieldId) => {
  const field = document.querySelector(`#${fieldId}`);
  const value = field.value.trim();

  if (!value) {
    setFieldError(fieldId, '필수 입력 항목입니다.');
    return false;
  }
  if (fieldId === 'email' && !EMAIL_REGEX.test(value)) {
    setFieldError(fieldId, '올바른 이메일 형식이 아닙니다.');
    return false;
  }
  setFieldError(fieldId, '');
  return true;
};

['name', 'email', 'message'].forEach((fieldId) => {
  const field = document.querySelector(`#${fieldId}`);
  field.addEventListener('input', () => validateField(fieldId));
});

form.addEventListener('submit', (event) => {
  event.preventDefault();

  const results = ['name', 'email', 'message'].map(validateField);
  const isValid = results.every(Boolean);

  if (!isValid) {
    successMsg.textContent = '';
    return;
  }

  successMsg.textContent = '메시지가 성공적으로 전송되었습니다. 빠르게 답변드릴게요!';
  form.reset();
  ['name', 'email', 'message'].forEach((fieldId) => setFieldError(fieldId, ''));
});

// ============================================
// 6) GitHub API 연동: 호출 → 로딩/성공/에러 상태 → Projects 렌더링
// ============================================
const GITHUB_USERNAME = 'sonjehyun123-maker';
const statusEl = document.querySelector('#projects-status');
const gridEl = document.querySelector('#projects-grid');

const escapeHtml = (str = '') =>
  str.replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));

const renderLoading = () => {
  statusEl.className = 'projects__status';
  statusEl.innerHTML = `<span class="spinner"></span>로딩 중...`;
  gridEl.innerHTML = '';
};

const renderError = () => {
  statusEl.className = 'projects__status error';
  statusEl.innerHTML = `프로젝트를 불러올 수 없습니다. <button class="retry-btn" id="retry-btn">다시 시도</button>`;
  gridEl.innerHTML = '';
  document.querySelector('#retry-btn').addEventListener('click', loadProjects);
};

const renderEmpty = () => {
  statusEl.className = 'projects__status';
  statusEl.textContent = '표시할 프로젝트가 없습니다.';
  gridEl.innerHTML = '';
};

const renderProjects = (repos) => {
  statusEl.className = 'projects__status';
  statusEl.textContent = '';

  const cards = repos
    .map(({ name, description, html_url, language, stargazers_count }) => `
      <article class="project-card">
        <div class="project-card__bar">
          <span class="dot dot--red"></span>
          <span class="dot dot--yellow"></span>
          <span class="dot dot--green"></span>
        </div>
        <div class="project-card__body">
          <h3 class="project-card__name">${escapeHtml(name)}</h3>
          <p class="project-card__desc">${escapeHtml(description || '설명이 등록되지 않은 저장소입니다.')}</p>
          <div class="project-card__meta">
            <span><i class="fa-solid fa-code"></i>${escapeHtml(language || '—')}</span>
            <span><i class="fa-solid fa-star"></i>${stargazers_count}</span>
          </div>
          <a class="project-card__link" href="${html_url}" target="_blank" rel="noopener">
            저장소 보기 <i class="fa-solid fa-arrow-up-right-from-square"></i>
          </a>
        </div>
      </article>
    `)
    .join('');

  gridEl.innerHTML = cards;
};

async function loadProjects() {
  renderLoading();

  try {
    const response = await fetch(`https://api.github.com/users/${GITHUB_USERNAME}/repos?sort=updated&per_page=9`);

    if (!response.ok) {
      throw new Error(`GitHub API error: ${response.status}`);
    }

    const repos = await response.json();

    if (!Array.isArray(repos) || repos.length === 0) {
      renderEmpty();
      return;
    }

    renderProjects(repos);
  } catch (error) {
    console.error(error);
    renderError();
  }
}

loadProjects();
