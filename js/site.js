const favicon = document.createElement('link');
favicon.rel = 'icon';
favicon.type = 'image/webp';
favicon.href = 'assets/swerve-logo.webp';
document.head.appendChild(favicon);

const toggle = document.querySelector('.nav-toggle');
const nav = document.querySelector('.site-nav');

if (nav && !nav.querySelector('a[href="music.html"]')) {
  const musicLink = document.createElement('a');
  musicLink.href = 'music.html';
  musicLink.textContent = 'Music';

  const communityLink = nav.querySelector('a[href="community.html"]');
  if (communityLink) nav.insertBefore(musicLink, communityLink);
  else nav.appendChild(musicLink);
}

const onMusicPage = window.location.pathname.endsWith('/music.html') || window.location.pathname.endsWith('music.html');
if (nav && onMusicPage) {
  nav.querySelectorAll('a').forEach(link => link.classList.remove('active'));
  const musicLink = nav.querySelector('a[href="music.html"]');
  if (musicLink) musicLink.classList.add('active');
}

if (toggle && nav) {
  toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(open));
  });
}

const footerLinks = document.querySelector('.footer-links');
if (footerLinks && !footerLinks.querySelector('a[href="music.html"]')) {
  const musicFooterLink = document.createElement('a');
  musicFooterLink.href = 'music.html';
  musicFooterLink.textContent = 'Music';

  const communityFooterLink = footerLinks.querySelector('a[href="community.html"]');
  if (communityFooterLink) footerLinks.insertBefore(musicFooterLink, communityFooterLink);
  else footerLinks.appendChild(musicFooterLink);
}

const year = document.getElementById('year');
if (year) year.textContent = new Date().getFullYear();
