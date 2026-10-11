/**
 * Automated institutional screenshot capture script using Playwright.
 * Captures clean 1440x900 full-page screenshots for docs/screenshots/
 * and high-DPI (2x deviceScaleFactor) cropped panel images for docs/screenshots/crops/
 */
import { chromium } from '@playwright/test'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUT_DIR = path.resolve(__dirname, '..', 'docs', 'screenshots')
const CROPS_DIR = path.resolve(OUT_DIR, 'crops')

async function capture() {
  if (!fs.existsSync(OUT_DIR)) {
    fs.mkdirSync(OUT_DIR, { recursive: true })
  }
  if (!fs.existsSync(CROPS_DIR)) {
    fs.mkdirSync(CROPS_DIR, { recursive: true })
  }

  const browser = await chromium.launch({ headless: true })

  // --------------------------------------------------------------------------
  // Phase 1: Full-Page Screenshots (1x Scale for optimal repo size < 2 MB)
  // --------------------------------------------------------------------------
  console.log('--- Phase 1: Capturing Full-Page Screenshots (1x) ---')
  const context1x = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1.0,
  })
  const page1x = await context1x.newPage()

  console.log('Navigating to http://127.0.0.1:8000 ...')
  await page1x.goto('http://127.0.0.1:8000', { waitUntil: 'domcontentloaded' })
  await page1x.waitForTimeout(600)

  // 1. Initial Monitor resting state (hero populated before scenario fires)
  console.log('1. Capturing 01_monitor_overview.png...')
  await page1x.screenshot({ path: path.join(OUT_DIR, '01_monitor_overview.png') })

  // Speed up to 20x so full stream processes quickly (button has '20×')
  const speed20x = page1x.locator('button', { hasText: /20/ }).first()
  if (await speed20x.count() > 0) {
    await speed20x.click()
  }

  // Wait until all 14 signals arrive in the feed
  console.log('Waiting for all 14 signals in feed...')
  await page1x.waitForFunction(() => {
    return document.querySelectorAll('section[aria-label="Signal Feed"] .cursor-pointer').length >= 14
  }, { timeout: 15000 }).catch(() => console.log('Timeout waiting for 14 signals'))

  const rows = page1x.locator('section[aria-label="Signal Feed"] .cursor-pointer')
  const count = await rows.count()
  console.log(`Feed populated with ${count} signals`)

  if (count > 0) {
    // Select first signal and expand details
    await rows.first().click()
    await page1x.waitForTimeout(400)
    const expandBtn = rows.first().locator('button[aria-label="Expand details"]')
    if (await expandBtn.count() > 0) {
      await expandBtn.first().click()
      await page1x.waitForTimeout(400)
    }
  }

  // 2. Monitor Mid-Replay with Details Drawer
  console.log('2. Capturing 02_monitor_mid_replay_details.png...')
  await page1x.screenshot({ path: path.join(OUT_DIR, '02_monitor_mid_replay_details.png') })

  // 3. Suppressed Rumor State
  console.log('3. Capturing 03_suppressed_rumor.png...')
  const suppBtn = page1x.locator('section[aria-label="Signal Feed"]').getByRole('button', { name: /^Supp/ })
  if (await suppBtn.count() > 0) {
    await suppBtn.click()
    await page1x.waitForTimeout(400)
    const rumorRow = page1x.locator('section[aria-label="Signal Feed"]').getByText(/rumor|whispers|Bank of America|Toyota/i).first()
    if (await rumorRow.count() > 0) {
      await rumorRow.click()
      await page1x.waitForTimeout(300)
    }
  }
  await page1x.screenshot({ path: path.join(OUT_DIR, '03_suppressed_rumor.png') })

  // Switch back to All
  const allBtn = page1x.locator('section[aria-label="Signal Feed"]').getByRole('button', { name: /^All/ })
  if (await allBtn.count() > 0) {
    await allBtn.click()
    await page1x.waitForTimeout(300)
  }

  // 4. Red Sea Scenario Shock (Replay Signal 008)
  console.log('4. Capturing 04_red_sea_scenario.png...')
  const redSeaCard = page1x.locator('#signal-card-sig_replay_008')
  if (await redSeaCard.count() > 0) {
    await redSeaCard.click()
    await page1x.waitForTimeout(800)
  }
  await page1x.screenshot({ path: path.join(OUT_DIR, '04_red_sea_scenario.png') })

  // 5. Active Treemap Shock
  console.log('5. Capturing 06_treemap_active_shock.png...')
  await page1x.screenshot({ path: path.join(OUT_DIR, '06_treemap_active_shock.png') })

  // 6. Scenario Lab
  console.log('6. Capturing 07_scenario_lab.png...')
  const navButtons = page1x.locator('header nav button')
  await navButtons.filter({ hasText: /Scenario/i }).click()
  await page1x.waitForTimeout(800)
  await page1x.screenshot({ path: path.join(OUT_DIR, '07_scenario_lab.png') })

  // 7. OPEC Net-Positive Scenario
  console.log('7. Capturing 05_opec_net_positive.png...')
  const themeSelect = page1x.locator('select')
  if (await themeSelect.count() > 0) {
    await themeSelect.selectOption('oil_price_up')
    await page1x.locator('form button[type="submit"]').click()
    await page1x.waitForTimeout(1000)
  }
  await page1x.screenshot({ path: path.join(OUT_DIR, '05_opec_net_positive.png') })

  // 8. Analyze Text View
  console.log('8. Capturing 08_analyze_result.png...')
  await navButtons.filter({ hasText: /Analyze/i }).click()
  await page1x.waitForTimeout(600)
  const opecPreset = page1x.getByRole('button', { name: /OPEC/i }).first()
  if (await opecPreset.count() > 0) {
    await opecPreset.click()
    await page1x.waitForTimeout(300)
    await page1x.locator('form button[type="submit"]').click()
    await page1x.waitForTimeout(1200)
  }
  await page1x.screenshot({ path: path.join(OUT_DIR, '08_analyze_result.png') })

  // 9. Calibration View
  console.log('9. Capturing 09_calibration_scatter.png...')
  await navButtons.filter({ hasText: /Calibration/i }).click()
  await page1x.waitForTimeout(1000)
  await page1x.screenshot({ path: path.join(OUT_DIR, '09_calibration_scatter.png') })

  await context1x.close()

  // --------------------------------------------------------------------------
  // Phase 2: Cropped Panel Images at 2x Scale (Retina Sharpness for Deck)
  // --------------------------------------------------------------------------
  console.log('--- Phase 2: Capturing 2x Cropped Panels for Deck ---')
  const context2x = await browser.newContext({
    viewport: { width: 1440, height: 1600 },
    deviceScaleFactor: 2.0,
  })
  const page2x = await context2x.newPage()
  await page2x.goto('http://127.0.0.1:8000', { waitUntil: 'domcontentloaded' })
  await page2x.waitForTimeout(600)

  // Speed up to 20x to process stream
  const speed2x = page2x.locator('button', { hasText: /20/ }).first()
  if (await speed2x.count() > 0) {
    await speed2x.click()
  }
  await page2x.waitForFunction(() => {
    return document.querySelectorAll('section[aria-label="Signal Feed"] .cursor-pointer').length >= 14
  }, { timeout: 15000 }).catch(() => console.log('Timeout waiting for 14 signals'))

  // Crop A: stress_red_sea.png (FIRST Red Sea trigger: replay_008, impact 8.8)
  console.log('A. Capturing crops/stress_red_sea.png...')
  const redSeaSignal = page2x.locator('#signal-card-sig_replay_008')
  if (await redSeaSignal.count() > 0) {
    await redSeaSignal.click()
    await page2x.waitForTimeout(800)
  }
  await page2x.evaluate(() => window.scrollTo(0, 0))
  await page2x.waitForTimeout(400)
  const redSeaPanel = page2x.locator('section[aria-label="Scenario Result"] > div').first()
  await redSeaPanel.screenshot({ path: path.join(CROPS_DIR, 'stress_red_sea.png') })

  // Crop B: treemap_active.png (Treemap with Red Sea shock active)
  console.log('B. Capturing crops/treemap_active.png...')
  await page2x.evaluate(() => window.scrollTo(0, 0))
  await page2x.waitForTimeout(400)
  const treemapPanel = page2x.locator('section[aria-label="Exposure Treemap"] > div').first()
  await treemapPanel.screenshot({ path: path.join(CROPS_DIR, 'treemap_active.png') })

  // Crop C: confidence_breakdown.png (Expanded signal row showing confidence factors)
  console.log('C. Capturing crops/confidence_breakdown.png...')
  const signal008Card = page2x.locator('#signal-card-sig_replay_008')
  if (await signal008Card.count() > 0) {
    const expandBtn2x = signal008Card.locator('button[aria-label="Expand details"]')
    if (await expandBtn2x.count() > 0) {
      await expandBtn2x.click()
      await page2x.waitForTimeout(500)
    }
    await signal008Card.scrollIntoViewIfNeeded()
    await signal008Card.screenshot({ path: path.join(CROPS_DIR, 'confidence_breakdown.png') })
  }

  // Crop D: stress_opec.png (OPEC Net-Positive stress panel)
  console.log('D. Capturing crops/stress_opec.png...')
  const navBtns2x = page2x.locator('header nav button')
  await navBtns2x.filter({ hasText: /Scenario/i }).click()
  await page2x.waitForTimeout(800)
  const themeSelect2x = page2x.locator('select')
  if (await themeSelect2x.count() > 0) {
    await themeSelect2x.selectOption('oil_price_up')
    await page2x.locator('form button[type="submit"]').click()
    await page2x.waitForTimeout(1000)
  }
  await page2x.evaluate(() => window.scrollTo(0, 0))
  await page2x.waitForTimeout(400)
  const opecPanel = page2x.locator('#scenario-lab-stress-panel > div').first()
  await opecPanel.screenshot({ path: path.join(CROPS_DIR, 'stress_opec.png') })

  // Crop E: calibration_chart.png (Scatter, fitted line, 80% band, with axis titles)
  console.log('E. Capturing crops/calibration_chart.png...')
  await navBtns2x.filter({ hasText: /Calibration/i }).click()
  await page2x.waitForTimeout(1200)
  const calibChartCard = page2x.locator('#calibration-chart-card')
  await calibChartCard.scrollIntoViewIfNeeded()
  await calibChartCard.screenshot({ path: path.join(CROPS_DIR, 'calibration_chart.png') })

  await context2x.close()
  await browser.close()
  console.log('All full-page and cropped screenshots captured successfully!')
}

capture().catch((err) => {
  console.error('Screenshot capture failed:', err)
  process.exit(1)
})
