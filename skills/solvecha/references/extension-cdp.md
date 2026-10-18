# Solvecha extension in a browser the agent controls

The extension clicks reCAPTCHA image challenges by itself. The agent only needs a Chromium with the extension and a debugging port.

1. Download https://solvecha.com/download/extension/chrome and unzip it, for example to `~/solvecha-extension`.
2. Start Chromium or Chrome for Testing with a separate profile (use `xvfb-run` on a server, extensions need a headed browser):
   ```bash
   chromium --user-data-dir="$HOME/.agent-chrome" --remote-debugging-port=9222 \
     --load-extension="$HOME/solvecha-extension" --no-first-run --no-default-browser-check
   ```
3. Open the extension options once and save the API key.
4. Connect the agent to `http://127.0.0.1:9222`:
   - Hermes Agent: `/browser connect` in the CLI.
   - OpenClaw: a browser profile with `cdpUrl: "http://127.0.0.1:9222"`.
   - Browser Use: `Browser(cdp_url="http://127.0.0.1:9222")`.

Google Chrome 137 and later ignore `--load-extension`; use Chromium or Chrome for Testing. Chrome 136 and later ignore the debugging port on the default profile, so always set `--user-data-dir`.
