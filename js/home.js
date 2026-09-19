async function loadHomeStats() {
  try {
    const response = await fetch('data/stats.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('Stats unavailable');
    const data = await response.json();
    const latest = data.latest_stream || {};
    const leaders = data.streak_leaders || [];

    const setText = (id, value) => {
      const el = document.getElementById(id);
      if (el) el.textContent = value ?? '—';
    };

    setText('homeLatestTitle', latest.title || 'Latest validated stream');
    setText('homeMessages', latest.messages ?? '—');
    setText('homeChatters', latest.unique_chatters ?? '—');
    setText('homeDuration', latest.duration || '—');

    const list = document.getElementById('homeStreakLeaders');
    if (!list) return;
    list.innerHTML = '';

    if (!leaders.length) {
      list.innerHTML = '<p class="muted-copy">Streak leaders will appear when the stream stats publisher goes live.</p>';
      return;
    }

    leaders.slice(0, 5).forEach((leader, index) => {
      const row = document.createElement('div');
      row.className = 'home-leader';
      row.innerHTML = `<span class="rank">${String(index + 1).padStart(2, '0')}</span><strong>${leader.username}</strong><span>${leader.streak} streams</span>`;
      list.appendChild(row);
    });
  } catch (error) {
    console.warn(error);
  }
}

loadHomeStats();