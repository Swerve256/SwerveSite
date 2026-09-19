function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value ?? '—';
}

function formatPublishedTime(value) {
  if (!value) return 'Waiting for first published snapshot';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return `Last published ${parsed.toLocaleString()}`;
}

function createLeaderRow(rank, name, value) {
  const row = document.createElement('div');
  row.className = 'leader-row';

  const rankEl = document.createElement('span');
  rankEl.className = 'rank';
  rankEl.textContent = rank;

  const nameEl = document.createElement('strong');
  nameEl.textContent = name || 'Unknown viewer';

  const valueEl = document.createElement('span');
  valueEl.textContent = value;

  row.append(rankEl, nameEl, valueEl);
  return row;
}

function renderLeaderboard(id, items, valueFormatter, emptyMessage = 'Waiting for published stats.') {
  const board = document.getElementById(id);
  if (!board) return;
  board.innerHTML = '';

  if (!items?.length) {
    const empty = document.createElement('p');
    empty.textContent = emptyMessage;
    board.appendChild(empty);
    return;
  }

  items.slice(0, 10).forEach((item, index) => {
    board.appendChild(
      createLeaderRow(
        String(index + 1).padStart(2, '0'),
        item.username,
        valueFormatter(item)
      )
    );
  });
}

async function loadStats() {
  try {
    const response = await fetch(`data/stats.json?v=${Date.now()}`, { cache: 'no-store' });
    if (!response.ok) throw new Error('Stats data unavailable');
    const data = await response.json();

    const latest = data.latest_stream || {};
    const allTime = data.all_time || {};
    const streaks = data.streak_leaders || [];

    setText('latestMessages', latest.messages);
    setText('latestChatters', latest.unique_chatters);
    setText('validatedStreams', allTime.validated_streams);
    setText('allTimeMessages', allTime.total_messages);
    setText('allTimeChatters', allTime.unique_chatters);
    setText('longestCurrentStreak', streaks[0]?.streak ?? '—');
    setText('latestTitle', latest.title || 'Latest validated stream');
    setText('latestMeta', [latest.date, latest.game].filter(Boolean).join(' • ') || 'Validated stream summary');
    setText('statsUpdated', formatPublishedTime(data.generated_at));

    renderLeaderboard(
      'streakLeaderboard',
      streaks,
      item => `${item.streak} streams`,
      'Streak leaders will appear after the stats publisher is connected.'
    );

    const recap = document.getElementById('latestRecap');
    if (recap) {
      recap.innerHTML = '';
      const items = [
        ['Duration', latest.duration || '—'],
        ['Messages', latest.messages ?? '—'],
        ['Unique Chatters', latest.unique_chatters ?? '—'],
        ['Top Chatter', latest.top_chatter || '—']
      ];
      items.forEach(([label, value]) => recap.appendChild(createLeaderRow('•', label, value)));
    }

    renderLeaderboard('latestChattersBoard', data.top_chatters || [], item => `${item.messages} messages`);
    renderLeaderboard('allTimeChattersBoard', data.all_time_chatters || [], item => `${item.messages} messages`);
  } catch (error) {
    console.warn(error);
    setText('statsUpdated', 'Stats temporarily unavailable');
  }
}

loadStats();
