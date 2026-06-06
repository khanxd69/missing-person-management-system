async function loadCharts() {
  try {
    const res  = await fetch('/api/chart/monthly');
    const data = await res.json();
    const ctx  = document.getElementById('monthly-chart');
    if (ctx) new Chart(ctx, {type:'bar',data:{labels:data.map(d=>d.month),datasets:[{label:'Cases',data:data.map(d=>d.count),backgroundColor:'rgba(230,57,70,0.6)',borderColor:'#e63946',borderWidth:1,borderRadius:6}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#7d8590',font:{size:11}},grid:{color:'rgba(255,255,255,0.04)'}},y:{ticks:{color:'#7d8590',stepSize:1},grid:{color:'rgba(255,255,255,0.04)'},beginAtZero:true}}}});
    const stats = await (await fetch('/api/stats')).json();
    const donut = document.getElementById('donut-chart');
    if (donut) new Chart(donut, {type:'doughnut',data:{labels:['Missing','Located','Closed'],datasets:[{data:[stats.missing,stats.located,stats.closed||0],backgroundColor:['#e63946','#2a9d8f','#2d333b'],borderColor:'#161b22',borderWidth:3}]},options:{responsive:true,cutout:'65%',plugins:{legend:{position:'bottom',labels:{color:'#7d8590',font:{size:11},padding:16}}}}});
  } catch(e) { console.warn('Chart load failed', e); }
}
loadCharts();
