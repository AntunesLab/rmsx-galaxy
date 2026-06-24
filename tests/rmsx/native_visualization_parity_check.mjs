#!/usr/bin/env node
/*
 * Browser parity smoke check for the native RMSX Molstar Galaxy visualization.
 *
 * Usage:
 *   node tests/rmsx/native_visualization_parity_check.mjs \
 *     --url "http://localhost:9090/visualizations/display?visualization=rmsx_molstar&dataset_id=..."
 *
 * Requires Playwright to be available in the Node environment. This script is
 * intentionally separate from the ordinary unit smoke tests because it needs a
 * running local Galaxy/Planemo visualization page.
 */

import process from "node:process";
import { readFile } from "node:fs/promises";

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
  } catch (error) {
    throw new Error(
      "Playwright is required for the native visualization parity check. " +
      "Install it in your local test environment or run this from an environment that already provides Playwright."
    );
  }
}

async function diagnostics(frame) {
  const text = await frame.getByTestId("molstar-diagnostics").textContent();
  return JSON.parse(text || "{}");
}

async function selectValue(locator, value) {
  await locator.selectOption(value);
}

async function fillAndCommit(locator, value) {
  await locator.fill(String(value));
  await locator.press("Enter").catch(() => {});
}

async function openPanel(frame, testId) {
  const panel = frame.getByTestId(testId);
  const isOpen = await panel.evaluate((element) => Boolean(element.open));
  if (!isOpen) {
    await panel.locator("summary").click();
  }
}

async function waitForDiagnostic(page, frame, predicate, description) {
  const timeoutMs = 10000;
  const start = Date.now();
  let last = null;
  while (Date.now() - start < timeoutMs) {
    last = await diagnostics(frame);
    if (predicate(last)) {
      pass(description);
      return last;
    }
    await page.waitForTimeout(250);
  }
  throw new Error(`${description}; last diagnostics: ${JSON.stringify(last, null, 2)}`);
}

async function waitForNativeViewer(page) {
  async function findViewer(timeoutMs) {
    const start = Date.now();
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

  try {
    return await findViewer(30000);
  } catch (error) {
    await page.reload({ waitUntil: "domcontentloaded" });
    return await findViewer(30000);
  }
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

async function main() {
  const url = argValue("--url") || process.env.RMSX_MOLSTAR_VIS_URL;
  const cookieFile = argValue("--cookie-file") || process.env.RMSX_GALAXY_COOKIE_FILE;
  if (!url) {
    throw new Error("Provide --url or RMSX_MOLSTAR_VIS_URL for a running Galaxy RMSX Molstar visualization.");
  }

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
    const frameLocator = await waitForNativeViewer(page);

    const requiredTestIds = [
      "molstar-control-panels",
      "molstar-controls-sidebar",
      "molstar-panel-layout",
      "molstar-panel-appearance",
      "molstar-panel-scale",
      "molstar-panel-residue",
      "molstar-panel-rotation",
      "molstar-panel-diagnostics",
      "molstar-render-select",
      "molstar-outline-checkbox",
      "molstar-rmsx-legend",
      "molstar-radius-legend",
      "molstar-layout-select",
      "molstar-palette-select",
      "molstar-color-min-number",
      "molstar-color-max-number",
      "molstar-radius-min-number",
      "molstar-radius-max-number",
      "molstar-thickness-range",
      "molstar-reset-scale",
      "molstar-spacing-range",
      "molstar-columns-number",
      "molstar-rotate-sensitivity-range",
      "molstar-local-rotate",
      "molstar-local-rotate-checkbox",
      "molstar-residue-marker-toggle",
      "molstar-residue-marker-checkbox",
      "molstar-diagnostics"
    ];
    for (const testId of requiredTestIds) {
      await frameLocator.getByTestId(testId).waitFor({ state: "attached", timeout: 5000 });
      pass(`control present: ${testId}`);
    }
    const sliceChipCount = await frameLocator.getByTestId("molstar-slice-chip").count();
    assert(sliceChipCount > 0, "slice visibility chips are present");

    let diag = await diagnostics(frameLocator);
    assert(diag.schemaVersion === "rmsx-molstar-viewer/v1", "manifest schema is accepted");
    assert(diag.controls?.accordionControls === true, "sidebar accordion controls are active");
    assert(diag.controls?.compactTabs === false, "native viewer does not expose a tab strip");
    assert(diag.controls?.sidebarLayout === true, "desktop sidebar control layout is active");
    assert(diag.controls?.activeControlPanel === "layout", "layout control panel is active by default");
    assert(diag.controls?.playback === false, "native viewer does not expose playback controls");
    assert(JSON.stringify(diag.controls?.layoutModes) === JSON.stringify(["tiled", "overlay"]), "native viewer exposes tiled and overlay layouts");
    assert(diag.controls?.urlStatePersistence === true, "URL-state persistence is advertised");
    assert(diag.controls?.renderStyle === true, "render style controls are advertised");
    assert(diag.controls?.rotateSensitivity === true, "rotate sensitivity control is advertised");
    assert(diag.stateInitialization?.urlParamsOverrideVisualizationConfig === true, "URL params override Galaxy visualization config state");
    assert(diag.presentation?.layout === "tiled", "tiled is the default native layout");
    assert(diag.loadedAllSlices === true, "native viewer reports all slices loaded");
    assert(diag.liveTransforms === true, "native viewer uses live Molstar transforms");
    assert(Boolean(diag.focusSphere?.radius), "native diagnostics include a camera focus sphere");
    assert(diag.visualMapping?.legend?.elements?.colorBar === true, "native legend includes the active palette color bar");
    assert(diag.visualMapping?.legend?.elements?.radiusLegend === true, "native legend includes the radius scale");
    assert(diag.visualMapping?.legend?.stops?.length === 3, "native legend reports low/mid/high stops");
    assert(diag.visualMapping.legend.stops.every((stop) => /^#[0-9A-F]{6}$/.test(stop.color) && Number.isFinite(stop.radius)), "native legend stops expose color and radius values");
    assert(diag.visibility?.chipCount === diag.sliceCount, "slice visibility chips match slice count");

    const defaultScale = {
      colorMin: diag.visualMapping?.colorMin,
      colorMax: diag.visualMapping?.colorMax,
      radiusMin: diag.visualMapping?.configuredRadiusMin,
      radiusMax: diag.visualMapping?.configuredRadiusMax,
      thickness: diag.visualMapping?.thickness
    };

    await openPanel(frameLocator, "molstar-panel-appearance");
    await selectValue(frameLocator.getByTestId("molstar-render-select"), "soft");
    await waitForDiagnostic(page, frameLocator, (current) => current.renderStyle?.preset === "soft", "render preset control updates diagnostics");
    await frameLocator.getByTestId("molstar-outline-checkbox").setChecked(false);
    await waitForDiagnostic(
      page,
      frameLocator,
      (current) => current.renderStyle?.outline === "off" && current.urlState?.expectedManagedParams?.outline === "0",
      "outline toggle updates diagnostics and URL state"
    );
    await frameLocator.getByTestId("molstar-outline-checkbox").setChecked(true);
    await waitForDiagnostic(page, frameLocator, (current) => current.renderStyle?.outline === "on", "outline toggle restores native outline");

    await openPanel(frameLocator, "molstar-panel-scale");
    await selectValue(frameLocator.getByTestId("molstar-palette-select"), "turbo");
    await waitForDiagnostic(page, frameLocator, (current) => current.palette === "turbo" && current.visualMapping?.legend?.stops?.[2]?.color, "palette switch updates diagnostics and legend");

    await fillAndCommit(frameLocator.getByTestId("molstar-thickness-number"), "1.25");
    await waitForDiagnostic(page, frameLocator, (current) => Math.abs(current.visualMapping?.thickness - 1.25) < 0.001, "thickness updates visual mapping");

    const domain = await diagnostics(frameLocator);
    const nextColorMin = Number((domain.visualMapping.colorMin + 0.1).toFixed(3));
    await fillAndCommit(frameLocator.getByTestId("molstar-color-min-number"), String(nextColorMin));
    await waitForDiagnostic(page, frameLocator, (current) => Math.abs(current.visualMapping?.colorMin - nextColorMin) < 0.001, "color low updates visual mapping");

    await fillAndCommit(frameLocator.getByTestId("molstar-radius-min-number"), "0.8");
    await waitForDiagnostic(page, frameLocator, (current) => current.visualMapping?.radiusMin >= 0.79, "radius low updates visual mapping");

    await frameLocator.getByTestId("molstar-reset-scale").click();
    await waitForDiagnostic(
      page,
      frameLocator,
      (current) => Math.abs(current.visualMapping?.colorMin - defaultScale.colorMin) < 0.001
        && Math.abs(current.visualMapping?.colorMax - defaultScale.colorMax) < 0.001
        && Math.abs(current.visualMapping?.configuredRadiusMin - defaultScale.radiusMin) < 0.001
        && Math.abs(current.visualMapping?.configuredRadiusMax - defaultScale.radiusMax) < 0.001
        && Math.abs(current.visualMapping?.thickness - defaultScale.thickness) < 0.001,
      "reset scale restores color, radius, and thickness defaults"
    );

    await openPanel(frameLocator, "molstar-panel-layout");
    await fillAndCommit(frameLocator.getByTestId("molstar-spacing-number"), "0.35");
    await waitForDiagnostic(page, frameLocator, (current) => Math.abs(current.presentation?.spacing - 0.35) < 0.001, "spacing updates presentation state");

    await fillAndCommit(frameLocator.getByTestId("molstar-columns-number"), "2");
    await waitForDiagnostic(page, frameLocator, (current) => current.presentation?.columns === 2, "columns update presentation state");

    await selectValue(frameLocator.getByTestId("molstar-layout-select"), "overlay");
    await waitForDiagnostic(page, frameLocator, (current) => current.presentation?.layout === "overlay", "overlay layout updates diagnostics");
    await selectValue(frameLocator.getByTestId("molstar-layout-select"), "tiled");
    await waitForDiagnostic(page, frameLocator, (current) => current.presentation?.layout === "tiled", "tiled layout restores diagnostics");

    await openPanel(frameLocator, "molstar-panel-residue");
    await frameLocator.getByTestId("molstar-residue-marker-checkbox").setChecked(true);
    await waitForDiagnostic(page, frameLocator, (current) => current.presentation?.marker === true, "marker toggle enables selected-residue overlay");
    await frameLocator.getByTestId("molstar-residue-marker-checkbox").setChecked(false);
    await waitForDiagnostic(page, frameLocator, (current) => current.presentation?.marker === false, "marker toggle disables selected-residue overlay");

    await openPanel(frameLocator, "molstar-panel-rotation");
    await fillAndCommit(frameLocator.getByTestId("molstar-rotate-sensitivity-number"), "0.7");
    await waitForDiagnostic(page, frameLocator, (current) => Math.abs(current.presentation?.rotationSensitivity - 0.7) < 0.001, "rotate sensitivity updates diagnostics");
    await frameLocator.getByTestId("molstar-local-rotate-checkbox").setChecked(false);
    await waitForDiagnostic(
      page,
      frameLocator,
      (current) => current.presentation?.localDrag === false && current.urlState?.expectedManagedParams?.localDrag === "0",
      "local drag checkbox disables local rotation diagnostics and URL state"
    );
    await frameLocator.getByTestId("molstar-local-rotate-checkbox").setChecked(true);
    await waitForDiagnostic(page, frameLocator, (current) => current.presentation?.localDrag === true, "local drag checkbox restores local rotation diagnostics");

    const viewport = frameLocator.getByTestId("molstar-viewport");
    const box = await viewport.boundingBox();
    if (box) {
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await page.mouse.down();
      await page.mouse.move(box.x + box.width / 2 + 80, box.y + box.height / 2 + 35, { steps: 8 });
      await page.mouse.up();
      await waitForDiagnostic(page, frameLocator, (current) => Boolean(current.lastRotationGesture), "local drag records a rotation gesture");
    } else {
      throw new Error("Molstar viewport bounding box is unavailable.");
    }

    await waitForDiagnostic(
      page,
      frameLocator,
      (current) => current.urlState?.synced === true,
      "managed URL state is synchronized"
    );
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  fail(error.message);
});
