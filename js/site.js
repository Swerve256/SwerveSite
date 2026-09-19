const favicon = document.createElement('link');
favicon.rel = 'icon';
favicon.type = 'image/webp';
favicon.href = 'assets/swerve-logo.webp';
document.head.appendChild(favicon);

const toggle = document.querySelector('.nav-toggle');
const nav = document.querySelector('.site-nav');

if (toggle && nav) {
  toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(open));
  });
}

const year = document.getElementById('year');
if (year) year.textContent = new Date().getFullYear();
