function recapSetText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value ?? '—';
}

function recapRow(rank, label, value) {
  const row = document.createElement('div');
  row.className = 'leader-row';

  const rankEl = document.createElement('span');
  rankEl.className = 'rank';
  rankEl.textContent = rank;

  const labelEl = document.createElement('strong');
  labelEl.textContent = label;

  const valueEl = document.createElement('span');
  valueEl.textContent = value;

  row.append(rankEl, labelEl, valueEl);
  return row;
}

async function loadRecap() {
  try {
    const response = await fetch(`data/stats.json?v=${Date.now()}`, { cache: 'no-store' });
    if (!response.ok) throw new Error('Stats data unavailable');
    const data = await response.json();
    const latest = data.latest_stream || {};
    const allTime = data.all_time || {};

    recapSetText('latestTitle', latest.title || 'Latest Stream');
    recapSetText('recapDate', latest.date || 'Validated stream summary');
    recapSetText('latestMessages', latest.messages);
    recapSetText('latestChatters', latest.unique_chatters);
    recapSetText('recapDuration', latest.duration || '—');
    recapSetText('validatedStreams', allTime.validated_streams);

    const board = document.getElementById('streakLeaderboard');
    if (board) {
      board.innerHTML = '';
      const leaders = (data.streak_leaders || []).slice(0, 5);
      if (!leaders.length) {
        board.appendChild(recapRow('—', 'Waiting on published stats', '—'));
      } else {
        leaders.forEach((leader, index) => {
          board.appendChild(recapRow(String(index + 1), leader.username || 'Unknown viewer', `${leader.streak} streams`));
        });
      }
    }

    const recap = document.getElementById('latestRecap');
    if (recap) {
      recap.innerHTML = '';
      [
        ['Top Chatter', latest.top_chatter || '—'],
        ['Messages', latest.messages ?? '—'],
        ['Unique Chatters', latest.unique_chatters ?? '—'],
        ['All-Time Messages', allTime.total_messages ?? '—']
      ].forEach(([label, value]) => recap.appendChild(recapRow('•', label, value)));
    }
  } catch (error) {
    console.warn(error);
  }
}

loadRecap();
setInterval(loadRecap, 60000);
