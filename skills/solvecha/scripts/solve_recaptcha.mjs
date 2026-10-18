#!/usr/bin/env node
// Solve a reCAPTCHA v2 image challenge, or report Google's verdict. Needs Node.js 18+
// and SOLVECHA_API_KEY.
//
//   node solve_recaptcha.mjs --task "Select all images with buses" --grid 3x3 --image grid.png
//   node solve_recaptcha.mjs --report JOB_ID --verdict accepted --grid 3x3
import { readFile } from "node:fs/promises";
import { parseArgs } from "node:util";

const API = (process.env.SOLVECHA_API_URL ?? "https://api.solvecha.com").replace(/\/$/, "");
const ERRORS = {
  9: "temporary error or unsolvable image: retry once with a fresh screenshot",
  10: "invalid request: check task, grid and image",
  11: "rate limit: wait 30 seconds",
  15: "wrong or missing API key",
  16: "out of credit: ask the user to top up; do not retry",
};

const { values } = parseArgs({
  options: {
    task: { type: "string" }, grid: { type: "string" }, image: { type: "string", multiple: true },
    timeout: { type: "string", default: "45" }, report: { type: "string" }, verdict: { type: "string" },
  },
});
const key = process.env.SOLVECHA_API_KEY;
const fail = (message) => { console.error(JSON.stringify({ error: message })); process.exit(1); };
if (!key) fail("SOLVECHA_API_KEY is not set. Create a key at https://solvecha.com/dashboard");

async function call(method, path, body) {
  const response = await fetch(API + path, {
    method,
    headers: { Authorization: `Bearer ${key}`, ...(body ? { "Content-Type": "application/json" } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  return response.json().catch(() => ({ error: 9, message: `HTTP ${response.status}` }));
}

if (values.report) {
  if (!values.verdict || !values.grid) fail("--report needs --verdict and --grid");
  console.log(JSON.stringify(await call("POST", "/v1/feedback", { job_id: values.report, verdict: values.verdict, grid: values.grid })));
  process.exit(0);
}
if (!values.task || !values.grid || !values.image?.length) fail("--task, --grid and --image are required");
const images = await Promise.all(values.image.map(async (file) => (await readFile(file)).toString("base64")));
const job = await call("POST", "/v1/recognition/recaptcha", { task: values.task, grid: values.grid, image_data: images });
if (!("data" in job)) fail(`Solvecha error ${job.error}: ${ERRORS[job.error] ?? job.message}`);
const deadline = Date.now() + Number(values.timeout) * 1000;
while (Date.now() < deadline) {
  await new Promise((resolve) => setTimeout(resolve, 1000));
  const answer = await call("GET", `/v1/recognition/recaptcha?id=${encodeURIComponent(job.data)}`);
  if (answer.error === 14) continue; // still working
  if ("data" in answer) {
    const tiles = answer.data.flatMap((picked, i) => (picked ? [i + 1] : []));
    console.log(JSON.stringify({ job_id: job.data, selected_tiles: tiles, answer: answer.data }));
    process.exit(0);
  }
  fail(`Solvecha error ${answer.error}: ${ERRORS[answer.error] ?? answer.message}`);
}
fail(`no answer in ${values.timeout} seconds (job ${job.data})`);
