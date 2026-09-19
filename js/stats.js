async function loadStats() {
  try {
    const response = await fetch('data/stats.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('Stats data unavailable');
    const data = await response.json();

    const latest = data.latest_stream || {};
    const allTime = data.all_time || {};

    const setText = (id, value) => {
      const el = document.getElementById(id);
      if (el) el.textContent = value ?? '—';
    };

    setText('latestMessages', latest.messages);
    setText('latestChatters', latest.unique_chatters);
    setText('validatedStreams', allTime.validated_streams);
    setText('allTimeMessages', allTime.total_messages);
    setText('latestTitle', latest.title || 'Latest validated stream');

    const board = document.getElementById('streakLeaderboard');
    if (board) {
      board.innerHTML = '';
      const leaders = data.streak_leaders || [];
      if (!leaders.length) {
        board.innerHTML = '<p>Streak leaders will appear after the stats publisher is connected.</p>';
      } else {
        leaders.slice(0, 10).forEach((leader, index) => {
          const row = document.createElement('div');
          row.className = 'leader-row';
          row.innerHTML = `<span class="rank">${String(index + 1).padStart(2, '0')}</span><strong>${leader.username}</strong><span>${leader.streak} streams</span>`;
          board.appendChild(row);
        });
      }
    }

    const recap = document.getElementById('latestRecap');
    if (recap) {
      recap.innerHTML = '';
      const items = [
        ['Duration', latest.duration || '—'],
        ['Messages', latest.messages ?? '—'],
        ['Unique Chatters', latest.unique_chatters ?? '—'],
        ['Top Chatter', latest.top_chatter || '—']
      ];
      items.forEach(([label, value]) => {
        const row = document.createElement('div');
        row.className = 'leader-row';
        row.innerHTML = `<span class="rank">•</span><strong>${label}</strong><span>${value}</span>`;
        recap.appendChild(row);
      });
    }
  } catch (error) {
    console.warn(error);
  }
}

loadStats();
