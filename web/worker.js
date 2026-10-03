// Python owns the game. This worker only loads it and carries JSON messages.
let dispatch;
let queue = Promise.resolve();

async function checkedFetch(path) {
  const response = await fetch(new URL(path, self.location.href));
  if (!response.ok) throw new Error(`Could not load ${path} (${response.status}).`);
  return response;
}

async function initialize() {
  const config = await (await checkedFetch("./runtime-config.json")).json();
  const indexURL = `https://cdn.jsdelivr.net/pyodide/v${config["pyodide-version"]}/full/`;
  const { loadPyodide } = await import(`${indexURL}pyodide.mjs`);
  const pyodide = await loadPyodide({ indexURL });
  if (pyodide.version !== config["pyodide-version"]) throw new Error("Pyodide version mismatch.");
  const pythonVersion = pyodide.runPython("import sys; '.'.join(map(str, sys.version_info[:2]))");
  if (pythonVersion !== config["python-version"]) throw new Error("Python version mismatch.");
  const archive = await (await checkedFetch("./python/quiz_games.zip")).arrayBuffer();
  pyodide.unpackArchive(archive, "zip", { extractDir: "/app" });
  pyodide.runPython("import sys; sys.path.insert(0, '/app')\nfrom countdown.browser import BrowserGame\ngame = BrowserGame()");
  dispatch = pyodide.runPython("game.dispatch");
  return { ready: true };
}

self.onmessage = ({ data }) => {
  queue = queue.then(async () => {
    try {
      const result = data.action === "init"
        ? await initialize()
        : JSON.parse(dispatch(JSON.stringify({ action: data.action, args: data.args })));
      self.postMessage({ id: data.id, result });
    } catch (error) {
      self.postMessage({ id: data.id, error: String(error.message || error) });
    }
  });
};
