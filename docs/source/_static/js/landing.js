/* Keep the complete command in the DOM for copying and assistive technology. */
document.addEventListener("DOMContentLoaded", () => {
  const command = document.querySelector(".ss-command code");
  if (!command) return;
  const replay = document.querySelector(".ss-replay");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const text = command.textContent;
  let timer;
  function finish() {
    window.clearTimeout(timer);
    command.textContent = text;
    replay.hidden = reducedMotion.matches;
    replay.disabled = false;
  }
  function play() {
    if (reducedMotion.matches) return finish();
    window.clearTimeout(timer);
    const original = document.createElement("span");
    original.className = "ss-command-text";
    original.textContent = text;
    original.setAttribute("aria-hidden", "true");
    const animation = document.createElement("span");
    animation.className = "ss-command-animation";
    animation.setAttribute("aria-hidden", "true");
    command.replaceChildren(original, animation);
    command.setAttribute("aria-label", text);
    replay.hidden = false;
    replay.disabled = true;
    let position = 0;
    function type() {
      animation.textContent = text.slice(0, ++position);
      if (position < text.length) timer = window.setTimeout(type, 30);
      else timer = window.setTimeout(finish, 650);
    }
    timer = window.setTimeout(type, 450);
  }
  command.addEventListener("copy", (event) => {
    if (command.querySelector(".ss-command-animation")) {
      event.clipboardData.setData("text/plain", text);
      event.preventDefault();
    }
  });
  replay.addEventListener("click", play);
  reducedMotion.addEventListener("change", finish);
  play();
});
