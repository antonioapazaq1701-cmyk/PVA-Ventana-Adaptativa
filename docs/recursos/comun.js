const porId = id => document.getElementById(id);
porId('tema').onclick = () => document.body.classList.toggle('claro');
porId('pantalla').onclick = async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await document.documentElement.requestFullscreen();
  } catch { porId('pantalla').textContent = 'No disponible'; }
};

const lienzo = document.createElement('canvas');
lienzo.id = 'lluvia-bits';
lienzo.setAttribute('aria-hidden', 'true');
document.body.prepend(lienzo);
const contexto = lienzo.getContext('2d');
const botonBits = document.createElement('button');
botonBits.id = 'bits';
document.querySelector('header nav').prepend(botonBits);
const reducirMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)');
let pausada = reducirMovimiento.matches;
let columnas = [];
let ultimoCuadro = 0;
let cuadro = 0;

function ajustarLluvia() {
  const escala = Math.min(window.devicePixelRatio || 1, 2);
  lienzo.width = Math.round(window.innerWidth * escala);
  lienzo.height = Math.round(window.innerHeight * escala);
  contexto.setTransform(escala, 0, 0, escala, 0, 0);
  columnas = Array.from({length: Math.ceil(window.innerWidth / 28)}, () => ({
    y: Math.random() * window.innerHeight,
    velocidad: 0.5 + Math.random() * 1.2,
    bits: Array.from({length: 9}, () => Math.random() < 0.5 ? '0' : '1')
  }));
  if (pausada) contexto.clearRect(0, 0, window.innerWidth, window.innerHeight);
}
function pintarLluvia(instante) {
  if (pausada || document.hidden) { cuadro = 0; return; }
  if (instante - ultimoCuadro >= 40) {
    ultimoCuadro = instante;
    contexto.clearRect(0, 0, window.innerWidth, window.innerHeight);
    contexto.fillStyle = getComputedStyle(document.body).getPropertyValue('--cian').trim();
    contexto.font = '13px Consolas, monospace';
    columnas.forEach((columna, i) => {
      columna.y += columna.velocidad * 3;
      if (columna.y > window.innerHeight + 160) columna.y = -10;
      columna.bits.forEach((bit, j) => {
        contexto.globalAlpha = (1 - j / columna.bits.length) * 0.8;
        contexto.fillText(bit, i * 28, columna.y - j * 16);
      });
    });
    contexto.globalAlpha = 1;
  }
  cuadro = requestAnimationFrame(pintarLluvia);
}
function actualizarBotonBits() {
  botonBits.textContent = pausada ? 'Activar bits' : 'Pausar bits';
  botonBits.setAttribute('aria-pressed', String(!pausada));
}
botonBits.onclick = () => {
  pausada = !pausada;
  actualizarBotonBits();
  if (pausada) { cancelAnimationFrame(cuadro); cuadro = 0; }
  else if (!cuadro && !document.hidden) cuadro = requestAnimationFrame(pintarLluvia);
};
window.addEventListener('resize', ajustarLluvia);
document.addEventListener('visibilitychange', () => {
  if (document.hidden) { cancelAnimationFrame(cuadro); cuadro = 0; }
  else if (!pausada && !cuadro) cuadro = requestAnimationFrame(pintarLluvia);
});
ajustarLluvia();
actualizarBotonBits();
if (!pausada) cuadro = requestAnimationFrame(pintarLluvia);
