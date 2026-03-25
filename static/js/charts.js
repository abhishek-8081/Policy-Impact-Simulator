const PALETTES = {
  light: {
    teal:'#92400e', teal2:'#b45309', slate:'#6b3a1f', slate2:'#7a706a',
    amber:'#c2410c', rose:'#a16207', indigo:'#854d0e', green:'#16a34a',
  },
  dark: {
    teal:'#c2956a', teal2:'#d97706', slate:'#a39890', slate2:'#7a706a',
    amber:'#e07a5f', rose:'#dda15e', indigo:'#bc6c25', green:'#22c55e',
  },
};

function P() {
  return document.documentElement.getAttribute('data-theme') === 'dark'
    ? PALETTES.dark : PALETTES.light;
}

function layoutBase() {
  const dark  = document.documentElement.getAttribute('data-theme') === 'dark';
  const txt   = dark ? '#e3dad4' : '#1c1412';
  const muted = dark ? '#c2956a' : '#7a706a';
  return {
    font:         { family: 'IBM Plex Sans, system-ui, sans-serif', size: 12, color: txt },
    margin:       { l:52, r:24, t:36, b:52 },
    paper_bgcolor:'transparent',
    plot_bgcolor: '#f2eee9',
    xaxis: { gridcolor:'#e3dbd4', linecolor:'#e3dbd4', zeroline:false, tickfont:{ color:txt, size:11 }, titlefont:{ color:muted } },
    yaxis: { gridcolor:'#e3dbd4', linecolor:'#e3dbd4', zeroline:false, tickfont:{ color:txt, size:11 }, titlefont:{ color:muted } },
    legend: { font:{ color:txt, size:11 }, bgcolor:'transparent' },
    title:  { font:{ color:txt, size:13 } },
  };
}

const CFG = { displayModeBar:false, responsive:true };

function renderClewsChart(data, containerId='chart-clews') {
  const el = document.getElementById(containerId);
  if (!el) return;
  const keys   = ['energy_cost','emissions','energy_investment','energy_consumption'];
  const labels = ['Energy Cost','Emissions','Investment','Consumption'];
  const pal    = P();
  const LB     = layoutBase();
  const colors = [pal.teal, pal.rose, pal.indigo, pal.amber];
  Plotly.newPlot(el, [{
    type:'bar', x:labels, y:keys.map(k=>data[k]??0),
    marker:{ color:colors },
    text: keys.map(k=>(data[k]??0).toString()),
    textposition:'auto',
  }], {
    ...LB,
    title:{ text:'CLEWS Output', font:{size:13} },
    margin:{ ...LB.margin, t:48 },
    yaxis:{ ...LB.yaxis, automargin:true },
  }, CFG);
}

function renderOgChart(data, containerId='chart-og') {
  const el = document.getElementById(containerId);
  if (!el) return;
  const keys   = ['gdp','wages','savings','capital','govt_revenue'];
  const labels = ['GDP','Wages','Savings','Capital','Govt Revenue'];
  const pal    = P();
  const LB     = layoutBase();
  const colors = [pal.teal, pal.slate, pal.teal2, pal.indigo, pal.amber];
  Plotly.newPlot(el, [{
    type:'bar', x:labels, y:keys.map(k=>data[k]??0),
    marker:{ color:colors },
    text: keys.map(k=>(data[k]??0).toString()),
    textposition:'auto',
  }], {
    ...LB,
    title:{ text:'OG-Core Output', font:{size:13} },
    margin:{ ...LB.margin, t:48 },
    yaxis:{ ...LB.yaxis, automargin:true },
  }, CFG);
}

function renderConvergenceChart(history, tolerance, containerId='chart-convergence') {
  const el = document.getElementById(containerId);
  if (!el || !history?.length) return;
  const pal   = P();
  const LB    = layoutBase();
  const iters = history.map(h=>h.iteration);
  const gdps  = history.map(h=>h.gdp);

  const traces = [{
    type:'scatter', mode:'lines+markers', name:'GDP',
    x:iters, y:gdps,
    line:{ color:pal.teal, width:2.5 }, marker:{ color:pal.teal, size:7 },
  }];

  const convergedAt = history.findIndex(h => h.delta_gdp !== null && h.delta_gdp < (tolerance||0.5));
  if (convergedAt >= 0) {
    traces.push({
      type:'scatter', mode:'markers', name:'Converged',
      x:[history[convergedAt].iteration], y:[history[convergedAt].gdp],
      marker:{ color:pal.green, size:12, symbol:'star' },
    });
  }

  Plotly.newPlot(el, traces, {
    ...LB,
    title:{ text:'GDP Convergence', font:{size:13} },
    xaxis:{ ...LB.xaxis, title:'Iteration', dtick:1 },
    yaxis:{ ...LB.yaxis, title:'GDP' },
    legend:{ orientation:'h', y:-0.40, x:0.5, xanchor:'center' },
    margin:{ ...LB.margin, b:100 },
  }, CFG);
}

function renderEmissionsChart(history, containerId='chart-emissions') {
  const el = document.getElementById(containerId);
  if (!el || !history?.length) return;
  const pal   = P();
  const LB    = layoutBase();
  const iters = history.map(h=>h.iteration);
  Plotly.newPlot(el, [
    {
      type:'scatter', mode:'lines+markers', name:'Emissions',
      x:iters, y:history.map(h=>h.emissions),
      line:{ color:pal.rose, width:2 }, marker:{ color:pal.rose, size:5 },
    },
    {
      type:'scatter', mode:'lines+markers', name:'Energy Cost',
      x:iters, y:history.map(h=>h.energy_cost),
      line:{ color:pal.amber, width:2 }, marker:{ color:pal.amber, size:5 },
      yaxis:'y2',
    },
  ], {
    ...LB,
    title:{ text:'Emissions & Energy Cost', font:{size:13} },
    xaxis:{ ...LB.xaxis, title:'Iteration', dtick:1 },
    yaxis:{ ...LB.yaxis, title:'Emissions' },
    yaxis2:{ title:'Energy Cost', overlaying:'y', side:'right', gridcolor:'transparent', zeroline:false },
    legend:{ orientation:'h', y:-0.40, x:0.5, xanchor:'center' },
    margin:{ ...LB.margin, r:60, b:100 },
  }, CFG);
}

function renderDeltaChart(history, tolerance, containerId='chart-delta') {
  const el = document.getElementById(containerId);
  if (!el || !history?.length) return;
  const withDelta = history.filter(h => h.delta_gdp !== null);
  if (!withDelta.length) return;

  const pal = P();
  const LB  = layoutBase();
  const tol = tolerance || 0.5;
  Plotly.newPlot(el, [
    {
      type:'bar', name:'|GDP|',
      x: withDelta.map(h=>h.iteration),
      y: withDelta.map(h=>h.delta_gdp),
      marker:{ color: withDelta.map(h => h.delta_gdp < tol ? pal.green : pal.amber) },
    },
    {
      type:'scatter', mode:'lines', name:`Tolerance (${tol})`,
      x:[withDelta[0].iteration, withDelta[withDelta.length-1].iteration],
      y:[tol, tol],
      line:{ color:pal.rose, width:2, dash:'dash' },
    },
  ], {
    ...LB,
    title:{ text:'|GDP| per Iteration', font:{size:13} },
    xaxis:{ ...LB.xaxis, title:'Iteration', dtick:1 },
    yaxis:{ ...LB.yaxis, title:'|GDP|' },
    legend:{ orientation:'h', y:-0.40, x:0.5, xanchor:'center' },
    margin:{ ...LB.margin, b:100 },
  }, CFG);
}

function renderSweepChart(sweepData, containerId='chart-sweep') {
  const el = document.getElementById(containerId);
  if (!el || !sweepData?.results) return;
  const pal    = P();
  const LB     = layoutBase();
  const xs     = sweepData.results.map(r=>r.param_value);
  const keys   = Object.keys(sweepData.results[0]).filter(k=>k!=='param_value');
  const colors = [pal.teal, pal.rose, pal.amber, pal.indigo, pal.teal2, pal.slate];
  const traces = keys.map((k,i) => ({
    type:'scatter', mode:'lines', name:k,
    x:xs, y:sweepData.results.map(r=>r[k]),
    line:{ color:colors[i%colors.length], width:2 },
  }));
  Plotly.newPlot(el, traces, {
    ...LB,
    title:{ text:`Sweep: ${sweepData.sweep_param} (0 to 100)`, font:{size:13} },
    xaxis:{ ...LB.xaxis, title:'' },
    yaxis:{ ...LB.yaxis, title:'Output value' },
    legend:{ orientation:'h', y:-0.18, x:0 },
    margin:{ ...LB.margin, b:70 },
  }, CFG);
}

function renderComparisonChart(runA, runB, containerId='chart-compare') {
  const el = document.getElementById(containerId);
  if (!el) return;
  const pal  = P();
  const LB   = layoutBase();
  const aOut = { ...(runA.clews_output||{}), ...(runA.og_output||{}) };
  const bOut = { ...(runB.clews_output||{}), ...(runB.og_output||{}) };
  const keys = [...new Set([...Object.keys(aOut),...Object.keys(bOut)])]
    .filter(k=>typeof (aOut[k]??bOut[k])==='number');
  const nameA = runA.metadata?.scenario_name || 'Run A';
  const nameB = runB.metadata?.scenario_name || 'Run B';
  Plotly.newPlot(el, [
    { type:'bar', name:nameA, x:keys, y:keys.map(k=>aOut[k]??null), marker:{ color:pal.teal } },
    { type:'bar', name:nameB, x:keys, y:keys.map(k=>bOut[k]??null), marker:{ color:pal.amber } },
  ], {
    ...LB,
    barmode:'group',
    title:{ text:'Side-by-side Comparison', font:{size:13} },
    legend:{ orientation:'h', y:-0.22 },
  }, CFG);
}
