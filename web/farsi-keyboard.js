// Standard Persian (ISIRI 9147) physical key positions, independent of OS layout.
// Reference: https://unicode.org/cldr/charts/43/keyboards/layouts/fa.html
const base = {
  KeyQ: "ض", KeyW: "ص", KeyE: "ث", KeyR: "ق", KeyT: "ف", KeyY: "غ",
  KeyU: "ع", KeyI: "ه", KeyO: "خ", KeyP: "ح", BracketLeft: "ج", BracketRight: "چ",
  KeyA: "ش", KeyS: "س", KeyD: "ی", KeyF: "ب", KeyG: "ل", KeyH: "ا",
  KeyJ: "ت", KeyK: "ن", KeyL: "م", Semicolon: "ک", Quote: "گ",
  KeyZ: "ظ", KeyX: "ط", KeyC: "ز", KeyV: "ر", KeyB: "ذ", KeyN: "د", KeyM: "پ",
  Comma: "و", Period: ".", Slash: "/", Space: " ",
  Digit1: "۱", Digit2: "۲", Digit3: "۳", Digit4: "۴", Digit5: "۵",
  Digit6: "۶", Digit7: "۷", Digit8: "۸", Digit9: "۹", Digit0: "۰",
  Minus: "-", Equal: "=", Backslash: "\\", Backquote: "\u200d",
};
const shifted = {
  KeyQ: "ْ", KeyW: "ٌ", KeyE: "ٍ", KeyR: "ً", KeyT: "ُ", KeyY: "ِ",
  KeyU: "َ", KeyI: "ّ", KeyO: "]", KeyP: "[", BracketLeft: "}", BracketRight: "{",
  KeyA: "ؤ", KeyS: "ئ", KeyD: "ی", KeyF: "إ", KeyG: "أ", KeyH: "آ",
  KeyJ: "ة", KeyK: "»", KeyL: "«", Semicolon: ":", Quote: "؛",
  KeyZ: "ک", KeyX: "ٓ", KeyC: "ژ", KeyV: "ٰ", KeyB: "\u200c", KeyN: "ٔ", KeyM: "ء",
  Comma: ">", Period: "<", Slash: "؟", Space: "\u200c",
  Digit1: "!", Digit2: "٬", Digit3: "٫", Digit4: "﷼", Digit5: "٪",
  Digit6: "×", Digit7: "،", Digit8: "*", Digit9: ")", Digit0: "(",
  Minus: "ـ", Equal: "+", Backslash: "|", Backquote: "÷",
};

// Virtual keyboards may omit physical codes. In that case only Latin letters
// are mapped by QWERTY character; Persian text, punctuation, and paste stay intact.
function latinFallback(text) {
  return text.replace(/[a-z]/gi, (letter) => base[`Key${letter.toUpperCase()}`]);
}

export function attachFarsiKeyboard(input, enabled) {
  function insert(text) {
    const start = input.selectionStart;
    const end = input.selectionEnd;
    if (input.maxLength >= 0 && input.value.length - (end - start) + text.length > input.maxLength) return;
    // Native editing retains caret/selection behavior and the browser undo stack.
    // setRangeText is the fallback for browsers without the legacy editing API.
    if (typeof document.execCommand !== "function" || !document.execCommand("insertText", false, text)) {
      input.setRangeText(text, start, end, "end");
      input.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: text }));
    }
  }

  input.addEventListener("keydown", (event) => {
    if (!enabled() || event.isComposing || event.keyCode === 229 ||
        event.ctrlKey || event.metaKey || event.altKey) return;
    // Already-Persian input (including IMEs and different native Persian layouts)
    // is entered normally instead of being mapped a second time.
    if (/^[\u0600-\u06ff\u200c\u200d]$/u.test(event.key)) return;
    const text = (event.shiftKey ? shifted : base)[event.code];
    if (text === undefined || text === event.key) return;
    event.preventDefault();
    insert(text);
  });

  input.addEventListener("beforeinput", (event) => {
    if (!enabled() || event.isComposing || !event.cancelable ||
        event.inputType !== "insertText" || !event.data) return;
    const text = latinFallback(event.data);
    if (text === event.data) return;
    event.preventDefault();
    insert(text);
  });
}
