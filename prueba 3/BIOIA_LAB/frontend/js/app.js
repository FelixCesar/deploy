// ✅ Rutas relativas - funciona en cualquier dominio
const API_BASE = "";

// Referencias base
const loginScreen = document.getElementById('login-screen');
const dashboard   = document.getElementById('dashboard');
const loginForm   = document.getElementById('login-form');

// 🔐 LOGIN
loginForm.addEventListener('submit', e => {
  e.preventDefault();
  const u = document.getElementById('username').value;
  const p = document.getElementById('password').value;

  if (u === 'admin' && p === '1234') {
    document.getElementById('login-screen').style.display = 'none';
    document.getElementById('dashboard').style.display = 'flex';
    console.log("✅ Sesión iniciada correctamente");
  } else {
    alert('Acceso denegado ❌');
  }
});

// 🚪 LOGOUT
document.getElementById('logout').addEventListener('click', () => {
  console.log("🚪 Cerrando sesión...");
  dashboard.style.display = 'none';
  loginScreen.style.display = 'flex';
  document.getElementById('username').value = 'admin';
  document.getElementById('password').value = '1234';
  const statusEl = document.getElementById('status');
  if (statusEl) statusEl.textContent = "Listo";
  alert("Sesión cerrada exitosamente 🌱");
});

// 🧭 MENU SECCIONES
const menuButtons = document.querySelectorAll('.menu-item');
const sections    = document.querySelectorAll('.section');
menuButtons.forEach(btn=>{
  btn.addEventListener('click', ()=>{
    menuButtons.forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    sections.forEach(s=>s.classList.add('hidden'));
    document.getElementById(btn.dataset.section).classList.remove('hidden');
  });
});

// FORMULARIO / REFERENCIAS
const form      = document.getElementById('sim-form');
const statusEl  = document.getElementById('status');

// Animación
const simCard   = document.getElementById('sim-anim');
const animResult= document.getElementById('anim-result');
const animOutput= document.getElementById('anim-output');
const bar       = document.getElementById('bar');
const eta       = document.getElementById('eta');
const aura      = document.getElementById('aura');
document.getElementById('btn-anim-new').addEventListener('click', ()=>{
  animResult.classList.add('hidden');
  simCard.classList.remove('hidden');
  resetAnim();
});

// Panel
const panelOutput = document.getElementById('panel-output');
const chartsBox   = document.getElementById('charts');

// Historial
const logBox      = document.getElementById('log');
document.getElementById('btn-refresh-log').addEventListener('click', cargarHistorial);

// 🧪 Envío de simulación
form.addEventListener('submit', async e => {
  e.preventDefault();
  statusEl.textContent = "Conectando con backend…";
  startAnim();

  const crew   = parseInt(document.getElementById('crew').value);
  const days   = parseInt(document.getElementById('days').value);
  const perfil = document.getElementById('perfil').value;
  const bioai  = document.getElementById('bioai').value;

  const data = await calcularEnBackend({crew, days, perfil, bioai});

  if (!data) {
    statusEl.textContent = "❌ No se recibieron datos";
    eta.textContent = "Error al conectar con el backend.";
    stopAnim(false);
    return;
  }

  const resumen = `
Tripulantes: ${crew}
Días: ${days}
Perfil: ${perfil}
BioAI: ${bioai}

Energía: ${(data.energia?.total_kw ?? 0).toFixed(2)} kW
Bacterias: ${(data.bacterias?.total_millones ?? 0).toFixed(2)} M
CO₂: ${(data.gases?.CO2 ?? 0).toFixed(2)} kg
CH₄: ${(data.gases?.CH4 ?? 0).toFixed(2)} kg
Nanobots activos: ${(data.nanobots?.activos ?? 0)}
  `.trim();

  await runProgress(36000);
  animOutput.textContent = resumen;
  stopAnim(true); 
  await cargarHistorial();

  panelOutput.innerHTML = `
<strong>👩‍🚀 Tripulantes:</strong> ${crew} — <strong>🕐 Días:</strong> ${days}<br>
<strong>🧫 Perfil:</strong> ${perfil} — <strong>🤖 BioAI:</strong> ${bioai}<br><br>
<strong>🔋 Energía:</strong> ${(data.energia?.total_kw ?? 0).toFixed(2)} kW<br>
<strong>🧬 Bacterias:</strong> ${(data.bacterias?.total_millones ?? 0).toFixed(2)} M<br>
<strong>💨 CO₂:</strong> ${(data.gases?.CO2 ?? 0).toFixed(2)} kg — <strong>CH₄:</strong> ${(data.gases?.CH4 ?? 0).toFixed(2)} kg<br>
<strong>⚙️ Nanobots:</strong> ${(data.nanobots?.activos ?? 0)}
  `;
  chartsBox.innerHTML = `
    ${renderChart("Energía", data.visual?.energia_pct)}
    ${renderChart("Bacterias", data.visual?.bacterias_pct)}
    ${renderChart("CO₂", data.visual?.co2_pct)}
    ${renderChart("CH₄", data.visual?.ch4_pct)}
    ${renderChart("Nanobots", data.visual?.nanobots_pct)}
  `;

  await cargarHistorial();
  statusEl.textContent = "Listo ✔️";
});

// 🧠 BACKEND
async function calcularEnBackend(payload){
  try{
    const res = await fetch(`/api/calcular`,{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify(payload)
    });
    if(!res.ok) throw new Error("Respuesta no OK");
    return await res.json();
  }catch(err){
    console.error("❌ Backend error:",err);
    return null;
  }
}

// 📜 HISTORIAL
async function cargarHistorial() {
  try {
    const res = await fetch(`/api/historial`);
    if (!res.ok) throw new Error("No OK");
    const data = await res.json();

    if (!Array.isArray(data) || !data.length) {
      logBox.innerHTML = `<div class="item empty">🌱 Aún no hay simulaciones guardadas.</div>`;
      return;
    }

    const table = `
      <div class="table-container">
        <table class="historial-table">
          <thead>
            <tr>
              <th>Fecha</th><th>Trip.</th><th>Días</th><th>Perfil</th><th>BioAI</th>
              <th>⚡ Energía (kW)</th><th>🧬 Bacterias (M)</th><th>💨 CO₂ (kg)</th><th>CH₄ (kg)</th><th>⚙️ Nanobots</th>
            </tr>
          </thead>
          <tbody>
            ${data.reverse().map(item => `
              <tr>
                <td>${item.fecha ?? "-"}</td>
                <td>${item.tripulantes ?? "-"}</td>
                <td>${item.dias ?? "-"}</td>
                <td>${item.perfil ?? "-"}</td>
                <td>${item.bioAI ?? "-"}</td>
                <td>${(item.resultados?.energia?.total_kw ?? 0).toFixed(2)}</td>
                <td>${(item.resultados?.bacterias?.total_millones ?? 0).toFixed(2)}</td>
                <td>${(item.resultados?.gases?.CO2 ?? 0).toFixed(2)}</td>
                <td>${(item.resultados?.gases?.CH4 ?? 0).toFixed(2)}</td>
                <td>${item.resultados?.nanobots?.activos ?? 0}</td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>`;
    logBox.innerHTML = table;
  } catch (error) {
    console.error("❌ Error cargando historial:", error);
    logBox.innerHTML = `<div class="item error">⚠️ No se pudo cargar el historial.<br>Verifica que el backend esté activo.</div>`;
  }
}

// 🌿 ANIMACIÓN
function startAnim(){
  bar.style.width = '0%';
  eta.textContent = "Iniciando…";
  document.querySelectorAll('.stem,.leaf').forEach(el=>{
    el.style.animation = 'none'; el.offsetHeight; el.style.animation = '';
  });
  aura.style.animation = 'none';
  aura.style.opacity = '0';
  animResult.classList.add('hidden');
  simCard.classList.remove('hidden');
}
function resetAnim(){
  bar.style.width='0%';
  eta.textContent='Esperando simulación…';
  aura.style.animation='none';
  aura.style.opacity='0';
}
function stopAnim(success){
  if(success){
    aura.style.animation='auraGlow 3s infinite';
    aura.style.opacity='1';
    simCard.classList.add('hidden');
    animResult.classList.remove('hidden');
  }else{
    eta.textContent='Error en la simulación.';
  }
}
function runProgress(totalMs){
  return new Promise(resolve=>{
    let elapsed=0; const step=100;
    const t=setInterval(()=>{
      elapsed += step;
      const p = Math.min(1, elapsed/totalMs);
      bar.style.width = `${(p*100).toFixed(1)}%`;
      if(p<0.5) bar.style.background="linear-gradient(90deg,#22c55e,#a3e635)";
      else if(p<0.8) bar.style.background="linear-gradient(90deg,#facc15,#f59e0b)";
      else bar.style.background="linear-gradient(90deg,#ef4444,#dc2626)";
      const left = ((totalMs - elapsed)/1000).toFixed(1);
      eta.textContent = `🌿 ${(p*100).toFixed(0)}% — quedan ${Math.max(0,left)}s`;
      if(p>=1){ clearInterval(t); resolve(); }
    }, step);
  });
}

// 📊 GRAFICOS
function renderChart(label, val){
  val = Math.max(0, Math.min(100, Number(val||0)));
  return `
    <div class="chart" data-label="${label}" data-value="${val}">
      <svg viewBox="0 0 36 36" class="circular-chart">
        <path class="circle-bg" d="M18 2.0845 a15.9155 15.9155 0 0 1 0 31.831 a15.9155 15.9155 0 0 1 0 -31.831"/>
        <path class="circle" stroke-dasharray="${val},100" d="M18 2.0845 a15.9155 15.9155 0 0 1 0 31.831 a15.9155 15.9155 0 0 1 0 -31.831"/>
        <text x="18" y="20.35" class="percentage">${val}%</text>
      </svg>
      <p>${label}</p>
    </div>
  `;
}

// Inicializar historial
cargarHistorial();
