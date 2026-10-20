/* Decorative, synthetic signals only. No recording data or scientific processing. */
document.addEventListener("DOMContentLoaded", () => {
  "use strict";
  const home = document.querySelector(".spikesorted-home");
  if (!home) return;
  const canvas = document.getElementById("spike-field");
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const toggle = document.getElementById("motion-toggle");
  let paused = reduced.matches, visible = true, frame = null, last = 0, elapsed = 0;
  let width = 0, height = 0;
  function resize() {
    width = canvas.clientWidth; height = canvas.clientHeight;
    const ratio = Math.min(devicePixelRatio || 1, 2);
    canvas.width = width * ratio; canvas.height = height * ratio;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    draw();
  }
  function draw() {
    ctx.clearRect(0, 0, width, height);
    const spacing = height / 14;
    for (let row = 0; row < 14; row++) {
      const baseline = row * spacing + spacing / 2;
      ctx.beginPath();
      ctx.strokeStyle = `rgba(${row % 3 === 0 ? "190,218,141" : "120,222,176"},${.15 + (row % 4) * .05})`;
      ctx.lineWidth = .8;
      for (let x = 0; x <= width; x += 2) {
        const sx = (x + elapsed * 24 + row * 71) % 950;
        const d = sx - 470;
        const spike = -38 * Math.exp(-(d * d) / 12) + 18 * Math.exp(-((d - 7) ** 2) / 45);
        const y = baseline + Math.sin(sx * .15 + row) * 1.6 + Math.sin(sx * .037) * 2 + spike;
        if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.stroke();
      const dotX = ((470 - elapsed * 24 - row * 71) % 950 + 950) % 950;
      if (dotX < width) {
        ctx.beginPath(); ctx.fillStyle = "#caf4bd"; ctx.shadowColor = "#9fffc4"; ctx.shadowBlur = 12;
        ctx.arc(dotX, baseline - 36, 1.6, 0, Math.PI * 2); ctx.fill(); ctx.shadowBlur = 0;
      }
    }
  }
  function tick(time) {
    frame = null;
    if (paused || !visible || document.hidden) { last = 0; return; }
    if (last) elapsed += Math.min((time - last) / 1000, .05);
    last = time; draw(); frame = requestAnimationFrame(tick);
  }
  function sync() {
    toggle.textContent = paused ? "Play animation" : "Pause animation";
    toggle.setAttribute("aria-pressed", String(paused));
    if (frame !== null) cancelAnimationFrame(frame);
    frame = null; last = 0;
    if (!paused && visible && !document.hidden) frame = requestAnimationFrame(tick);
  }
  toggle.hidden = false;
  toggle.addEventListener("click", () => { paused = !paused; sync(); });
  reduced.addEventListener("change", () => { paused = reduced.matches; sync(); });
  document.addEventListener("visibilitychange", sync);
  new IntersectionObserver(entries => { visible = entries[0].isIntersecting; sync(); }).observe(canvas);
  new ResizeObserver(resize).observe(canvas);
  resize(); sync();
});
