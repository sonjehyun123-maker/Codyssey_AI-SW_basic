const GITHUB_USERNAME = 'sonjehyun123-maker';
const THEME_KEY = 'portfolio-theme';
const THEME_ORDER = ['green', 'light'];
const THEME_LABEL = { green: '[ GRN ]', light: '[ PPR ]' };
const ERROR_MESSAGES = {
  403: 'ERR_RATE_LIMIT: GitHub API 요청 한도를 초과했습니다.',
  404: 'ERR_NOT_FOUND: 사용자를 찾을 수 없습니다.',
};
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// 앱 전역 상태 — 모든 렌더링은 이 객체를 읽어서 수행
const STATE = {
  theme: localStorage.getItem(THEME_KEY) || 'green',
  menuOpen: false,
  scrolled: false,
  showScrollTop: false,
  projectsStatus: 'loading', // loading | success | error | empty
  projects: [],
  projectsError: '',
  formErrors: { name: '', email: '', message: '' },
};

// DOM 요소 선택
const header = document.querySelector('#siteHeader');
const hamburger = document.querySelector('#hamburger');
const navMenu = document.querySelector('#navMenu');
const themeToggle = document.querySelector('#themeToggle');
const scrollTopBtn = document.querySelector('#scrollTop');
const avatarImg = document.querySelector('#avatarImg');
const projectsContainer = document.querySelector('#projectsContainer');
const form = document.querySelector('#contactForm');

avatarImg.addEventListener('error', () => {
  avatarImg.src = 'https://placehold.co/480x480/14171C/E7EAEE?text=Jaehyun';
}, { once: true });

// 렌더 함수들: STATE를 읽어서 DOM에 반영만 함

const renderTheme = () => {
  if (STATE.theme === 'green') {
    document.documentElement.removeAttribute('data-theme');
  } else {
    document.documentElement.setAttribute('data-theme', STATE.theme);
  }
  themeToggle.textContent = THEME_LABEL[STATE.theme];
  themeToggle.setAttribute('aria-label', `테마 전환 (현재: ${STATE.theme})`);
};

const renderMenu = () => {
  navMenu.classList.toggle('active', STATE.menuOpen);
  hamburger.classList.toggle('active', STATE.menuOpen);
  hamburger.setAttribute('aria-expanded', String(STATE.menuOpen));
};

const renderHeader = () => {
  header.classList.toggle('scrolled', STATE.scrolled);
  scrollTopBtn.classList.toggle('visible', STATE.showScrollTop);
};

const renderFormErrors = () => {
  Object.entries(STATE.formErrors).forEach(([fieldId, message]) => {
    document.querySelector(`#${fieldId}Error`).textContent = message;
  });
};

const renderProjectCard = ({ name, description, html_url, stargazers_count, language }) => `
  <article class="project-card">
    <h3>&gt; ${name}</h3>
    <p>${description ?? '설명이 등록되지 않은 저장소입니다.'}</p>
    <div class="project-meta">
      <span>★ ${stargazers_count}</span>
      <span>${language ?? 'N/A'}</span>
      <a href="${html_url}" target="_blank" rel="noopener">open →</a>
    </div>
  </article>
`;

const renderProjects = () => {
  if (STATE.projectsStatus === 'loading') {
    projectsContainer.innerHTML = '<div class="state-box"><span class="blink-cursor">로딩 중</span></div>';
    return;
  }
  if (STATE.projectsStatus === 'error') {
    projectsContainer.innerHTML = `
      <div class="state-box error">
        프로젝트를 불러올 수 없습니다. (${STATE.projectsError})
        <br><button class="btn retry-btn" id="retryBtn">[ retry ]</button>
      </div>
    `;
    document.querySelector('#retryBtn').addEventListener('click', loadProjects);
    return;
  }
  if (STATE.projectsStatus === 'empty') {
    projectsContainer.innerHTML = '<div class="state-box">표시할 프로젝트가 없습니다.</div>';
    return;
  }
  const cards = STATE.projects.map(renderProjectCard).join('');
  projectsContainer.innerHTML = `<div class="projects-grid">${cards}</div>`;
};

// 이벤트: 스크롤 → STATE.scrolled / showScrollTop 갱신 → renderHeader
const handleScroll = () => {
  const y = window.scrollY;
  STATE.scrolled = y > 60;
  STATE.showScrollTop = y > 300;
  renderHeader();
};
window.addEventListener('scroll', handleScroll);
handleScroll();

// 이벤트: 햄버거 클릭 → STATE.menuOpen 토글 → renderMenu
hamburger.addEventListener('click', () => {
  STATE.menuOpen = !STATE.menuOpen;
  renderMenu();
});

navMenu.querySelectorAll('a').forEach((link) => {
  link.addEventListener('click', (event) => {
    const target = document.querySelector(link.getAttribute('href'));
    if (!target) return;
    event.preventDefault();
    target.scrollIntoView({ behavior: prefersReducedMotion ? 'auto' : 'smooth' });
    STATE.menuOpen = false;
    renderMenu();
  });
});

scrollTopBtn.addEventListener('click', () => {
  window.scrollTo({ top: 0, behavior: prefersReducedMotion ? 'auto' : 'smooth' });
});

// 이벤트: 테마 토글 클릭 → STATE.theme 순환(그린→라이트) → renderTheme
renderTheme();
themeToggle.addEventListener('click', () => {
  STATE.theme = THEME_ORDER[(THEME_ORDER.indexOf(STATE.theme) + 1) % THEME_ORDER.length];
  localStorage.setItem(THEME_KEY, STATE.theme);
  renderTheme();
});

// 스크롤 애니메이션: threshold 0.2
const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.2 }
);
document.querySelectorAll('.reveal').forEach((el) => revealObserver.observe(el));

// 부팅 로그 타이핑 효과
const bootLines = [
  '> status: [ONLINE] building things that work_',
];

const typeBootLog = async () => {
  const el = document.querySelector('#bootLog');
  if (prefersReducedMotion) {
    el.innerHTML = bootLines.map((line) => `<span class="done">${line}</span>`).join('<br>');
    return;
  }
  for (const line of bootLines) {
    let shown = '';
    for (const char of line) {
      shown += char;
      el.innerHTML = shown;
      await new Promise((resolve) => setTimeout(resolve, 18));
    }
    el.innerHTML += '<br>';
  }
};
typeBootLog();

// 이벤트: GitHub API 호출 → STATE.projectsStatus/projects 갱신 → renderProjects
const loadProjects = async () => {
  STATE.projectsStatus = 'loading';
  renderProjects();
  try {
    const response = await fetch(`https://api.github.com/users/${GITHUB_USERNAME}/repos?sort=updated&per_page=6`);
    if (!response.ok) throw new Error(ERROR_MESSAGES[response.status] ?? `ERR_HTTP_${response.status}`);
    const repos = await response.json();
    const nonForkRepos = repos.filter(({ fork }) => !fork);
    if (nonForkRepos.length === 0) {
      STATE.projectsStatus = 'empty';
    } else {
      STATE.projects = nonForkRepos;
      STATE.projectsStatus = 'success';
    }
  } catch (error) {
    STATE.projectsStatus = 'error';
    STATE.projectsError = error instanceof TypeError ? 'ERR_NETWORK: 네트워크 연결을 확인해주세요.' : error.message;
  }
  renderProjects();
};
loadProjects();

// 이벤트: 폼 입력/제출 → STATE.formErrors 갱신 → renderFormErrors
const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const validateField = (fieldId, value) => {
  if (!value.trim()) {
    STATE.formErrors[fieldId] = '# error: 필수 입력 항목입니다.';
  } else if (fieldId === 'email' && !emailPattern.test(value)) {
    STATE.formErrors[fieldId] = '# error: 이메일 형식이 올바르지 않습니다.';
  } else {
    STATE.formErrors[fieldId] = '';
  }
  renderFormErrors();
  return STATE.formErrors[fieldId] === '';
};

['name', 'email', 'message'].forEach((fieldId) => {
  const field = document.querySelector(`#${fieldId}`);
  field.addEventListener('input', () => validateField(fieldId, field.value));
});

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const { name, email, message } = Object.fromEntries(new FormData(form));
  const results = [
    validateField('name', name),
    validateField('email', email),
    validateField('message', message),
  ];
  const successEl = document.querySelector('#formSuccess');
  successEl.textContent = results.every(Boolean)
    ? `> message_sent.log ✓  ${name}님, 메시지가 준비됐습니다.`
    : '';
  if (results.every(Boolean)) form.reset();
});