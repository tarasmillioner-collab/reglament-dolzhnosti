// Walk the OpenShorts dashboard through the AI Shorts wizard once per script,
// exactly as a person would: pick the script, upload the actor photo, press
// Generate, watch the logs, land on the result. The whole session is recorded
// and every step is screenshotted.
//
//   NODE_PATH=$(npm root -g) node drive_dashboard.cjs <scripts_aligned.json> <assets_dir> <out_dir>
//
// Env: DASHBOARD_URL (default http://localhost:8000), CHROMIUM_PATH (optional),
//      OPENSHORTS_OUTPUT (the backend's output dir, for the preview transcode below).
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { chromium } = require('playwright');

const [scriptsPath, assetsDir, outDir] = process.argv.slice(2);
const BASE = process.env.DASHBOARD_URL || 'http://localhost:8000';
const data = JSON.parse(fs.readFileSync(scriptsPath, 'utf8'));
fs.mkdirSync(path.join(outDir, 'screens'), { recursive: true });
fs.mkdirSync(path.join(outDir, 'recording'), { recursive: true });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || undefined,
    args: ['--autoplay-policy=no-user-gesture-required'],
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
    recordVideo: { dir: path.join(outDir, 'recording'), size: { width: 1440, height: 900 } },
  });
  // Same state the dashboard leaves behind after an analysis: the app view and
  // the cached analysis + scripts (written by hand from the goPure briefs, in
  // place of the Gemini step), with the Higgsfield video mode remembered.
  await context.addInitScript((cache) => {
    if (sessionStorage.getItem('seeded')) return;
    localStorage.setItem('openshorts_skip_landing', '1');
    localStorage.setItem('saasshorts_cache', JSON.stringify({ ...cache, timestamp: Date.now() }));
    sessionStorage.setItem('seeded', '1');
  }, { url: '', analysis: data.analysis, webResearch: null, scripts: data.scripts, videoMode: 'higgsfield' });

  // Playwright's Chromium ships without H.264/AAC, so the result player would
  // stay grey in the recording. Serve the browser a VP8 copy of the final mp4
  // (the mp4 itself is what gets published).
  if (process.env.OPENSHORTS_OUTPUT) {
    await context.route(/\/videos\/saas_[^/]+\/[^/?]+\.mp4/, async (route) => {
      const rel = decodeURIComponent(new URL(route.request().url()).pathname.replace(/^\/videos\//, ''));
      const src = path.join(process.env.OPENSHORTS_OUTPUT, rel);
      const preview = src.replace(/\.mp4$/, '.preview.webm');
      if (!fs.existsSync(preview)) {
        execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', src, '-vf', 'scale=540:-2',
          '-c:v', 'libvpx', '-deadline', 'realtime', '-cpu-used', '8', '-b:v', '1500k',
          '-c:a', 'libvorbis', preview]);
      }
      await route.fulfill({ status: 200, contentType: 'video/webm', body: fs.readFileSync(preview) });
    });
  }

  const page = await context.newPage();
  const shot = async (name, opts = {}) => {
    await sleep(400);
    await page.screenshot({ path: path.join(outDir, 'screens', `${name}.png`), ...opts });
    console.log(`screenshot ${name}`);
  };
  const results = [];

  await page.goto(`${BASE}/#app`, { waitUntil: 'networkidle' });
  await sleep(1500);
  await shot('00_app_home');

  for (let i = 0; i < data.scripts.length; i++) {
    const script = data.scripts[i];
    const n = String(i + 1);
    if (i > 0) {
      await page.reload({ waitUntil: 'networkidle' });
      await sleep(1000);
    }
    await page.getByRole('button', { name: /ai shorts/i }).first().click();
    await page.getByText('Configure video', { exact: false }).first().waitFor();
    await sleep(800);
    if (i === 0) await shot('01_analysis_scripts', { fullPage: true });

    await page.getByText(script.title, { exact: true }).first().click();
    await sleep(600);
    await page.getByRole('button', { name: /configure video/i }).click();
    await page.getByText(/configure video/i).first().waitFor();

    const upload = page.waitForResponse((r) => r.url().includes('/api/saasshorts/actor-upload'));
    await page.locator('input[type=file][accept="image/*"]').first()
      .setInputFiles(path.join(assetsDir, script.asset_id, 'actor.png'));
    await upload;
    await sleep(1200);
    await shot(`${n}a_configure`, { fullPage: true });

    const generate = page.waitForResponse((r) => r.url().includes('/api/saasshorts/generate'));
    await page.getByRole('button', { name: /generate video/i }).click();
    const { job_id: jobId } = await (await generate).json();
    console.log(`[${script.asset_id}] job ${jobId}`);
    await sleep(6000);
    await shot(`${n}b_generating`);

    await page.getByText(/your short is ready/i).waitFor({ timeout: 10 * 60 * 1000 });
    await sleep(7000);
    await shot(`${n}c_result`);
    await page.mouse.wheel(0, 700);
    await sleep(800);
    await shot(`${n}d_result_details`);

    const status = await (await page.request.get(`${BASE}/api/saasshorts/status/${jobId}`)).json();
    results.push({ asset_id: script.asset_id, title: script.title, job_id: jobId,
                   video_url: status.result.video_url, duration: status.result.duration,
                   cost: status.result.cost_estimate, logs: status.logs });
    await sleep(3000); // let the recording show the finished short playing
  }

  const video = page.video();
  await context.close();
  await browser.close();
  if (video) fs.renameSync(await video.path(), path.join(outDir, 'recording', 'dashboard.webm'));
  fs.writeFileSync(path.join(outDir, 'results.json'), JSON.stringify(results, null, 2));
  console.log('done');
})().catch((e) => { console.error(e); process.exit(1); });
