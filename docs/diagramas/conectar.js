// Preenche <i data-ic="pack:nome"> com o SVG do icone e desenha os conectores declarados em window.LIGACOES.
document.querySelectorAll("[data-ic]").forEach((el) => { el.innerHTML = window.ICONS[el.dataset.ic] || ""; });
document.querySelectorAll(".ic svg path[fill='currentColor'], .ic svg").forEach(() => {});

function desenhar() {
  const tela = document.getElementById("tela");
  const base = tela.getBoundingClientRect();
  const svg = document.getElementById("conectores");
  svg.setAttribute("width", base.width);
  svg.setAttribute("height", base.height);
  svg.innerHTML = `<defs>
    <marker id="seta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#334155"/></marker></defs>`;
  const pt = (id, lado, desloc = 0) => {
    const r = document.getElementById(id).getBoundingClientRect();
    const x0 = r.left - base.left, y0 = r.top - base.top;
    return {
      t: [x0 + r.width / 2 + desloc, y0], b: [x0 + r.width / 2 + desloc, y0 + r.height],
      l: [x0, y0 + r.height / 2 + desloc], r: [x0 + r.width, y0 + r.height / 2 + desloc],
    }[lado];
  };
  for (const c of window.LIGACOES) {
    const [a, b] = [pt(c.de, c.lde, c.dde || 0), pt(c.para, c.lpara, c.dpara || 0)];
    if (c.vertical) a[0] = b[0];
    let d;
    if (c.reta) d = `M${a[0]},${a[1]} L${b[0]},${b[1]}`;
    else if (c.lde === "b" || c.lde === "t") { const my = (a[1] + b[1]) / 2; d = `M${a[0]},${a[1]} C${a[0]},${my} ${b[0]},${my} ${b[0]},${b[1]}`; }
    else { const mx = (a[0] + b[0]) / 2; d = `M${a[0]},${a[1]} C${mx},${a[1]} ${mx},${b[1]} ${b[0]},${b[1]}`; }
    const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
    p.setAttribute("d", d); p.setAttribute("fill", "none");
    p.setAttribute("stroke", c.cor || "#334155"); p.setAttribute("stroke-width", "2.2");
    if (c.tracejado) p.setAttribute("stroke-dasharray", "7 6");
    p.setAttribute("marker-end", "url(#seta)");
    if (c.duplo) p.setAttribute("marker-start", "url(#seta)");
    svg.appendChild(p);
    if (c.rotulo) {
      const len = p.getTotalLength(), m = p.getPointAtLength(len * (c.pos || 0.5));
      const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
      const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
      t.setAttribute("class", "rot"); t.setAttribute("text-anchor", "middle"); t.setAttribute("dominant-baseline", "middle");
      t.setAttribute("x", m.x + (c.dx || 0)); t.setAttribute("y", m.y + (c.dy || 0)); t.textContent = c.rotulo;
      g.appendChild(t); svg.appendChild(g);
      const bb = t.getBBox();
      const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      bg.setAttribute("class", "rotbg"); bg.setAttribute("x", bb.x - 6); bg.setAttribute("y", bb.y - 3);
      bg.setAttribute("width", bb.width + 12); bg.setAttribute("height", bb.height + 6); bg.setAttribute("rx", 6);
      bg.setAttribute("stroke", "#cbd5e1");
      g.insertBefore(bg, t);
    }
  }
  document.body.dataset.pronto = "1";
}
window.addEventListener("load", desenhar);
