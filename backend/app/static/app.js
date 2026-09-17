const form = document.querySelector('#search-form');
const input = document.querySelector('#query');
const conversation = document.querySelector('#conversation');
const statusBox = document.querySelector('#status');
const submitButton = document.querySelector('#submit-button');

document.querySelectorAll('.suggestion').forEach((button) => {
  button.addEventListener('click', () => {
    input.value = button.dataset.query;
    input.focus();
  });
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const query = input.value.trim();
  if (!query) return;
  const turn = document.createElement('article');
  turn.className = 'turn';
  const question = document.createElement('div');
  question.className = 'query-bubble';
  question.textContent = query;
  const reply = document.createElement('div');
  reply.className = 'reply';
  reply.innerHTML = '<p class="muted">Searching the demo catalog…</p>';
  turn.append(question, reply);
  conversation.append(turn);
  statusBox.hidden = true;
  submitButton.disabled = true;
  input.value = '';
  try {
    const response = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status})`);
    renderResponse(reply, payload);
  } catch (error) {
    reply.innerHTML = '';
    const message = document.createElement('p');
    message.className = 'intent-message';
    message.textContent = `The search service could not complete this request. ${error.message}`;
    reply.append(message);
  } finally {
    submitButton.disabled = false;
    input.focus();
    turn.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
});

function renderResponse(container, data) {
  container.replaceChildren();
  if (data.intent !== 'briefing' && !(data.intent === 'clarification' && data.scope_options?.length)) {
    const tag = make('span', 'tag warning', intentLabel(data.intent));
    const row = make('div', 'reply-heading');
    row.append(make('h2', '', intentTitle(data.intent)), tag);
    container.append(row, make('p', 'intent-message', data.message || 'Please refine your search.'));
    return;
  }
  if (data.presentation?.scope_summary) {
    container.append(make('p', 'scope-caption', `Search context: ${data.presentation.scope_summary}`));
  }
  if (data.intent === 'clarification' || data.scope_options?.length) {
    container.append(make('div', 'unavailable', data.message || 'Choose a scope or add more detail.'));
    renderScopeOptions(container, data.scope_options || [], data.query);
    return;
  }
  for (const result of data.results || []) container.append(renderScopeResult(result));
  for (const note of data.data_status || []) container.append(make('p', 'data-note', note));
}

function renderScopeResult(result) {
  const wrapper = make('section', 'scope-result');
  const header = make('div', 'reply-heading');
  const title = make('div');
  title.append(make('h2', '', result.scope.condition));
  title.append(make('p', 'scope-caption', `${result.scope.reason} · match ${Math.round(result.scope.confidence * 100)}%`));
  header.append(title, make('span', 'tag warning', result.standard_procedure ? 'Approved record' : 'Illustrative sample'));
  wrapper.append(header);

  const procSection = make('section', 'content-section');
  procSection.append(make('h3', '', 'Standard procedure'));
  const procedure = result.standard_procedure || result.illustrative_procedure;
  if (procedure) {
    const box = make('div', 'procedure-box');
    for (const [heading, text] of Object.entries(procedure.sections || {})) {
      box.append(make('h4', '', heading), make('p', '', text));
    }
    procSection.append(box);
    procSection.append(make('p', 'procedure-status', `${result.procedure_status || 'Stored source record'} · Record ${procedure.id} · v${procedure.version} · reviewed ${procedure.review_date} · `));
    const statusLine = procSection.querySelector('.procedure-status');
    statusLine.append(link(procedure.source, 'View guideline/source'));
  } else {
    procSection.append(make('p', 'unavailable', result.procedure_status || 'No approved procedure is available for this scope.'));
  }
  wrapper.append(procSection);

  const treatmentsSection = make('section', 'content-section');
  treatmentsSection.append(make('h3', '', `Emerging treatments (${result.emerging_treatments?.length || 0})`));
  if (!result.emerging_treatments?.length) {
    treatmentsSection.append(make('p', 'empty-treatment', 'No matching treatment records were found in the demo catalog.'));
  } else {
    treatmentsSection.append(renderTreatmentTable(result.emerging_treatments));
  }
  wrapper.append(treatmentsSection);
  return wrapper;
}

function renderTreatmentTable(records) {
  const holder = make('div', 'table-wrap');
  const table = document.createElement('table');
  const headers = ['Treatment', 'Studied condition', 'Stage / status', 'Reported result', 'Organization', 'Source'];
  const thead = document.createElement('thead');
  const headerRow = document.createElement('tr');
  headers.forEach((name) => headerRow.append(make('th', '', name)));
  thead.append(headerRow);
  const tbody = document.createElement('tbody');
  records.forEach((record) => {
    const row = document.createElement('tr');
    const treatmentCell = document.createElement('td');
    treatmentCell.append(make('span', '', record.treatment));
    treatmentCell.append(document.createElement('br'));
    const detailButton = make('button', 'detail-button', 'View details');
    detailButton.type = 'button';
    detailButton.addEventListener('click', () => loadDetail(record.id, detailButton.closest('tr')));
    treatmentCell.append(detailButton);
    row.append(treatmentCell);
    row.append(make('td', '', record.studied_condition || record.condition));
    row.append(make('td', '', record.stage));
    row.append(make('td', '', record.result));
    row.append(make('td', '', record.organization || 'Not listed'));
    const source = document.createElement('td');
    source.append(link(record.source, record.source_type || 'Source'));
    source.append(make('div', 'muted', `Reviewed ${record.review_date || 'date unavailable'}`));
    row.append(source);
    tbody.append(row);
  });
  table.append(thead, tbody);
  holder.append(table);
  return holder;
}

async function loadDetail(id, row) {
  let detail = row.nextElementSibling;
  if (detail?.classList.contains('detail-row')) {
    detail.remove();
    return;
  }
  const response = await fetch(`/api/treatments/${encodeURIComponent(id)}`);
  const data = await response.json();
  detail = document.createElement('tr');
  detail.className = 'detail-row';
  const cell = document.createElement('td');
  cell.colSpan = 6;
  const panel = make('div', 'treatment-detail');
  panel.append(make('h4', '', data.record?.treatment || 'Treatment details'));
  panel.append(make('p', '', data.message));
  if (data.record) {
    panel.append(make('p', '', `Type: ${data.record.type || 'Not specified'} · Studied condition: ${data.record.studied_condition}`));
    panel.append(make('p', '', `Reported result: ${data.record.result}`));
    panel.append(make('p', '', `Organization: ${data.record.organization || 'Not listed'}`));
    panel.append(link(data.record.source, data.record.source_type || 'Open source'));
  }
  cell.append(panel);
  detail.append(cell);
  row.after(detail);
}

function renderScopeOptions(container, options, query) {
  if (!options.length) return;
  const list = make('div', 'scope-options');
  list.append(make('h3', '', 'Choose a condition scope'));
  options.forEach((option) => {
    const button = make('button', 'scope-option');
    button.type = 'button';
    button.append(make('strong', '', option.condition));
    button.append(make('small', '', option.reason || 'Possible match'));
    button.addEventListener('click', async () => {
      button.disabled = true;
      button.querySelector('small').textContent = 'Loading this scope…';
      try {
        const response = await fetch('/api/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query, selected_scope_id: option.id }),
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || 'Could not load scope.');
        renderResponse(container, payload);
      } catch (error) {
        button.querySelector('small').textContent = error.message;
        button.disabled = false;
      }
    });
    list.append(button);
  });
  container.append(list);
}

function link(url, label) {
  const anchor = document.createElement('a');
  anchor.className = 'source-link';
  anchor.href = url;
  anchor.target = '_blank';
  anchor.rel = 'noopener noreferrer';
  anchor.textContent = label;
  return anchor;
}

function make(tag, className = '', text = '') {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== '') node.textContent = text;
  return node;
}

function intentLabel(intent) {
  return ({ urgent: 'Urgent', personalized_request: 'Personal care request', out_of_scope: 'Out of scope', incomplete: 'More detail needed', clarification: 'Clarification' })[intent] || 'Notice';
}
function intentTitle(intent) {
  return ({ urgent: 'Please seek immediate help', personalized_request: 'This tool can’t recommend personal treatment', out_of_scope: 'This search is outside the demo scope', incomplete: 'Tell us a little more' })[intent] || 'Let’s refine the search';
}
