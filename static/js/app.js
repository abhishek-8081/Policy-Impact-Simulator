function initTheme() {
  const stored = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', stored);
  const btn = document.getElementById('theme-toggle');
  if (btn) btn.textContent = stored === 'dark' ? 'Light' : 'Dark';
}
function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  const btn = document.getElementById('theme-toggle');
  if (btn) btn.textContent = next === 'dark' ? 'Light' : 'Dark';
  redrawVisibleCharts();
}

function redrawVisibleCharts() {
  const ids = ['chart-clews','chart-og','chart-convergence','chart-emissions','chart-delta','chart-sweep','chart-compare'];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el && el._fullLayout) {
      const LB = layoutBase();
      Plotly.relayout(el, {
        'font.color':    LB.font.color,
        'paper_bgcolor': LB.paper_bgcolor,
        'plot_bgcolor':  LB.plot_bgcolor,
        'xaxis.gridcolor':  LB.xaxis.gridcolor,
        'xaxis.linecolor':  LB.xaxis.linecolor,
        'xaxis.tickfont.color': LB.xaxis.tickfont.color,
        'yaxis.gridcolor':  LB.yaxis.gridcolor,
        'yaxis.linecolor':  LB.yaxis.linecolor,
        'yaxis.tickfont.color': LB.yaxis.tickfont.color,
        'legend.font.color': LB.legend.font.color,
        'title.font.color':  LB.title.font.color,
      });
    }
  });
}

function checkMobile() {
  if (window.innerWidth < 1024) {
    const el = document.getElementById('mobile-warning');
    if (el) el.classList.remove('hidden');
  }
}

function switchTab(tabName) {
  document.querySelectorAll('.tab-btn').forEach(btn =>
    btn.classList.toggle('active', btn.dataset.tab === tabName));
  document.querySelectorAll('.tab-panel').forEach(panel =>
    panel.classList.toggle('active', panel.id === `tab-${tabName}`));
  if (tabName === 'results') fetchResults();
}

function initSliders() {
  document.querySelectorAll('input[type="range"][data-param]').forEach(range => {
    const num = document.querySelector(`input[type="number"][data-param="${range.dataset.param}"]`);
    const lbl = document.querySelector(`[data-val="${range.dataset.param}"]`);
    function sync(src) {
      const v = parseFloat(src.value);
      if (range !== src) range.value = v;
      if (num && num !== src) num.value = v;
      if (lbl) lbl.textContent = v;
    }
    range.addEventListener('input', () => { sync(range); updateDirectionPreviews(); });
    if (num) num.addEventListener('input', () => { sync(num); updateDirectionPreviews(); });
    if (lbl) lbl.textContent = range.value;
  });
}

function initModelSelector() {
  document.querySelectorAll('.model-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.model-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });
}
function getActiveModel() {
  const btn = document.querySelector('.model-btn.active');
  return btn ? btn.dataset.model : 'clews';
}

function initDirectionToggle() {
  document.querySelectorAll('.dir-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.dir-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      updateFlowDiagram('idle', btn.dataset.dir);
      clearValidationBadges();
      setStepState(1, ''); setStepState(2, ''); setStepState(3, '');
    });
  });
}
function getActiveDirection() {
  const btn = document.querySelector('.dir-btn.active');
  return btn ? btn.dataset.dir : 'clews_to_og';
}

function showSpinner(id) { document.getElementById(id)?.classList.add('visible'); }
function hideSpinner(id) { document.getElementById(id)?.classList.remove('visible'); }

function showMsg(id, text, type = 'error') {
  const el = document.getElementById(id);
  if (el) el.innerHTML = `<div class="msg msg-${type}">${escHtml(text)}</div>`;
}
function clearMsg(id) { const el = document.getElementById(id); if (el) el.innerHTML = ''; }

function showWarnings(warnings, containerId) {
  const el = document.getElementById(containerId);
  if (!el || !warnings || !warnings.length) return;
  el.innerHTML = warnings.map(w =>
    `<div class="msg msg-warn">${escHtml(w)}</div>`).join('');
}

async function loadPresets() {
  try {
    const res = await fetch('/presets');
    const presets = await res.json();
    renderPresetButtons(presets);
  } catch (e) {
    console.error('Failed to load presets', e);
  }
}

function renderPresetButtons(presets) {
  const container = document.getElementById('preset-buttons');
  if (!container) return;
  container.innerHTML = presets.map(p => `
    <button class="preset-btn" data-id="${p.id}" title="${escHtml(p.description)}"
            onclick="applyPreset('${p.id}')">
      ${p.flag} ${p.name}
    </button>`).join('') +
    `<button class="preset-btn preset-custom active" onclick="clearPreset()">Custom</button>`;
}

async function applyPreset(id) {
  try {
    const res = await fetch(`/presets/${id}`);
    const preset = await res.json();
    const p = preset.parameters;
    setSlider('carbon_tax',        p.carbon_tax);
    setSlider('base_energy_cost',  p.base_energy_cost);
    setSlider('renewable_share',   p.renewable_share);
    setSlider('tax_rate',          p.tax_rate);
    setSlider('population_growth', p.population_growth);
    document.querySelectorAll('.preset-btn').forEach(btn =>
      btn.classList.toggle('active', btn.dataset.id === id));
    showMsg('preset-msg', `${preset.flag} ${preset.name}: ${preset.description}`, 'info');
    setTimeout(() => clearMsg('preset-msg'), 5000);
  } catch (e) {
    showMsg('preset-msg', 'Failed to load preset: ' + e.message);
  }
}

function clearPreset() {
  document.querySelectorAll('.preset-btn').forEach(btn =>
    btn.classList.toggle('active', btn.classList.contains('preset-custom')));
}

const IMPACT_RULES = {
  carbon_tax:        { energy_cost: 1, emissions: -1, gdp: -1, wages: -1 },
  base_energy_cost:  { energy_cost: 1, gdp: -1, wages: -1 },
  renewable_share:   { energy_cost: -1, emissions: -1, energy_investment: 1 },
  tax_rate:          { gdp: -1, wages: -1, govt_revenue: 1, savings: -1 },
  population_growth: { gdp: 1, labor: 1 },
};

function updateDirectionPreviews() {
  document.querySelectorAll('.impact-arrow').forEach(el => {
    el.textContent = ''; el.className = 'impact-arrow';
  });
  const params = readParameterInputs();
  const defaults = { carbon_tax: 30, base_energy_cost: 50, renewable_share: 0.3, tax_rate: 0.25, population_growth: 0.02 };
  Object.entries(IMPACT_RULES).forEach(([param, impacts]) => {
    const delta = (params[param] || 0) - (defaults[param] || 0);
    if (Math.abs(delta) < 1e-9) return;
    const dir = delta > 0 ? 1 : -1;
    Object.entries(impacts).forEach(([output, sign]) => {
      const el = document.querySelector(`.impact-arrow[data-output="${output}"]`);
      if (!el) return;
      const netDir = dir * sign;
      el.textContent = netDir > 0 ? '+' : '-';
      el.className = `impact-arrow ${netDir > 0 ? 'up' : 'down'}`;
    });
  });
}

async function handleCreateScenario() {
  const name  = document.getElementById('scenario-name').value.trim() || 'New Scenario';
  const model = getActiveModel();
  try {
    const scenario = await createScenario(name, model);
    document.getElementById('scenario-name').value = '';
    await loadScenarios();
    await loadScenario(scenario.id);
    clearMsg('scenario-msg');
  } catch (e) { showMsg('scenario-msg', e.message); }
}

async function handleSaveScenario() {
  if (!window._activeScenarioId) { showMsg('scenario-msg', 'No scenario selected.'); return; }
  try {
    await updateScenario(window._activeScenarioId);
    showMsg('scenario-msg', 'Scenario saved.', 'ok');
    setTimeout(() => clearMsg('scenario-msg'), 2000);
  } catch (e) { showMsg('scenario-msg', e.message); }
}

async function handleRunModel() {
  if (!window._activeScenarioId) { showMsg('run-msg', 'Select or create a scenario first.'); return; }
  try {
    await fetch(`/scenarios/${window._activeScenarioId}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: getActiveModel(), parameters: readParameterInputs(), run_config: readRunConfig() }),
    });
  } catch (_) {}

  clearMsg('run-msg');
  clearMsg('warnings-msg');
  showSpinner('spinner-run');
  document.getElementById('btn-run-model').disabled = true;

  try {
    const res  = await fetch(`/run/${window._activeScenarioId}`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) { showMsg('run-msg', data.error || 'Run failed.'); return; }
    if (data.warnings?.length) showWarnings(data.warnings, 'warnings-msg');
    displayModelResults(data.results, data.metadata);
  } catch (e) {
    showMsg('run-msg', 'Network error: ' + e.message);
  } finally {
    hideSpinner('spinner-run');
    document.getElementById('btn-run-model').disabled = false;
  }
}

function displayModelResults(results, metadata) {
  const area = document.getElementById('model-results');
  if (!area) return;
  area.innerHTML = '';

  const clews = results.clews;
  const og    = results.og;
  const prev  = window._lastResults || {};

  if (clews) {
    area.innerHTML += buildResultCards(clews, 'CLEWS Output', {
      energy_cost: ['Energy Cost','$/MWh'], emissions: ['Emissions','MtCO2'],
      energy_investment: ['Investment','$B'], energy_consumption: ['Consumption','TWh'],
    }, prev.clews);
  }
  if (og) {
    area.innerHTML += buildResultCards(og, 'OG-Core Output', {
      gdp: ['GDP','$B'], wages: ['Wages','$/worker'], savings: ['Savings','$B'],
      capital: ['Capital','$B'], govt_revenue: ['Govt Revenue','$B'], productivity: ['Productivity','TFP'],
    }, prev.og);
  }

  area.innerHTML += `<p class="text-muted text-sm mt-8">Run ID: ${metadata.run_id} &nbsp;&middot;&nbsp; ${metadata.duration_seconds}s</p>`;

  window._lastResults = results;
  if (clews) renderClewsChart(clews);
  if (og)    renderOgChart(og);
}

function buildResultCards(data, title, labelMap, prevData) {
  const cards = Object.entries(labelMap).map(([k, [label, unit]]) => {
    const val  = data[k] != null ? data[k] : null;
    const prev = prevData?.[k];
    let deltaHtml = '';
    if (prev != null && val != null && prev !== 0) {
      const pct   = ((val - prev) / Math.abs(prev) * 100).toFixed(1);
      const isUp  = val > prev;
      deltaHtml = `<div class="r-delta ${isUp ? 'up' : 'down'}">${isUp ? '+' : '-'}${Math.abs(pct)}%</div>`;
    }
    return `
    <div class="result-card">
      <div class="r-label">${label}</div>
      <div class="r-value">${val != null ? val.toLocaleString() : '—'}</div>
      <div class="r-unit">${unit}</div>
      ${deltaHtml}
    </div>`;
  }).join('');
  return `<div class="section-title mt-12">${title}</div><div class="result-grid">${cards}</div>`;
}

async function handleRunCoupled() {
  if (!window._activeScenarioId) { showMsg('coupled-msg', 'Select a scenario first.'); return; }
  const direction = getActiveDirection();
  try {
    await fetch(`/scenarios/${window._activeScenarioId}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'coupled', parameters: readParameterInputs(),
        run_config: { ...readRunConfig(), coupling_direction: direction } }),
    });
  } catch (_) {}

  clearMsg('coupled-msg');
  showSpinner('spinner-coupled');
  document.getElementById('btn-run-coupled').disabled = true;
  setStepState(1, 'running'); setStepState(2, 'idle'); setStepState(3, 'idle');
  clearValidationBadges();
  updateFlowDiagram('running', direction);

  try {
    const res  = await fetch(`/run/${window._activeScenarioId}`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) {
      showMsg('coupled-msg', data.error || 'Coupled run failed.');
      setStepState(1, 'error');
      updateFlowDiagram('error', direction);
      return;
    }
    setStepState(1, 'done'); setStepState(2, 'done'); setStepState(3, 'done');
    setValidationBadge('val-clews',    'ok', 'CLEWS valid');
    setValidationBadge('val-exchange', 'ok', 'Exchange valid');
    setValidationBadge('val-og',       'ok', 'OG-Core valid');
    const timing = data.results?.timing || data.metadata?.timing || {};
    displayCoupledResults(data.results, direction);
    updateFlowDiagram('done', direction, timing);
  } catch (e) {
    showMsg('coupled-msg', 'Network error: ' + e.message);
    setStepState(1, 'error');
  } finally {
    hideSpinner('spinner-coupled');
    document.getElementById('btn-run-coupled').disabled = false;
  }
}

function setStepState(step, state) {
  const el = document.getElementById(`step-${step}`);
  if (el) el.className = `pipeline-step ${state}`;
}

function clearValidationBadges() {
  ['val-clews','val-exchange','val-og'].forEach(id => setValidationBadge(id, 'idle', 'Waiting'));
}

function setValidationBadge(id, type, text) {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = `val-badge ${type}`;
  el.textContent = text;
}

function updateFlowDiagram(state, direction, timing) {
  const diag = document.getElementById('flow-diagram');
  if (!diag) return;
  const isCtO = direction !== 'og_to_clews';
  const aLabel = isCtO ? 'CLEWS' : 'OG-Core';
  const bLabel = isCtO ? 'OG-Core' : 'CLEWS';
  const arrow  = isCtO ? 'energy_cost, emissions' : 'gdp_factor';
  const t      = timing || {};
  const aMs    = isCtO ? t.clews_ms : t.og_ms;
  const bMs    = isCtO ? t.og_ms    : t.clews_ms;

  const stateA = state === 'done' ? 'done' : state === 'error' ? 'error' : state === 'running' ? 'running' : '';

  diag.innerHTML = `
    <div class="flow-box ${stateA}">
      <div class="flow-label">${aLabel}</div>
      ${aMs != null ? `<div class="flow-timing">${aMs}ms</div>` : ''}
    </div>
    <div class="flow-arrow">
      <div class="flow-arrow-label">${arrow}</div>
      <div>------&gt;</div>
    </div>
    <div class="flow-box ${state === 'done' ? 'done' : ''}">
      <div class="flow-label">Mapping</div>
      ${t.mapping_ms != null ? `<div class="flow-timing">${t.mapping_ms}ms</div>` : ''}
    </div>
    <div class="flow-arrow">
      <div class="flow-arrow-label">mapped inputs</div>
      <div>------&gt;</div>
    </div>
    <div class="flow-box ${state === 'done' ? 'done' : ''}">
      <div class="flow-label">${bLabel}</div>
      ${bMs != null ? `<div class="flow-timing">${bMs}ms</div>` : ''}
    </div>`;
}

function displayCoupledResults(results, direction) {
  const isCtO = direction === 'clews_to_og';
  const modelA = isCtO ? results.clews : results.og;
  const modelB = isCtO ? results.og    : results.clews;
  const labelsClews = { energy_cost:'Energy Cost', emissions:'Emissions', energy_investment:'Investment', energy_consumption:'Consumption' };
  const labelsOg    = { gdp:'GDP', wages:'Wages', savings:'Savings', capital:'Capital', govt_revenue:'Govt Revenue' };

  const wrapLabels = obj => Object.fromEntries(Object.entries(obj).map(([k,v])=>[k,[v,'—']]));

  document.getElementById('coupled-model-a').innerHTML =
    buildResultCards(modelA || {}, isCtO ? 'CLEWS Output' : 'OG-Core Output',
      wrapLabels(isCtO ? labelsClews : labelsOg));

  const exchKeys = Object.fromEntries(Object.keys(results.exchange||{}).map(k=>[k,[k,'—']]));
  document.getElementById('coupled-exchange').innerHTML =
    buildResultCards(results.exchange||{}, 'Exchange Data', exchKeys);

  document.getElementById('coupled-model-b').innerHTML =
    buildResultCards(modelB || {}, isCtO ? 'OG-Core Output' : 'CLEWS Output',
      wrapLabels(isCtO ? labelsOg : labelsClews));
}

async function handleRunConverging() {
  if (!window._activeScenarioId) { showMsg('conv-msg', 'Select a scenario first.'); return; }
  try {
    await fetch(`/scenarios/${window._activeScenarioId}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'converging', parameters: readParameterInputs(), run_config: readRunConfig() }),
    });
  } catch (_) {}

  clearMsg('conv-msg');
  showSpinner('spinner-conv');
  document.getElementById('btn-run-conv').disabled = true;
  const badge = document.getElementById('conv-status-badge');
  badge.className = 'conv-status idle'; badge.textContent = 'Running...';

  try {
    const res  = await fetch(`/run/${window._activeScenarioId}`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) { showMsg('conv-msg', data.error || 'Converging run failed.'); return; }

    const r     = data.results;
    const tMs   = r.timing?.total_ms;
    const tStr  = tMs != null ? ` (${tMs}ms)` : '';

    if (r.converged) {
      badge.className = 'conv-status converged';
      badge.textContent = `Converged after ${r.iterations} iteration${r.iterations===1?'':'s'}${tStr}`;
    } else {
      badge.className = 'conv-status not-converged';
      badge.textContent = `Did not converge within ${r.iterations} iterations${tStr}`;
    }

    const tol = parseFloat(getInputVal('tolerance') || 0.5);
    renderConvergenceChart(r.history, tol);
    renderEmissionsChart(r.history);
    renderDeltaChart(r.history, tol);
    renderIterationTable(r.history, tol);
    document.getElementById('iter-table-wrap')?.classList.remove('hidden');
  } catch (e) {
    showMsg('conv-msg', 'Network error: ' + e.message);
  } finally {
    hideSpinner('spinner-conv');
    document.getElementById('btn-run-conv').disabled = false;
  }
}

function renderIterationTable(history, tol) {
  const tbody = document.getElementById('iter-tbody');
  if (!tbody || !history) return;
  tbody.innerHTML = history.map(h => {
    const convergedRow = h.delta_gdp !== null && h.delta_gdp < tol;
    return `<tr${convergedRow ? ' class="converged-row"' : ''}>
      <td>${h.iteration}</td>
      <td>${h.gdp.toLocaleString()}</td>
      <td>${h.energy_cost}</td>
      <td>${h.emissions}</td>
      <td>${h.delta_gdp !== null ? h.delta_gdp : '—'}</td>
    </tr>`;
  }).join('');
}

async function fetchResults() {
  try {
    const res  = await fetch('/results');
    const runs = await res.json();
    renderRunList(runs);
    populateRunDropdowns(runs);
  } catch (e) { showMsg('results-msg', 'Could not load results: ' + e.message); }
}

function renderRunList(runs) {
  const el = document.getElementById('run-list');
  if (!el) return;
  if (!runs.length) { el.innerHTML = '<p class="text-muted text-sm">No runs yet.</p>'; return; }
  el.innerHTML = runs.map(r => `
    <div class="run-item" onclick="expandRun('${r.run_id}')">
      <div>
        <div class="run-name">${escHtml(r.scenario_name || r.run_id)}</div>
        <div class="run-meta">${r.timestamp?.slice(0,19).replace('T',' ')||''} · ${r.duration_seconds}s</div>
      </div>
      <span class="run-mode">${r.model||''}</span>
      <span class="run-meta ${r.status==='error'?'text-error':''}">${r.status||''}</span>
      <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); exportRun('${r.run_id}')">CSV</button>
    </div>
    <div id="run-detail-${r.run_id}" class="hidden run-detail"></div>`).join('');
}

async function expandRun(runId) {
  const detail = document.getElementById(`run-detail-${runId}`);
  if (!detail) return;
  if (!detail.classList.contains('hidden')) { detail.classList.add('hidden'); return; }
  try {
    const res  = await fetch(`/results/${runId}`);
    const data = await res.json();
    detail.textContent = JSON.stringify(data, null, 2);
    detail.classList.remove('hidden');
  } catch (e) {
    detail.textContent = 'Failed to load: ' + e.message;
    detail.classList.remove('hidden');
  }
}

function populateRunDropdowns(runs) {
  ['compare-a','compare-b'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = '<option value="">— select run —</option>' +
      runs.map(r => `<option value="${r.run_id}">${escHtml(r.scenario_name||r.run_id)} (${r.model||''})</option>`).join('');
  });
}

async function handleCompare() {
  const a = document.getElementById('compare-a').value;
  const b = document.getElementById('compare-b').value;
  if (!a || !b) { showMsg('compare-msg', 'Select two runs.'); return; }
  if (a === b)  { showMsg('compare-msg', 'Select two different runs.'); return; }
  clearMsg('compare-msg');
  try {
    const res  = await fetch(`/results/${a}/compare/${b}`);
    const data = await res.json();
    if (!res.ok) { showMsg('compare-msg', data.error || 'Compare failed'); return; }
    renderComparisonChart(data.run_a, data.run_b);
    renderComparisonTable(data.run_a, data.run_b);
    document.getElementById('compare-area').classList.remove('hidden');
  } catch (e) { showMsg('compare-msg', 'Network error: ' + e.message); }
}

function renderComparisonTable(runA, runB) {
  const el = document.getElementById('compare-table');
  if (!el) return;
  const aOut = { ...(runA.clews_output||{}), ...(runA.og_output||{}) };
  const bOut = { ...(runB.clews_output||{}), ...(runB.og_output||{}) };
  const keys = [...new Set([...Object.keys(aOut), ...Object.keys(bOut)])].filter(k => typeof (aOut[k]??bOut[k]) === 'number');
  const nameA = runA.metadata?.scenario_name || 'Run A';
  const nameB = runB.metadata?.scenario_name || 'Run B';

  el.innerHTML = `<table class="iter-table">
    <thead><tr><th>Metric</th><th>${escHtml(nameA)}</th><th>${escHtml(nameB)}</th><th>Change</th></tr></thead>
    <tbody>${keys.map(k => {
      const a = aOut[k], b = bOut[k];
      const pct = (a != null && b != null && a !== 0)
        ? ((b - a) / Math.abs(a) * 100).toFixed(1) : '—';
      const cls = pct !== '—' ? (parseFloat(pct) > 0 ? 'up' : 'down') : '';
      return `<tr><td>${k}</td><td>${a??'—'}</td><td>${b??'—'}</td>
        <td class="${cls}">${pct !== '—' ? (parseFloat(pct)>0?'+ ':' ')+pct+'%' : '—'}</td></tr>`;
    }).join('')}</tbody></table>`;
}

async function exportRun(runId) {
  window.location.href = `/results/${runId}/export/csv`;
}

async function handleSensitivity() {
  clearMsg('sensitivity-msg');
  showSpinner('spinner-sensitivity');
  try {
    const res  = await fetch('/sensitivity', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ parameters: readParameterInputs() }),
    });
    const data = await res.json();
    renderSensitivityTable(data.sensitivity);
  } catch (e) {
    showMsg('sensitivity-msg', 'Sensitivity error: ' + e.message);
  } finally {
    hideSpinner('spinner-sensitivity');
  }
}

function renderSensitivityTable(sensitivity) {
  const el = document.getElementById('sensitivity-results');
  if (!el || !sensitivity) return;
  const rows = Object.entries(sensitivity).map(([out, s]) => {
    const e = s.elasticity;
    const cls = e > 0 ? 'up' : 'down';
    return `<tr>
      <td>${out}</td>
      <td><strong>${s.most_sensitive_to}</strong></td>
      <td class="${cls}">${e > 0 ? '+' : '-'} ${Math.abs(e).toFixed(3)}</td>
    </tr>`;
  }).join('');
  el.innerHTML = `<table class="iter-table">
    <thead><tr><th>Output</th><th>Most sensitive to</th><th>Elasticity</th></tr></thead>
    <tbody>${rows}</tbody></table>`;
}

async function handleSweep() {
  const sweepParam = document.getElementById('sweep-param').value || 'carbon_tax';
  const model      = document.getElementById('sweep-model').value || 'clews';
  clearMsg('sweep-msg');
  showSpinner('spinner-sweep');
  try {
    const res  = await fetch('/sweep', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ parameters: readParameterInputs(), sweep_param: sweepParam, min:0, max:100, steps:25, model }),
    });
    renderSweepChart(await res.json(), 'chart-sweep');
  } catch (e) { showMsg('sweep-msg', 'Sweep error: ' + e.message); }
  finally { hideSpinner('spinner-sweep'); }
}

function showArchModal() {
  document.getElementById('arch-modal').classList.remove('hidden');
}
function closeArchModal() {
  document.getElementById('arch-modal').classList.add('hidden');
}
function showFeaturesModal() {
  document.getElementById('features-modal').classList.remove('hidden');
}
function closeFeaturesModal() {
  document.getElementById('features-modal').classList.add('hidden');
}

window._activeScenarioId = null;
window._lastResults      = null;

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  checkMobile();
  initSliders();
  initModelSelector();
  initDirectionToggle();
  loadPresets();
  loadScenarios();
  clearValidationBadges();
  updateFlowDiagram('idle', 'clews_to_og');
});
