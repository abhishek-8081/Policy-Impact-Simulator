async function loadScenarios() {
  try {
    const res = await fetch('/scenarios');
    const scenarios = await res.json();
    renderScenarioList(scenarios);
    populateCompareDropdowns(scenarios);
    return scenarios;
  } catch (e) {
    console.error('Failed to load scenarios', e);
    return [];
  }
}

async function createScenario(name, model) {
  const params = readParameterInputs();
  const run_config = readRunConfig();
  const res = await fetch('/scenarios', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, model, parameters: params, run_config }),
  });
  if (!res.ok) throw new Error((await res.json()).error || 'Create failed');
  return res.json();
}

async function loadScenario(id) {
  const res = await fetch(`/scenarios/${id}`);
  if (!res.ok) throw new Error('Scenario not found');
  const s = await res.json();
  applyScenarioToForm(s);
  window._activeScenarioId = id;
  document.querySelectorAll('.scenario-item').forEach(el => {
    el.classList.toggle('active', el.dataset.id === id);
  });
  return s;
}

async function updateScenario(id) {
  const params = readParameterInputs();
  const run_config = readRunConfig();
  const model = (document.querySelector('.model-btn.active') || {}).dataset?.model || undefined;
  const body = { parameters: params, run_config };
  if (model) body.model = model;
  const res = await fetch(`/scenarios/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error((await res.json()).error || 'Update failed');
  return res.json();
}

async function deleteScenario(id) {
  const res = await fetch(`/scenarios/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Delete failed');
  if (window._activeScenarioId === id) window._activeScenarioId = null;
  await loadScenarios();
}

function renderScenarioList(scenarios) {
  const el = document.getElementById('scenario-list');
  if (!el) return;
  if (scenarios.length === 0) {
    el.innerHTML = '<p class="text-muted text-sm" style="padding:8px 0">No saved scenarios yet.</p>';
    return;
  }
  el.innerHTML = scenarios.map(s => `
    <div class="scenario-item" data-id="${s.id}" onclick="loadScenario('${s.id}')">
      <span class="s-name">${escHtml(s.name)}</span>
      <span class="s-model ${s.model}">${s.model}</span>
      <button class="del-btn" title="Delete" onclick="event.stopPropagation(); deleteScenario('${s.id}')">&times;</button>
    </div>`).join('');
}

function applyScenarioToForm(scenario) {
  const p = scenario.parameters || {};
  const rc = scenario.run_config || {};

  setSlider('carbon_tax',        p.carbon_tax        ?? 30);
  setSlider('base_energy_cost',  p.base_energy_cost  ?? 50);
  setSlider('renewable_share',   p.renewable_share   ?? 0.3);
  setSlider('tax_rate',          p.tax_rate          ?? 0.25);
  setSlider('population_growth', p.population_growth ?? 0.02);

  setSlider('tolerance',     rc.tolerance     ?? 0.5);
  setInput('max_iterations', rc.max_iterations ?? 20);

  const model = scenario.model || 'clews';
  document.querySelectorAll('.model-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.model === model);
  });

  const dir = rc.coupling_direction || 'clews_to_og';
  document.querySelectorAll('.dir-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.dir === dir);
  });
}

function readParameterInputs() {
  return {
    carbon_tax:        parseFloat(getInputVal('carbon_tax'))        || 30,
    base_energy_cost:  parseFloat(getInputVal('base_energy_cost'))  || 50,
    renewable_share:   parseFloat(getInputVal('renewable_share'))   || 0.3,
    tax_rate:          parseFloat(getInputVal('tax_rate'))          || 0.25,
    population_growth: parseFloat(getInputVal('population_growth')) || 0.02,
  };
}

function readRunConfig() {
  const activeDir = document.querySelector('.dir-btn.active');
  return {
    tolerance:         parseFloat(getInputVal('tolerance'))     || 0.5,
    max_iterations:    parseInt(getInputVal('max_iterations'))  || 20,
    coupling_direction: activeDir ? activeDir.dataset.dir : 'clews_to_og',
  };
}

function populateCompareDropdowns(_scenarios) {
}

function setSlider(name, value) {
  const range = document.querySelector(`input[type="range"][data-param="${name}"]`);
  const num   = document.querySelector(`input[type="number"][data-param="${name}"]`);
  if (range) { range.value = value; range.dispatchEvent(new Event('input')); }
  if (num)   num.value = value;
}

function setInput(name, value) {
  const el = document.querySelector(`[data-param="${name}"]`);
  if (el) el.value = value;
}

function getInputVal(name) {
  const el = document.querySelector(`[data-param="${name}"]`);
  return el ? el.value : null;
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
