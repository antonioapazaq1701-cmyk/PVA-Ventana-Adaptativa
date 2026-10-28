const bloques = JSON.parse(porId('datos-codigo').textContent);
let indice = 0;
let notasVisibles = true;
let lineasAjustadas = true;

function listar(filtro = '') {
  const lista = porId('lista-bloques');
  lista.replaceChildren();
  let archivo = '';
  let encontrados = 0;
  bloques.forEach((bloque, numero) => {
    const contenido = `${bloque.archivo} ${bloque.nombre} ${bloque.titulo} ${bloque.detalle} ${Object.values(bloque.notas).join(' ')}`;
    if (!contenido.toLocaleLowerCase().includes(filtro.toLocaleLowerCase())) return;
    encontrados++;
    if (archivo !== bloque.archivo) {
      archivo = bloque.archivo;
      const titulo = document.createElement('h3');
      titulo.textContent = archivo;
      lista.append(titulo);
    }
    const boton = document.createElement('button');
    boton.dataset.indice = numero;
    boton.className = numero === indice ? 'activo' : '';
    if (numero === indice) boton.setAttribute('aria-current', 'true');
    const nombre = document.createElement('span');
    nombre.textContent = bloque.nombre;
    const cantidad = Object.keys(bloque.notas).length;
    boton.append(nombre);
    if (cantidad) {
      const insignia = document.createElement('small');
      insignia.textContent = cantidad;
      insignia.setAttribute('aria-label', `${cantidad} líneas explicadas`);
      boton.append(insignia);
    }
    boton.onclick = () => {
      mostrarBloque(numero);
      lista.querySelector(`[data-indice="${numero}"]`)?.focus();
    };
    lista.append(boton);
  });
  porId('sin-resultados').hidden = encontrados !== 0;
}

function mostrarBloque(numero) {
  indice = Math.max(0, Math.min(bloques.length - 1, numero));
  const bloque = bloques[indice];
  const fin = bloque.inicio + bloque.codigo.length - 1;
  const cantidadNotas = Object.keys(bloque.notas).length;
  porId('ubicacion').textContent = `${bloque.archivo} / ${bloque.nombre} · ${indice + 1} de ${bloques.length}`;
  porId('titulo-bloque').textContent = bloque.titulo;
  porId('explicacion').textContent = bloque.detalle;
  porId('archivo-editor').textContent = bloque.archivo;
  porId('rango-editor').textContent = `Líneas ${bloque.inicio}–${fin}`;
  porId('contador-notas').textContent = cantidadNotas ? `${cantidadNotas} líneas explicadas` : 'Explicación general del bloque';
  porId('notas-visibles').disabled = cantidadNotas === 0;

  const fragmento = document.createDocumentFragment();
  bloque.codigo.forEach((texto, i) => {
    const numeroLinea = bloque.inicio + i;
    const explicacion = bloque.notas[numeroLinea];
    const fila = document.createElement('div');
    fila.className = 'linea' + (explicacion ? ' linea-explicada' : '');
    const numeroElemento = document.createElement('span');
    numeroElemento.className = 'numero';
    numeroElemento.textContent = numeroLinea;
    const codigo = document.createElement('span');
    codigo.className = 'codigo';
    for (const [contenido, clase] of bloque.colores[i]) {
      if (!clase) codigo.append(document.createTextNode(contenido));
      else {
        const token = document.createElement('span');
        token.className = `sintaxis-${clase}`;
        token.textContent = contenido;
        codigo.append(token);
      }
    }
    if (!texto) codigo.append(document.createTextNode(' '));
    fila.append(numeroElemento, codigo);
    fragmento.append(fila);
    if (explicacion) {
      const nota = document.createElement('div');
      nota.className = 'explicacion-linea';
      const etiqueta = document.createElement('span');
      etiqueta.textContent = `Línea ${numeroLinea}`;
      const detalle = document.createElement('p');
      detalle.textContent = explicacion;
      nota.append(etiqueta, detalle);
      fragmento.append(nota);
    }
  });
  porId('codigo').replaceChildren(fragmento);
  porId('codigo').scrollTop = 0;
  porId('codigo').scrollLeft = 0;
  porId('bloque-anterior').disabled = indice === 0;
  porId('bloque-siguiente').disabled = indice === bloques.length - 1;
  listar(porId('buscar').value);
}

porId('buscar').oninput = evento => listar(evento.target.value);
porId('bloque-anterior').onclick = () => mostrarBloque(indice - 1);
porId('bloque-siguiente').onclick = () => mostrarBloque(indice + 1);
porId('notas-visibles').onclick = () => {
  notasVisibles = !notasVisibles;
  porId('codigo').classList.toggle('sin-notas', !notasVisibles);
  porId('notas-visibles').textContent = notasVisibles ? 'Ocultar explicaciones' : 'Mostrar explicaciones';
  porId('notas-visibles').setAttribute('aria-pressed', String(notasVisibles));
};
porId('ajustar-lineas').onclick = () => {
  lineasAjustadas = !lineasAjustadas;
  porId('codigo').classList.toggle('ajustadas', lineasAjustadas);
  porId('ajustar-lineas').textContent = lineasAjustadas ? 'Sin ajuste' : 'Ajustar líneas';
  porId('ajustar-lineas').setAttribute('aria-pressed', String(lineasAjustadas));
};
mostrarBloque(0);
