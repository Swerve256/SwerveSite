async function loadRecap() {
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

    setText('latestTitle', latest.title || 'Latest Stream');
    setText('recapDate', latest.date || 'Validated stream summary');
    setText('latestMessages', latest.messages);
    setText('latestChatters', latest.unique_chatters);
    setText('recapDuration', latest.duration || '—');
    setText('validatedStreams', allTime.validated_streams);

    const board = document.getElementById('streakLeaderboard');
    board.innerHTML = '';
    const leaders = (data.streak_leaders || []).slice(0, 5);
    if (!leaders.length) {
      board.innerHTML = '<div class="leader-row"><span class="rank">—</span><strong>Waiting on published stats</strong><span>—</span></div>';
    } else {
      leaders.forEach((leader, index) => {
        const row = document.createElement('div');
        row.className = 'leader-row';
        row.innerHTML = `<span class="rank">${index + 1}</span><strong>${leader.username}</strong><span>${leader.streak}</span>`;
        board.appendChild(row);
      });
    }

    const recap = document.getElementById('latestRecap');
    recap.innerHTML = '';
    [
      ['Top Chatter', latest.top_chatter || '—'],
      ['Messages', latest.messages ?? '—'],
      ['Unique Chatters', latest.unique_chatters ?? '—'],
      ['All-Time Messages', allTime.total_messages ?? '—']
    ].forEach(([label, value]) => {
      const row = document.createElement('div');
      row.className = 'leader-row';
      row.innerHTML = `<span class="rank">•</span><strong>${label}</strong><span>${value}</span>`;
      recap.appendChild(row);
    });
  } catch (error) {
    console.warn(error);
  }
}

loadRecap();