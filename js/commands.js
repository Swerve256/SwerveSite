async function loadCommands() {
  const list = document.getElementById('commandsList');
  const search = document.getElementById('commandSearch');
  const filter = document.getElementById('commandFilter');
  const count = document.getElementById('commandCount');

  try {
    const response = await fetch('data/commands.json', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    const commands = Array.isArray(data.commands) ? data.commands : [];

    const categories = [...new Set(commands.map(item => item.category).filter(Boolean))].sort();
    categories.forEach(category => {
      const option = document.createElement('option');
      option.value = category;
      option.textContent = category;
      filter.appendChild(option);
    });

    function render() {
      const query = search.value.trim().toLowerCase();
      const selected = filter.value;

      const visible = commands.filter(item => {
        const commandText = item.commands.join(' ').toLowerCase();
        const haystack = `${commandText} ${item.description} ${item.access} ${item.category}`.toLowerCase();
        return (!query || haystack.includes(query)) && (!selected || item.category === selected);
      });

      count.textContent = `${visible.length} command groups`;
      list.innerHTML = '';

      if (!visible.length) {
        list.innerHTML = '<p class="commands-empty">No commands match that search.</p>';
        return;
      }

      visible.forEach(item => {
        const row = document.createElement('article');
        row.className = 'command-row';

        const commandCell = document.createElement('div');
        commandCell.className = 'command-name';
        item.commands.forEach(command => {
          const code = document.createElement('code');
          code.textContent = command;
          commandCell.appendChild(code);
        });

        const body = document.createElement('div');
        body.className = 'command-body';
        const title = document.createElement('strong');
        title.textContent = item.description;
        const meta = document.createElement('div');
        meta.className = 'command-meta';
        meta.innerHTML = `<span>${item.category}</span><span>${item.access}</span>`;
        body.appendChild(title);
        body.appendChild(meta);

        row.appendChild(commandCell);
        row.appendChild(body);
        list.appendChild(row);
      });
    }

    search.addEventListener('input', render);
    filter.addEventListener('change', render);
    render();
  } catch (error) {
    list.innerHTML = '<p class="commands-empty">Commands are temporarily unavailable.</p>';
    count.textContent = 'Unable to load commands';
    console.error(error);
  }
}

loadCommands();
