let actual = 0;
const laminas = [...document.querySelectorAll('.lamina')];
function mostrar(numero) {
  actual = Math.max(0, Math.min(laminas.length - 1, numero));
  laminas.forEach((lamina, i) => lamina.hidden = i !== actual);
  porId('indice').value = actual;
  porId('contador').textContent = `${actual + 1} / ${laminas.length}`;
  porId('anterior').disabled = actual === 0;
  porId('siguiente').disabled = actual === laminas.length - 1;
  window.scrollTo(0, 0);
}
porId('anterior').onclick = () => mostrar(actual - 1);
porId('siguiente').onclick = () => mostrar(actual + 1);
porId('indice').onchange = evento => mostrar(Number(evento.target.value));
document.addEventListener('keydown', evento => {
  if (['INPUT', 'SELECT', 'TEXTAREA', 'BUTTON'].includes(evento.target.tagName)) return;
  if (evento.key === 'ArrowRight') { evento.preventDefault(); mostrar(actual + 1); }
  if (evento.key === 'ArrowLeft') { evento.preventDefault(); mostrar(actual - 1); }
});

let bloque = 0;
const grupos = [[0, 2], [2, 6], [6, 12], [12, 20]];
function dibujar() {
  const fragmento = document.createDocumentFragment();
  for (let i = 0; i < 20; i++) {
    const sobre = document.createElement('div');
    const confirmado = bloque > 0 && i < grupos[bloque - 1][1];
    const enVentana = bloque < grupos.length && i >= grupos[bloque][0] && i < grupos[bloque][1];
    sobre.className = 'sobre' + (confirmado ? ' hecho' : enVentana ? ' en-ventana' : '');
    sobre.textContent = i;
    sobre.setAttribute('aria-label', `Parte ${i}: ${confirmado ? 'confirmada' : enVentana ? 'ventana actual' : 'pendiente'}`);
    fragmento.append(sobre);
  }
  porId('sobres-demo').replaceChildren(fragmento);
  porId('detalle-demo').textContent = bloque === 0
    ? 'Preparado: ventana 2, partes 0 y 1.'
    : `ACK ${grupos[bloque - 1][1]}: partes ${grupos[bloque - 1][0]} a ${grupos[bloque - 1][1] - 1} confirmadas.${bloque < 4 ? ' Siguiente ventana: ' + [2, 4, 6, 8][bloque] + '.' : ' Mensaje completo: veinte partes.'}`;
  porId('paso-bloque').disabled = bloque === 4;
}
porId('paso-bloque').onclick = () => { bloque = Math.min(4, bloque + 1); dibujar(); };
porId('reiniciar-bloque').onclick = () => { bloque = 0; dibujar(); };

function dividirEjemplo() {
  const datos = new TextEncoder().encode(porId('texto-demo').value);
  const partes = document.createDocumentFragment();
  for (let inicio = 0; inicio < datos.length; inicio += 256) {
    const parte = datos.slice(inicio, inicio + 256);
    const tarjeta = document.createElement('div');
    tarjeta.className = 'fragmento';
    const titulo = document.createElement('strong');
    titulo.textContent = `Parte ${inicio / 256} · ${parte.length} bytes`;
    const vista = document.createElement('span');
    vista.textContent = new TextDecoder('utf-8').decode(parte).slice(0, 50) + (parte.length > 50 ? '…' : '');
    tarjeta.append(titulo, vista);
    partes.append(tarjeta);
  }
  porId('fragmentos-demo').replaceChildren(partes);
  porId('resultado-fragmentos').textContent = `${datos.length} bytes · ${Math.ceil(datos.length / 256)} partes de hasta 256 bytes`;
}
porId('texto-demo').addEventListener('input', dividirEjemplo);
porId('texto-ejemplo').onclick = () => {
  porId('texto-demo').value = 'Mensaje PVA: '.repeat(30) + '🌎';
  dividirEjemplo();
};
mostrar(0);
dibujar();
dividirEjemplo();
