const musicGrid = document.getElementById('musicGrid');

function escapeHtml(value = '') {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function renderTrack(track) {
  const title = escapeHtml(track.title || 'Untitled');
  const artist = escapeHtml(track.artist || 'Swerve256');
  const category = escapeHtml(track.category || 'TRACK');
  const description = escapeHtml(track.description || '');
  const cover = track.cover ? `<img src="${escapeHtml(track.cover)}" alt="${title} cover art">` : '<span>SW256</span>';
  const player = track.audio
    ? `<audio class="music-player" controls preload="none"><source src="${escapeHtml(track.audio)}"></audio>`
    : '<div class="music-status">Audio file coming soon.</div>';

  const actions = [];
  if (track.suno) actions.push(`<a href="${escapeHtml(track.suno)}" target="_blank" rel="noopener">Listen on Suno</a>`);
  if (track.youtube) actions.push(`<a href="${escapeHtml(track.youtube)}" target="_blank" rel="noopener">Watch on YouTube</a>`);

  return `
    <article class="music-card">
      <div class="music-art">${cover}</div>
      <div class="music-meta">
        <span class="music-tag">${category}</span>
        <h3>${title}</h3>
        <p><strong>${artist}</strong>${description ? ` — ${description}` : ''}</p>
        ${player}
        ${actions.length ? `<div class="music-actions">${actions.join('')}</div>` : ''}
      </div>
    </article>`;
}

async function loadMusic() {
  if (!musicGrid) return;

  try {
    const response = await fetch('data/music.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    const tracks = Array.isArray(data.tracks) ? data.tracks : [];

    if (!tracks.length) {
      musicGrid.innerHTML = `
        <article class="music-empty">
          <p class="eyebrow">MUSIC LIBRARY</p>
          <h3>The catalog is ready.</h3>
          <p>Add tracks to <code>data/music.json</code> and they will appear here automatically.</p>
        </article>`;
      return;
    }

    musicGrid.innerHTML = tracks.map(renderTrack).join('');
  } catch (error) {
    console.error('Could not load music catalog:', error);
    musicGrid.innerHTML = `
      <article class="music-empty">
        <p class="eyebrow">MUSIC LIBRARY</p>
        <h3>Could not load the catalog.</h3>
        <p>Refresh the page or check <code>data/music.json</code>.</p>
      </article>`;
  }
}

loadMusic();
