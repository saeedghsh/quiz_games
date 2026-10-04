const $ = (id) => document.getElementById(id);
const pending = new Map();
let worker;
let nextId = 0;
let mode = "words";
let state = { phase: "idle", tiles: [] };
let busy = false;
let round = 0;
let timer;
let deadline;
let duration = 30;

function farsiRound() { return mode === "words" && state.language === "fa"; }
function translated(english, farsi) { return farsiRound() ? farsi : english; }

function fatal(error) {
  clearInterval(timer);
  worker?.terminate();
  for (const request of pending.values()) {
    clearTimeout(request.timeout);
    request.reject(error);
  }
  pending.clear();
  $("loading").hidden = true;
  $("app").hidden = true;
  $("error").hidden = false;
  $("error-text").textContent = `The game could not load. Check your connection and try again. ${error.message}`;
}

function request(action, args = {}) {
  return new Promise((resolve, reject) => {
    const id = ++nextId;
    const timeout = setTimeout(() => fatal(new Error("The Python engine timed out.")), action === "init" ? 120000 : 60000);
    pending.set(id, { resolve, reject, timeout });
    worker.postMessage({ id, action, args });
  });
}

function setBusy(value) {
  busy = value;
  document.querySelectorAll("#app button, #app select, #answer").forEach((control) => {
    control.disabled = value;
  });
  $("app").setAttribute("aria-busy", String(value));
}

async function run(action) {
  if (busy) return;
  setBusy(true);
  $("feedback").hidden = true;
  try { await action(); }
  catch (error) {
    $("feedback").textContent = error.message;
    $("feedback").hidden = false;
  } finally { setBusy(false); }
}

function resetTimer() {
  clearInterval(timer);
  deadline = null;
  duration = Number($("duration").value);
  $("time").textContent = duration || "∞";
  $("time").parentElement.classList.remove("expired");
  $("timer-progress").style.width = "100%";
}

function startTimer() {
  if (!duration) return;
  deadline = Date.now() + duration * 1000;
  const tick = () => {
    const remaining = Math.max(0, deadline - Date.now());
    $("time").textContent = Math.ceil(remaining / 1000);
    $("timer-progress").style.width = `${remaining / (duration * 10)}%`;
    if (!remaining) {
      clearInterval(timer);
      $("time").parentElement.classList.add("expired");
      $("instruction").textContent = translated("Time’s up! Declare your answer when you’re ready.", "زمان تمام شد! واژهٔ خود را بنویسید.");
    }
  };
  timer = setInterval(tick, 200);
  tick();
}

function configureMode() {
  const words = mode === "words";
  const farsi = farsiRound();
  const board = document.querySelector(".board");
  board.dir = farsi ? "rtl" : "ltr";
  board.lang = farsi ? "fa" : "en";
  $("answer").dir = farsi ? "rtl" : "ltr";
  $("answer").lang = farsi ? "fa" : "en";
  $("words-mode").classList.toggle("active", words);
  $("numbers-mode").classList.toggle("active", !words);
  $("words-mode").setAttribute("aria-pressed", String(words));
  $("numbers-mode").setAttribute("aria-pressed", String(!words));
  $("letter-setting").hidden = !words;
  $("language-setting").hidden = !words;
  $("number-setting").hidden = words;
  $("game-kicker").textContent = words ? translated("THE LETTERS ROUND", "بازی واژه‌های فارسی") : "THE NUMBERS ROUND";
  $("game-title").textContent = words ? translated("Find your longest word.", "بلندترین واژه را بسازید.") : "Get as close as you can.";
  $("answer-label").textContent = words ? translated("Your word or words", "واژه‌های شما") : "Your calculation";
  $("answer").placeholder = words ? translated("What can you make?", "چه واژه‌ای می‌توانید بسازید؟") : "For example: (25 + 3) * 7";
  $("answer-help").textContent = words ? translated("Separate multiple words with spaces. Your longest valid word scores.", "واژه‌ها را با فاصله یا «،» جدا کنید. نیم‌فاصله امتیاز ندارد.") : "Use +, -, *, / and parentheses. Division must give a whole number.";
  $("vowel").hidden = farsi;
  $("consonant").hidden = farsi;
  $("draw-letter").hidden = !farsi;
  $("fill").textContent = translated("Fill the rest ↗", "انتخاب بقیهٔ حروف ↖");
  $("submit").textContent = translated("Submit answer ↗", "ثبت پاسخ ↖");
  $("skip").textContent = translated("Skip round", "رد کردن این دور");
  $("result-title").textContent = translated("Round complete", "پایان این دور");
  document.querySelector(".clock small").textContent = translated("SECONDS", "ثانیه");
  document.querySelector(".solution .eyebrow").textContent = translated("FROM THE SOLVER", "پاسخ‌های پیشنهادی");
  const rules = document.querySelector(".rules");
  rules.dir = farsi ? "rtl" : "ltr";
  rules.lang = farsi ? "fa" : "en";
  rules.querySelector("h3").textContent = translated("How to play", "روش بازی");
  rules.querySelector(".eyebrow").textContent = translated("A QUICK REFRESHER", "یادآوری کوتاه");
  rules.querySelector(".timer-note").textContent = translated("The timer is for thinking. When it ends, you can still declare your answer.", "زمان‌سنج برای فکر کردن است. پس از پایان زمان هم می‌توانید پاسخ خود را بنویسید.");
  const paragraphs = farsi ? [
    "با حروف روی صفحه بلندترین واژه را بسازید. هر حرف فقط یک بار قابل استفاده است.",
    "حروف از کل الفبا انتخاب می‌شوند. هر حرف در بلندترین پاسخ درست، یک امتیاز دارد.",
    "ک و ی عربی پذیرفته می‌شوند. حرکت‌ها و نیم‌فاصله شمرده نمی‌شوند. «آ» و «ا» دو حرف جدا هستند.",
  ] : words ? [
    "Build the longest dictionary word you can from the letters on the board.",
    "Use each tile only once. Each letter in your longest valid word earns one point.",
  ] : [
    "Use any of your six numbers to reach the target. Each tile can be used once, with +, −, × and exact division.",
    "Big numbers: 25, 50, 75, 100. Small numbers: 1–9, at most two of each.",
    "An exact answer earns 10 points. Within 5 earns 7; within 10 earns 5.",
  ];
  $("rules-text").replaceChildren(...paragraphs.map((text) => {
    const p = document.createElement("p"); p.textContent = text; return p;
  }));
}

function render(next) {
  const previousPhase = state.phase;
  state = next;
  configureMode();
  const words = mode === "words";
  const count = words ? (state.letter_count || Number($("letter-count").value)) : 6;
  $("tiles").classList.toggle("numbers", !words);
  // Wrap larger letter rounds without shrinking tiles to unreadable sizes.
  $("tiles").style.gridTemplateColumns = words ? `repeat(${Math.min(count, 9)}, minmax(0, 1fr))` : "";
  $("tiles").replaceChildren(...Array.from({ length: count }, (_, i) => {
    const tile = document.createElement("span");
    tile.className = `tile${state.tiles[i] === undefined ? " blank" : ""}`;
    tile.textContent = state.tiles[i] ?? "·";
    return tile;
  }));
  $("draw-controls").hidden = state.phase !== "selecting";
  $("answer-form").hidden = state.phase !== "playing";
  $("empty-state").hidden = state.phase !== "idle";
  $("results").hidden = state.phase !== "finished";
  $("target-panel").hidden = words || state.phase === "idle";
  $("target").textContent = state.target ?? "—";
  $("new-round").innerHTML = state.phase === "idle" ? 'Start round <span aria-hidden="true">→</span>' : 'New round <span aria-hidden="true">↻</span>';
  const instructions = {
    idle: "Choose your settings, then start a round.",
    selecting: translated(`Choose a vowel or consonant. ${count - state.tiles.length} tiles to go.`, `${count - state.tiles.length} حرف دیگر انتخاب کنید.`),
    playing: words ? translated("The letters are yours. Find the longest word you can.", "با این حروف بلندترین واژه را پیدا کنید.") : "Make the target using some or all of your numbers.",
    finished: translated("Nicely played. Ready for another?", "این دور تمام شد. آمادهٔ دور بعدی هستید؟"),
  };
  $("instruction").textContent = instructions[state.phase];
  if (state.phase === "playing" && deadline && Date.now() >= deadline) {
    $("instruction").textContent = translated("Time’s up! Declare your answer when you’re ready.", "زمان تمام شد! واژهٔ خود را بنویسید.");
  }
  if (state.phase === "playing" && previousPhase !== "playing") startTimer();
  if (state.phase === "finished") {
    clearInterval(timer);
    showResult();
  }
  if (state.error) {
    $("feedback").textContent = state.error;
    $("feedback").hidden = false;
  }
}

function showResult() {
  const result = state.result;
  $("score").textContent = translated(`${result.score} ${result.score === 1 ? "point" : "points"}`, `${result.score} امتیاز`);
  $("result-detail").replaceChildren();
  if (mode === "words") {
    for (const answer of result.answers) {
      const chip = document.createElement("span");
      chip.className = `answer-chip${answer.valid ? "" : " invalid"}`;
      chip.textContent = `${answer.valid ? "✓" : "×"} ${answer.word}`;
      $("result-detail").append(chip);
    }
    if (!result.answers.length) $("result-detail").textContent = translated("No word declared this round.", "در این دور واژه‌ای ثبت نشد.");
  } else {
    $("result-detail").textContent = result.is_valid
      ? `${result.answer} = ${result.value}. ${result.distance === 0 ? "Right on target!" : `${result.distance} away from the target.`}`
      : "No calculation declared this round.";
  }
  $("solutions").replaceChildren();
  $("solution-status").textContent = translated("Finding the best possibilities…", "در حال یافتن بهترین واژه‌ها…");
}

async function finish(answer) {
  render(await request("submit", { answer }));
  if (state.phase !== "finished") return;
  let solution;
  try {
    solution = await request("solve");
  } catch (error) {
    $("solution-status").textContent = translated("The solver could not finish this round. You can start a new round.", "جست‌وجوی واژه‌ها کامل نشد. می‌توانید دور تازه‌ای شروع کنید.");
    throw error;
  }
  if (mode === "words") {
    $("solution-status").textContent = solution.length ? translated(`The longest possible words have ${solution.length} letters.`, `بلندترین واژه‌ها ${solution.length} حرف دارند.`) : translated("No dictionary word can be made from this draw.", "با این حروف واژه‌ای در واژه‌نامه پیدا نشد.");
    $("solutions").textContent = solution.words.join(" · ");
  } else {
    $("solution-status").textContent = `${solution.is_complete ? "Best solution" : "Best found (search time limited)"}: ${solution.best_value}, ${solution.best_distance} from the target.`;
    for (const expression of solution.expressions) {
      const code = document.createElement("code");
      code.textContent = `${expression} = ${solution.best_value}`;
      $("solutions").append(code);
    }
  }
}

async function newRound() {
  resetTimer();
  $("answer").value = "";
  const next = await request("new", { mode, language: $("word-language").value, letter_count: Number($("letter-count").value), big_count: Number($("big-count").value) });
  state = { phase: "idle", tiles: [] };
  render(next);
  $("round-tag").textContent = `ROUND ${String(++round).padStart(2, "0")} · ${farsiRound() ? "فارسی" : mode.toUpperCase()}`;
}

$("new-round").addEventListener("click", () => run(newRound));
for (const nextMode of ["words", "numbers"]) {
  $(`${nextMode}-mode`).addEventListener("click", () => run(async () => {
    if (mode === nextMode) return;
    mode = nextMode;
    configureMode();
    await newRound();
  }));
}
for (const [id, kind] of [["vowel", "v"], ["consonant", "c"], ["draw-letter", "letter"]]) {
  $(id).addEventListener("click", () => run(async () => render(await request("draw", { kind }))));
}
$("fill").addEventListener("click", () => run(async () => render(await request("fill"))));
$("word-language").addEventListener("change", () => run(newRound));
$("answer-form").addEventListener("submit", (event) => {
  event.preventDefault();
  run(() => finish($("answer").value));
});
$("skip").addEventListener("click", () => run(() => finish("")));
$("retry").addEventListener("click", () => location.reload());
$("duration").addEventListener("change", () => {
  if (["idle", "selecting"].includes(state.phase)) resetTimer();
});

try {
  worker = new Worker(new URL("./worker.js", import.meta.url), { type: "module" });
  worker.onmessage = ({ data }) => {
    const request = pending.get(data.id);
    if (!request) return;
    clearTimeout(request.timeout);
    pending.delete(data.id);
    if (data.error) request.reject(new Error(data.error));
    else request.resolve(data.result);
  };
  worker.onerror = (event) => fatal(new Error(event.message || "Browser worker failed."));
  await request("init");
  configureMode();
  resetTimer();
  render(state);
  $("loading").hidden = true;
  $("app").hidden = false;
} catch (error) { fatal(error); }
