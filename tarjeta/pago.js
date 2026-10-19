/* College Traveler · Pago con tarjeta (Mercado Pago)
   Widget compartido: lo usan /tarjeta/ y las presentaciones web /v/<codigo>/.
   Uso: <div id="ctpago" data-v="rec…"></div><script src="/tarjeta/pago.js"></script>
   Flujo: correo → (si no está registrado: registro rápido aquí mismo) → pagos → Mercado Pago. */
(function () {
  var API = 'https://script.google.com/macros/s/AKfycbwNDEGZo4UuFyzFZl5PrS7EoYzdoEESbuJnYsAvs63LgQ01IT8mm5WFAObxPgTyN2Pr/exec';
  var MESES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
  var TARIFA = { Cuadruple: 'Cuádruple (4 por habitación)', Triple: 'Triple (3 por habitación)', Doble: 'Doble (2 por habitación)', Individual: 'Individual' };
  var CSS = '' +
    '.ctp{font-family:Lato,Helvetica,Arial,sans-serif;color:#14142B}' +
    '.ctp .st{display:none}.ctp .st.on{display:block}' +
    '.ctp h3{font-family:"Cormorant Garamond",Georgia,serif;font-weight:600;font-size:30px;line-height:1.1;margin:0 0 8px}' +
    '.ctp p.bs{font-size:15.5px;line-height:1.6;color:#5A6472;font-weight:300;margin:0 0 16px}' +
    '.ctp label.t{display:block;font-size:14px;font-weight:700;margin:14px 0 7px}' +
    '.ctp input.f,.ctp select.f{width:100%;font:inherit;font-size:16.5px;padding:13px 15px;border:1px solid #CBD3DC;border-radius:10px;outline:none;color:#14142B;background:#fff;-webkit-appearance:none;appearance:none}' +
    '.ctp select.f{background-image:linear-gradient(45deg,transparent 50%,#8A93A1 50%),linear-gradient(135deg,#8A93A1 50%,transparent 50%);background-position:calc(100% - 20px) 50%,calc(100% - 15px) 50%;background-size:5px 5px;background-repeat:no-repeat}' +
    '.ctp input.f:focus,.ctp select.f:focus{border-color:#009DE0;box-shadow:0 0 0 3px rgba(0,157,224,.15)}' +
    '.ctp .dos{display:grid;grid-template-columns:1fr 1fr;gap:0 12px}' +
    '.ctp .seg2{display:flex;gap:8px}.ctp .seg2 label{flex:1;border:1px solid #CBD3DC;border-radius:10px;padding:12px;text-align:center;font-size:15px;cursor:pointer}' +
    '.ctp .seg2 input{position:absolute;opacity:0;pointer-events:none}.ctp .seg2 label.sel{border-color:#009DE0;background:#F2FAFE;font-weight:700}' +
    '.ctp .chk{display:flex;gap:10px;align-items:flex-start;font-size:13.5px;color:#5A6472;line-height:1.5;margin-top:16px;cursor:pointer}' +
    '.ctp .chk input{margin-top:3px;accent-color:#009DE0;width:17px;height:17px;flex:none}' +
    '.ctp .btn{display:block;width:100%;margin-top:16px;background:#009DE0;color:#fff;border:0;border-radius:10px;font:inherit;font-weight:700;font-size:16.5px;padding:15px;cursor:pointer;text-align:center;text-decoration:none}' +
    '.ctp .btn:hover{background:#0089C4}.ctp .btn[disabled]{opacity:.55;cursor:default}' +
    '.ctp .err{display:none;color:#C2410C;font-size:14px;margin-top:10px;line-height:1.5}' +
    '.ctp .op{display:block;border:1px solid #E7EBF0;border-radius:12px;padding:15px 15px 13px 44px;margin-top:10px;cursor:pointer;position:relative}' +
    '.ctp .op>input{position:absolute;left:15px;top:18px;accent-color:#009DE0;width:17px;height:17px;margin:0}' +
    '.ctp .op.sel{border-color:#009DE0;background:#F2FAFE}' +
    '.ctp .op .nm{font-size:16px;font-weight:700}.ctp .op .fe{font-size:13.5px;color:#5A6472;margin-top:1px}.ctp .op .fe .v{color:#C2410C;font-weight:700}' +
    '.ctp .op .pr{display:flex;justify-content:space-between;align-items:baseline;margin-top:8px;font-size:14px;color:#5A6472}.ctp .op .pr b{font-size:20px;color:#14142B}' +
    '.ctp .op .mt{display:none;margin-top:10px}.ctp .op.sel .mt{display:block}' +
    '.ctp .op .px{position:relative}.ctp .op .px:before{content:"$";position:absolute;left:12px;top:11px;color:#5A6472;font-size:17px}' +
    '.ctp .op .mt input{width:100%;font:inherit;font-size:17px;padding:11px 12px 11px 28px;border:1px solid #CBD3DC;border-radius:9px;outline:none}' +
    '.ctp .op .mt small{display:block;color:#8A93A1;font-size:12.5px;margin-top:6px}' +
    '.ctp .msi{font-size:13.5px;color:#5A6472;margin:14px 0 0;line-height:1.55}' +
    '.ctp .seg{display:flex;gap:8px;font-size:12.5px;color:#8A93A1;margin-top:12px;line-height:1.5}.ctp .seg svg{flex:none;margin-top:2px}' +
    '.ctp .otra{font-size:14px;text-align:center;margin-top:14px;color:#5A6472}.ctp .otra a{color:#009DE0}' +
    '.ctp .ok{display:inline-block;border:1px solid #12805C;color:#12805C;font-size:12px;letter-spacing:2px;text-transform:uppercase;padding:5px 12px;border-radius:20px;margin-bottom:10px}' +
    '.ctp .spin{display:inline-block;width:15px;height:15px;border:2px solid rgba(255,255,255,.5);border-top-color:#fff;border-radius:50%;animation:ctpg .8s linear infinite;vertical-align:-2px;margin-right:8px}' +
    '@keyframes ctpg{to{transform:rotate(360deg)}}' +
    '@media (max-width:420px){.ctp .dos{grid-template-columns:1fr}}';
  var CANDADO = '<svg width="13" height="15" viewBox="0 0 13 15" aria-hidden="true"><rect x="1" y="6.5" width="11" height="7.5" rx="1.5" fill="none" stroke="#8A93A1" stroke-width="1.4"/><path d="M3.5 6.5V4.5a3 3 0 0 1 6 0v2" fill="none" stroke="#8A93A1" stroke-width="1.4"/></svg>';
  var HTML = '' +
    '<div class="st on" data-s="correo">' +
      '<h3>Paga con tarjeta</h3>' +
      '<p class="bs">Escribe tu correo. Si ya te registraste, te mostramos lo que te falta; si no, te registras aquí mismo en un minuto. Puedes pagar el siguiente pago, una parte o todo el viaje.</p>' +
      '<form data-f="correo" novalidate><label class="t">Tu correo</label>' +
      '<input class="f" name="correo" type="email" inputmode="email" autocomplete="email" placeholder="nombre@correo.com">' +
      '<button class="btn" type="submit">Continuar</button><div class="err"></div></form>' +
    '</div>' +
    '<div class="st" data-s="registro">' +
      '<h3>Regístrate para pagar</h3>' +
      '<p class="bs">No encontramos <b data-k="correo"></b> en este viaje. Regístrate aquí y enseguida pagas. Tus documentos los subes después.</p>' +
      '<form data-f="registro" novalidate>' +
        '<label class="t">Nombre completo, como en tu identificación</label><input class="f" name="nombre" autocomplete="name">' +
        '<div class="dos"><div><label class="t">Matrícula</label><input class="f" name="matricula" placeholder="00123456"></div>' +
        '<div><label class="t">WhatsApp (10 dígitos)</label><input class="f" name="tel" type="tel" inputmode="numeric" autocomplete="tel-national" placeholder="228 123 4567"></div></div>' +
        '<label class="t">Género</label><div class="seg2" data-g><label><input type="radio" name="genero" value="Femenino">Femenino</label><label><input type="radio" name="genero" value="Masculino">Masculino</label></div>' +
        '<div data-tarifa style="display:none"><label class="t">Tipo de habitación</label><select class="f" name="tarifa"></select></div>' +
        '<label class="chk"><input type="checkbox" name="privacidad" value="1"><span>Acepto el aviso de privacidad: mis datos se usan solo para organizar este viaje (logística, seguridad, recordatorios de pago y contacto de emergencia) y no se comparten con terceros ajenos al viaje.</span></label>' +
        '<button class="btn" type="submit">Registrarme y continuar</button><div class="err"></div>' +
      '</form>' +
      '<div class="otra"><a href="#" data-volver>Me registré con otro correo</a></div>' +
    '</div>' +
    '<div class="st" data-s="pagos">' +
      '<h3>Hola, <span data-k="nombre"></span></h3>' +
      '<p class="bs" data-k="intro"></p>' +
      '<div data-lista></div><p class="msi" data-k="msi"></p>' +
      '<button class="btn" type="button" data-pagar>Pagar con tarjeta</button><div class="err" data-e="pagar"></div>' +
      '<div class="seg">' + CANDADO + '<span>Te llevamos a la página oficial de Mercado Pago. Al terminar, tu pago se registra solo y tu recibo te llega por correo. No tienes que subir comprobante.</span></div>' +
      '<div class="otra"><a href="#" data-volver>No soy yo</a></div>' +
    '</div>' +
    '<div class="st" data-s="liquidado">' +
      '<span class="ok">Al corriente</span><h3>Ya pagaste todo tu viaje</h3>' +
      '<p class="bs">Gracias, <span data-k="nombre"></span>. No tienes pagos pendientes. Si crees que hay un error, escríbenos.</p>' +
      '<div class="otra"><a href="#" data-volver>Consultar otro correo</a></div>' +
    '</div>' +
    '<div class="st" data-s="sinviaje"><h3>Abre el link de tu viaje</h3><p class="bs">Este link no trae el viaje. Ábrelo desde la presentación o el correo de tu viaje, o escríbenos y te lo mandamos.</p></div>' +
    '<div class="seg" data-pie>' + CANDADO + '<span>Los datos de tu tarjeta solo los ve Mercado Pago. El precio con tarjeta incluye la comisión del banco.</span></div>';

  function dinero(n) { return '$' + Number(n).toLocaleString('es-MX', { maximumFractionDigits: 2 }); }
  function tj(b) { return Math.ceil(b * 1.0818 + 4); }
  function fecha(iso) { if (!iso) return ''; var p = iso.split('-'); return Number(p[2]) + ' de ' + MESES[Number(p[1]) - 1]; }
  var ERRORES = {
    nombre: 'Escribe tu nombre completo, con apellidos.', matricula: 'Escribe tu matrícula.', tel: 'Tu WhatsApp debe tener 10 dígitos.',
    genero: 'Elige tu género (lo usamos para armar las habitaciones).', tarifa: 'Elige tu tipo de habitación.',
    privacidad: 'Para registrarte acepta el aviso de privacidad.', correo: 'Revisa tu correo: parece que está incompleto.',
    baja: 'Esa matrícula aparece dada de baja en este viaje. Escríbenos por WhatsApp al 228 272 8556.'
  };

  function montar(el) {
    if (!document.getElementById('ctp-css')) { var s = document.createElement('style'); s.id = 'ctp-css'; s.textContent = CSS; document.head.appendChild(s); }
    el.classList.add('ctp'); el.innerHTML = HTML;
    var V = el.getAttribute('data-v') || new URLSearchParams(location.search).get('v') || '';
    var q = function (sel) { return el.querySelector(sel); }, qa = function (sel) { return el.querySelectorAll(sel); };
    var info = null, datos = null, correo = '';
    function ver(n) { [].forEach.call(qa('.st'), function (x) { x.classList.toggle('on', x.getAttribute('data-s') === n); }); }
    function txt(k, v) { [].forEach.call(qa('[data-k="' + k + '"]'), function (x) { x.textContent = v; }); }
    function err(box, t) { box.textContent = t || ''; box.style.display = t ? 'block' : 'none'; }
    function cargando(b, t, original) { b.disabled = !!t; b.innerHTML = t ? '<span class="spin"></span>' + t : original; }
    function api(o) { var u = API + '?v=' + encodeURIComponent(V); for (var k in o) u += '&' + k + '=' + encodeURIComponent(o[k]); return fetch(u).then(function (r) { if (!r.ok) throw 0; return r.json(); }); }

    if (!/^rec[A-Za-z0-9]{14}$/.test(V)) { ver('sinviaje'); return; }
    api({ accion: 'viaje' }).then(function (r) {
      if (!r.ok) return; info = r.viaje;
      el.dispatchEvent(new CustomEvent('ctp:viaje', { detail: info }));
      if (!info.unDia && info.tarifas && info.tarifas.length > 1) {
        q('[data-tarifa]').style.display = 'block';
        q('select[name=tarifa]').innerHTML = '<option value="">Elige una opción</option>' + info.tarifas.map(function (t) { return '<option value="' + t + '">' + (TARIFA[t] || t) + '</option>'; }).join('');
      }
    }).catch(function () {});
    try { var c0 = localStorage.getItem('ct_correo'); if (c0) q('input[name=correo]').value = c0; } catch (e) {}

    function resultado(r) {
      if (r.correo) correo = r.correo;
      try { localStorage.setItem('ct_correo', correo); } catch (e) {}
      if (r.liquidado || !r.pagos.length) { txt('nombre', r.nombre); ver('liquidado'); return; }
      datos = r; pintar(); ver('pagos');
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // 1) Correo
    var fC = q('form[data-f=correo]');
    fC.addEventListener('submit', function (ev) {
      ev.preventDefault(); var e = fC.querySelector('.err'); err(e);
      correo = fC.correo.value.trim().toLowerCase();
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(correo)) { err(e, ERRORES.correo); return; }
      var b = fC.querySelector('.btn'); cargando(b, 'Buscando tu registro…');
      api({ accion: 'buscar', correo: correo }).then(function (r) {
        cargando(b, '', 'Continuar');
        if (!r.ok && r.error === 'sin_registro') { txt('correo', correo); ver('registro'); setTimeout(function () { q('input[name=nombre]').focus(); }, 50); return; }
        if (!r.ok) { err(e, 'No pudimos consultar tus pagos. Intenta de nuevo en un momento.'); return; }
        resultado(r);
      }).catch(function () { cargando(b, '', 'Continuar'); err(e, 'No pudimos consultar tus pagos. Revisa tu conexión e intenta de nuevo.'); });
    });

    // 2) Registro rápido
    var fR = q('form[data-f=registro]');
    [].forEach.call(fR.querySelectorAll('.seg2 input'), function (r) { r.addEventListener('change', function () {
      [].forEach.call(fR.querySelectorAll('.seg2 label'), function (l) { l.classList.toggle('sel', l.querySelector('input').checked); }); }); });
    fR.addEventListener('submit', function (ev) {
      ev.preventDefault(); var e = fR.querySelector('.err'); err(e);
      var g = fR.querySelector('input[name=genero]:checked');
      var o = { accion: 'registrar', correo: correo, nombre: fR.nombre.value.trim(), matricula: fR.matricula.value.trim(),
        tel: fR.tel.value.replace(/\D/g, ''), genero: g ? g.value : '', tarifa: fR.tarifa.value, privacidad: fR.privacidad.checked ? '1' : '' };
      var falta = o.nombre.split(/\s+/).length < 2 ? 'nombre' : !o.matricula ? 'matricula' : o.tel.length !== 10 ? 'tel' : !o.genero ? 'genero' :
        (q('[data-tarifa]').style.display === 'block' && !o.tarifa) ? 'tarifa' : !o.privacidad ? 'privacidad' : '';
      if (falta) { err(e, ERRORES[falta]); return; }
      var b = fR.querySelector('.btn'); cargando(b, 'Registrándote…');
      api(o).then(function (r) {
        cargando(b, '', 'Registrarme y continuar');
        if (!r.ok) { err(e, ERRORES[r.error] || 'No pudimos registrarte. Intenta de nuevo o escríbenos por WhatsApp al 228 272 8556.'); return; }
        resultado(r);
      }).catch(function () { cargando(b, '', 'Registrarme y continuar'); err(e, 'No pudimos registrarte. Revisa tu conexión e intenta de nuevo.'); });
    });

    // 3) Pagos
    function op(v, nm, fe, m, t, sel, extra) {
      return '<label class="op' + (sel ? ' sel' : '') + '"><input type="radio" name="pg" value="' + v + '"' + (sel ? ' checked' : '') + '>' +
        '<div class="nm">' + nm + '</div><div class="fe">' + fe + '</div>' +
        (m != null ? '<div class="pr"><span>Transferencia ' + dinero(m) + '</span><span>Tarjeta <b>' + dinero(t) + '</b></span></div>' : '') + (extra || '') + '</label>';
    }
    function pintar() {
      var ps = datos.pagos, p = ps[0], fe = p.vencido ? '<span class="v">Venció el ' + fecha(p.fecha) + '</span>' : 'Vence el ' + fecha(p.fecha);
      txt('nombre', datos.nombre);
      txt('intro', 'Te falta ' + dinero(datos.todo.monto) + (ps.length > 1 ? ' en ' + ps.length + ' pagos' : '') + '. Elige cuánto quieres pagar.');
      var min = Math.min(100, datos.todo.monto);
      var h = op(p.id, 'Siguiente pago · ' + p.etiqueta, fe, p.monto, p.tarjeta, true);
      if (ps.length > 1) h += op('todo', 'Liquidar todo el viaje', 'Los ' + ps.length + ' pagos que te faltan, en un solo cargo', datos.todo.monto, datos.todo.tarjeta, false);
      h += op('monto', 'Otra cantidad', 'Abona lo que quieras; se descuenta de tus próximos pagos', null, null, false,
        '<div class="mt"><div class="px"><input type="number" data-m inputmode="numeric" min="' + min + '" max="' + datos.todo.monto + '" step="50" placeholder="Monto por transferencia"></div><small data-mh></small></div>');
      q('[data-lista]').innerHTML = h;
      [].forEach.call(qa('[data-lista] input[name=pg]'), function (r) { r.addEventListener('change', function () { actualizar(); if (r.value === 'monto') q('[data-m]').focus(); }); });
      q('[data-m]').addEventListener('input', actualizar);
      actualizar();
    }
    function libre() { var v = Math.round(Number(q('[data-m]').value)); return v > 0 ? v : 0; }
    function elegido() {
      var r = q('[data-lista] input[name=pg]:checked'); if (!r) return null;
      if (r.value === 'todo') return { p: 'todo', tarjeta: datos.todo.tarjeta };
      if (r.value === 'monto') { var m = libre(); return { p: 'monto', m: m, tarjeta: m ? tj(m) : 0 }; }
      return { p: datos.pagos[0].id, tarjeta: datos.pagos[0].tarjeta };
    }
    function actualizar() {
      [].forEach.call(qa('[data-lista] .op'), function (l) { l.classList.toggle('sel', l.querySelector('input[name=pg]').checked); });
      var e = elegido(), min = Math.min(100, datos.todo.monto), b = q('[data-pagar]');
      q('[data-mh]').textContent = (e.p === 'monto' && e.m) ? 'Con tarjeta: ' + dinero(e.tarjeta) + '.' : 'De ' + dinero(min) + ' a ' + dinero(datos.todo.monto) + '.';
      b.disabled = !e.tarjeta; b.textContent = e.tarjeta ? 'Pagar ' + dinero(e.tarjeta) + ' con tarjeta' : 'Escribe el monto';
      txt('msi', e.tarjeta ? 'En una sola exhibición o hasta en 3 meses sin intereses de ' + dinero(Math.round(e.tarjeta / 3 * 100) / 100) + '.' : '');
      err(q('[data-e=pagar]'));
    }
    q('[data-pagar]').addEventListener('click', function () {
      var e = elegido(), box = q('[data-e=pagar]'), b = this, t0 = b.textContent; if (!e) return;
      var o = { accion: 'pagar', correo: correo, p: e.p };
      if (e.p === 'monto') { var min = Math.min(100, datos.todo.monto); if (e.m < min || e.m > datos.todo.monto) { err(box, 'El monto va de ' + dinero(min) + ' a ' + dinero(datos.todo.monto) + '.'); return; } o.m = e.m; }
      cargando(b, 'Abriendo Mercado Pago…');
      api(o).then(function (r) { if (r.ok && r.url) { location.href = r.url; return; } cargando(b, '', t0); err(box, 'No pudimos abrir el pago. Intenta de nuevo o paga por transferencia.'); })
        .catch(function () { cargando(b, '', t0); err(box, 'No pudimos abrir el pago. Revisa tu conexión e intenta de nuevo.'); });
    });
    [].forEach.call(qa('[data-volver]'), function (a) { a.addEventListener('click', function (ev) { ev.preventDefault(); ver('correo'); q('input[name=correo]').focus(); }); });
  }

  function iniciar() { [].forEach.call(document.querySelectorAll('[data-ctpago]'), montar); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
})();
