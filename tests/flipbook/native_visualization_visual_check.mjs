#!/usr/bin/env node
/*
 * Visual smoke check for the native Flipbook Molstar view.
 *
 * This complements native_visualization_parity_check.mjs by inspecting the
 * rendered canvas/screenshot rather than only control diagnostics.
 */

import { readFile, mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { basename, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import process from "node:process";

function argValue(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : "";
}

function fail(message) {
  console.error(`FAIL ${message}`);
  process.exitCode = 1;
}

function pass(message) {
  console.log(`PASS ${message}`);
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
  pass(message);
}

async function loadPlaywright() {
  try {
    return await import("playwright");
  } catch (_error) {
    throw new Error("Playwright is required for the native visualization visual check.");
  }
}

function parseManifestText(text) {
  const parsed = JSON.parse(text);
  if (parsed?.schemaVersion === "flipbook-molstar-viewer/v1") {
    return parsed;
  }
  const payload = parsed?.item_data || parsed?.data || parsed?.contents || parsed?.content;
  if (typeof payload === "string") {
    const nested = JSON.parse(payload);
    if (nested?.schemaVersion === "flipbook-molstar-viewer/v1") {
      return nested;
    }
  }
  throw new Error("Manifest file does not contain a flipbook-molstar-viewer/v1 payload.");
}

async function loadManifestFile(path) {
  return parseManifestText(await readFile(path, "utf8"));
}

function withManifestDefaults(manifest) {
  return {
    ...manifest,
    selectedResidueMarker: {
      ...(manifest.selectedResidueMarker || {}),
      enabledDefault: false
    },
    flipbookReference: {
      ...(manifest.flipbookReference || {}),
      tilePaddingFactor: Number(manifest.flipbookReference?.tilePaddingFactor ?? 1.55)
    }
  };
}

async function writeManifestHarness(manifest, sourcePath) {
  const dir = await mkdtemp(`${tmpdir()}/flipbook-molstar-visual-check-`);
  const staticScript = resolve("config/plugins/visualizations/flipbook_molstar/static/script.js");
  const htmlPath = resolve(dir, "manifest_harness.html");
  const incoming = JSON.stringify({ manifest: withManifestDefaults(manifest) }).replace(/</g, "\\u003c");
  const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Flipbook Molstar manifest visual check</title>
</head>
<body>
  <div id="app"></div>
  <script>
    document.getElementById("app").dataset.incoming = ${JSON.stringify(incoming)};
    document.title = ${JSON.stringify(`Flipbook Molstar visual check: ${basename(sourcePath)}`)};
  </script>
  <script src="${pathToFileURL(staticScript).href}"></script>
</body>
</html>`;
  await writeFile(htmlPath, html, "utf8");
  return `${pathToFileURL(htmlPath).href}?marker=0`;
}

async function diagnostics(frame) {
  const text = await frame.getByTestId("molstar-diagnostics").textContent();
  return JSON.parse(text || "{}");
}

async function waitForNativeViewer(page) {
  const start = Date.now();
  const timeoutMs = 30000;
  while (Date.now() - start < timeoutMs) {
    const scopes = [page, ...page.frames().filter((frame) => frame !== page.mainFrame())];
    for (const scope of scopes) {
      const report = scope.getByTestId("molstar-report");
      const reportCount = await report.count().catch(() => 0);
      if (!reportCount) {
        continue;
      }
      const canvas = scope.locator("canvas");
      const canvasCount = await canvas.count().catch(() => 0);
      if (!canvasCount) {
        continue;
      }
      await report.waitFor({ state: "visible", timeout: 5000 });
      await canvas.waitFor({ state: "visible", timeout: 5000 });
      return scope;
    }
    await page.waitForTimeout(250);
  }
  throw new Error("native Molstar viewer did not appear in the page or any Galaxy visualization iframe");
}

function parseNetscapeCookies(text) {
  const cookies = [];
  for (const line of text.split(/\r?\n/)) {
    if (!line || line.startsWith("# ") || line.startsWith("# Netscape") || line.startsWith("# https") || line.startsWith("# This")) {
      continue;
    }
    const httpOnly = line.startsWith("#HttpOnly_");
    const rawLine = httpOnly ? line.replace("#HttpOnly_", "") : line;
    const parts = rawLine.split("\t");
    if (parts.length < 7) {
      continue;
    }
    const [domain, , path, secure, expires, name, value] = parts;
    cookies.push({
      name,
      value,
      domain,
      path,
      expires: Number(expires),
      httpOnly,
      secure: secure === "TRUE",
      sameSite: "Lax"
    });
  }
  return cookies;
}

async function waitForReady(page, frame) {
  const timeoutMs = 30000;
  const start = Date.now();
  let last = null;
  while (Date.now() - start < timeoutMs) {
    last = await diagnostics(frame);
    if (
      last.schemaVersion === "flipbook-molstar-viewer/v1"
      && last.loadedAllSlices === true
      && last.liveTransforms === true
      && last.presentation?.layout === "tiled"
      && last.focusSphere?.radius
    ) {
      await page.waitForTimeout(1600);
      return last;
    }
    await page.waitForTimeout(250);
  }
  throw new Error(`native Molstar viewer did not reach a ready tiled state; last diagnostics: ${JSON.stringify(last, null, 2)}`);
}

async function canvasVisualStats(frame) {
  return frame.locator("canvas").evaluate((canvas) => {
    const width = canvas.width;
    const height = canvas.height;
    const sample = document.createElement("canvas");
    sample.width = width;
    sample.height = height;
    const ctx = sample.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(canvas, 0, 0);
    const data = ctx.getImageData(0, 0, width, height).data;
    const stride = 2;
    const binSize = 6;
    const bins = new Array(Math.ceil(width / binSize)).fill(0);
    let nonWhitePixels = 0;
    let moleculePixels = 0;
    const axisCutX = Math.floor(width * 0.18);
    const axisCutY = Math.floor(height * 0.72);
    const edgeIgnore = 8;

    for (let y = 0; y < height; y += stride) {
      for (let x = 0; x < width; x += stride) {
        if (x < edgeIgnore || x > width - edgeIgnore || y < edgeIgnore || y > height - edgeIgnore) {
          continue;
        }
        const offset = ((y * width) + x) * 4;
        const r = data[offset];
        const g = data[offset + 1];
        const b = data[offset + 2];
        const a = data[offset + 3];
        if (a < 24) {
          continue;
        }
        const distanceFromWhite = Math.abs(255 - r) + Math.abs(255 - g) + Math.abs(255 - b);
        const isNonWhite = distanceFromWhite > 45;
        if (!isNonWhite) {
          continue;
        }
        nonWhitePixels += 1;
        const inLowerLeftAxis = x < axisCutX && y > axisCutY;
        if (inLowerLeftAxis) {
          continue;
        }
        moleculePixels += 1;
        bins[Math.floor(x / binSize)] += 1;
      }
    }

    const activeBins = bins.map((count, index) => ({ count, index })).filter((bin) => bin.count >= 8);
    const clusters = [];
    for (const bin of activeBins) {
      const last = clusters[clusters.length - 1];
      if (!last || bin.index - last.endBin > 4) {
        clusters.push({ startBin: bin.index, endBin: bin.index, pixelCount: bin.count });
      } else {
        last.endBin = bin.index;
        last.pixelCount += bin.count;
      }
    }
    const visualClusters = clusters
      .map((cluster) => ({
        startX: cluster.startBin * binSize,
        endX: Math.min(width, (cluster.endBin + 1) * binSize),
        width: Math.min(width, (cluster.endBin + 1) * binSize) - (cluster.startBin * binSize),
        pixelCount: cluster.pixelCount
      }))
      .filter((cluster) => cluster.width >= 18 && cluster.pixelCount >= 55);

    return {
      width,
      height,
      nonWhitePixels,
      moleculePixels,
      nonWhiteRatio: nonWhitePixels / Math.max(1, (width / stride) * (height / stride)),
      clusterCount: visualClusters.length,
      clusters: visualClusters
    };
  });
}

async function waitForCanvasVisualStats(page, frame, expectedClusters) {
  const timeoutMs = 30000;
  const start = Date.now();
  let last = null;
  while (Date.now() - start < timeoutMs) {
    last = await canvasVisualStats(frame);
    if (last.nonWhitePixels > 600 && last.moleculePixels > 400 && last.clusterCount >= expectedClusters) {
      return last;
    }
    await page.waitForTimeout(500);
  }
  throw new Error(`Molstar canvas did not reach a nonblank tiled molecular draw state; last visual stats: ${JSON.stringify(last)}`);
}

async function main() {
  const manifestPath = argValue("--manifest") || process.env.FLIPBOOK_MOLSTAR_MANIFEST;
  const cookieFile = argValue("--cookie-file") || process.env.RMSX_GALAXY_COOKIE_FILE;
  let url = argValue("--url") || process.env.FLIPBOOK_MOLSTAR_VIS_URL;
  if (manifestPath) {
    url = await writeManifestHarness(await loadManifestFile(manifestPath), manifestPath);
  }
  if (!url) {
    throw new Error("Provide --url, --manifest, FLIPBOOK_MOLSTAR_VIS_URL, or FLIPBOOK_MOLSTAR_MANIFEST for a Flipbook Molstar visualization.");
  }
  const screenshotPath = resolve(argValue("--screenshot") || "/private/tmp/flipbook_molstar_visual_check.png");
  const minClustersArg = Number(argValue("--min-clusters") || 0);

  const { chromium } = await loadPlaywright();
  const browser = await chromium.launch({
    headless: process.env.HEADLESS !== "0",
    args: [
      "--ignore-gpu-blocklist",
      "--enable-unsafe-swiftshader",
      "--use-gl=angle",
      "--use-angle=swiftshader"
    ]
  });

  const page = await browser.newPage({ viewport: { width: 1440, height: 950 } });
  if (cookieFile) {
    await page.context().addCookies(parseNetscapeCookies(await readFile(cookieFile, "utf8")));
  }
  try {
    await page.goto(url, { waitUntil: "domcontentloaded" });
    const frame = await waitForNativeViewer(page);
    const diag = await waitForReady(page, frame);
    const expectedClusters = minClustersArg || Math.max(1, diag.visibleSlices?.length || diag.sliceCount || 1);
    const stats = await waitForCanvasVisualStats(page, frame, expectedClusters);
    await frame.getByTestId("molstar-report").screenshot({ path: screenshotPath });

    assert(stats.nonWhitePixels > 600, "Molstar canvas is nonblank");
    assert(stats.moleculePixels > 400, "Molstar canvas contains molecule-colored pixels outside the orientation axes");
    assert(stats.clusterCount >= expectedClusters, `tiled Flipbook view shows at least ${expectedClusters} separated visual clusters`);
    const edgeMargin = stats.width * 0.02;
    const clustersInsideMargins = stats.clusters.every((cluster) => cluster.startX > edgeMargin && cluster.endX < stats.width - edgeMargin);
    if (!clustersInsideMargins) {
      throw new Error(`tiled Flipbook clusters are framed inside the canvas margins; clusters: ${JSON.stringify(stats.clusters)}`);
    }
    pass("tiled Flipbook clusters are framed inside the canvas margins");
    assert(diag.presentation?.marker === false, "selected-residue marker is disabled in the default visual state");
    assert(diag.presentation?.tiledPlacement?.slot > 0, "tiled placement diagnostics expose a positive slot size");
    assert(diag.presentation?.tiledPlacement?.cameraExtraRadius > 0, "camera framing diagnostics expose extra visual margin");
    pass(`screenshot written to ${screenshotPath}`);
    pass(`visual stats ${JSON.stringify({ clusterCount: stats.clusterCount, clusters: stats.clusters, nonWhitePixels: stats.nonWhitePixels, moleculePixels: stats.moleculePixels })}`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  fail(error.message);
});
