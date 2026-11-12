/* rolls.js
 * The expandable roll-number grid, including copy-to-clipboard.
 *
 * Chips are painted lazily: a 1,037-roll notice only builds its chips when
 * somebody actually opens that list.
 */
/* ------------------------------------------------------------ roll chips
   Rendered lazily: the chips for a 1,037-roll notice are only built when
   somebody actually opens that list. */
function rollWrapHtml(rolls, hit){
  return `<div class="rollwrap" data-rolls="${esc(rolls.join(","))}" data-hit="${esc(hit ?? "")}">
    <div class="rolltools">
      <input type="text" inputmode="numeric" class="rollfilter" placeholder="${esc(t("filterList"))}" aria-label="${esc(t("filterList"))}">
      <button type="button" class="btn rollcopy">${esc(t("copyAll"))}</button>
      <span class="rollcount"></span>
    </div>
    <div class="rollgrid"></div>
  </div>`;
}
/* The chip for the number you just searched. Every caller passed hit=null, so
   the .hit style existed but never applied to anything; reading the live
   search box means opening any list highlights your roll without the archive
   having to be re-rendered on every keystroke. */
const currentRoll = () => AS(($("#roll") || {}).value || "").replace(/\D/g, "");
function paintRolls(wrap){
  const all = (wrap.dataset.rolls || "").split(",").filter(Boolean);
  const hit = wrap.dataset.hit || currentRoll();
  const q   = AS((wrap.querySelector(".rollfilter") || {}).value || "").replace(/\D/g, "");
  const list = q ? all.filter(r => r.includes(q)) : all;
  const grid = wrap.querySelector(".rollgrid");
  grid.innerHTML = list.length
    ? list.map(r => `<span class="rollchip${r === hit ? " hit" : ""}">${esc(NUM(r))}</span>`).join("")
    : `<div class="rollempty">${esc(t("noMatchInList"))}</div>`;
  wrap.querySelector(".rollcount").textContent =
    q ? t("showing")(NUM(list.length), NUM(all.length)) : NUM(all.length);
  /* A 1,037-chip grid scrolls inside itself, so a highlighted chip is usually
     off-screen when the list opens. */
  const chip = grid.querySelector(".rollchip.hit");
  if (chip && chip.scrollIntoView) chip.scrollIntoView({ block:"nearest", inline:"nearest" });
}
