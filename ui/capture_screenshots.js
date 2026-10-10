/**
 * Automated institutional screenshot capture script using Playwright.
 * Captures clean 1440x900 high-res screenshots for docs/screenshots/
 */
import { chromium } from '@playwright/test'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const OUT_DIR = path.resolve(__dirname, '..', 'docs', 'screenshots')

async function capture() {
  if (!fs.existsSync(OUT_DIR)) {
    fs.mkdirSync(OUT_DIR, { recursive: true })
  }

  const browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1.0, // standard scale keeps files < 2MB total
  })
  const page = await context.newPage()

  console.log('Navigating to http://127.0.0.1:8000 ...')
  await page.goto('http://127.0.0.1:8000', { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(600)

  // 1. Initial Monitor resting state (hero populated before scenario fires)
  console.log('1. Capturing 01_monitor_overview.png...')
  await page.screenshot({ path: path.join(OUT_DIR, '01_monitor_overview.png') })

  // Speed up to 20x so full stream processes quickly
  const speed20x = page.locator('button', { hasText: '20x' })
  if (await speed20x.count() > 0) {
    await speed20x.click()
  }

  // Allow stream to finish all 14 signals and their outcomes
  console.log('Waiting for signals and outcomes in feed...')
  await page.waitForTimeout(3000)

  const rows = page.locator('section[aria-label="Signal Feed"] .cursor-pointer')
  const count = await rows.count()
  console.log(`Feed populated with ${count} signals`)

  if (count > 0) {
    // Select first signal and expand details
    await rows.first().click()
    await page.waitForTimeout(400)
    const expandBtn = rows.first().locator('button[aria-label="Expand details"]')
    if (await expandBtn.count() > 0) {
      await expandBtn.first().click()
      await page.waitForTimeout(400)
    }
  }

  // 2. Monitor Mid-Replay with Details Drawer
  console.log('2. Capturing 02_monitor_mid_replay_details.png...')
  await page.screenshot({ path: path.join(OUT_DIR, '02_monitor_mid_replay_details.png') })

  // 3. Suppressed Rumor State
  console.log('3. Capturing 03_suppressed_rumor.png...')
  const suppBtn = page.locator('section[aria-label="Signal Feed"]').getByRole('button', { name: /^Supp/ })
  if (await suppBtn.count() > 0) {
    await suppBtn.click()
    await page.waitForTimeout(400)
    // Expand a suppressed rumor (e.g. Bank of America or TSMC)
    const rumorRow = page.locator('section[aria-label="Signal Feed"]').getByText(/rumor|whispers|Bank of America|Toyota/i).first()
    if (await rumorRow.count() > 0) {
      await rumorRow.click()
      await page.waitForTimeout(300)
    }
  }
  await page.screenshot({ path: path.join(OUT_DIR, '03_suppressed_rumor.png') })

  // Switch back to All
  const allBtn = page.locator('section[aria-label="Signal Feed"]').getByRole('button', { name: /^All/ })
  if (await allBtn.count() > 0) {
    await allBtn.click()
    await page.waitForTimeout(300)
  }

  // 4. Red Sea Scenario Shock
  console.log('4. Capturing 04_red_sea_scenario.png...')
  const redSeaCard = page.locator('section[aria-label="Signal Feed"]').getByText(/Maersk|Red Sea/i).first()
  if (await redSeaCard.count() > 0) {
    await redSeaCard.click()
    await page.waitForTimeout(800)
  }
  await page.screenshot({ path: path.join(OUT_DIR, '04_red_sea_scenario.png') })

  // 5. Active Treemap Shock
  console.log('5. Capturing 06_treemap_active_shock.png...')
  await page.screenshot({ path: path.join(OUT_DIR, '06_treemap_active_shock.png') })

  // 6. Scenario Lab
  console.log('6. Capturing 07_scenario_lab.png...')
  const navButtons = page.locator('header nav button')
  await navButtons.filter({ hasText: /Scenario/i }).click()
  await page.waitForTimeout(1000)
  await page.screenshot({ path: path.join(OUT_DIR, '07_scenario_lab.png') })

  // 7. OPEC Net-Positive Scenario
  console.log('7. Capturing 05_opec_net_positive.png...')
  const themeSelect = page.locator('select')
  if (await themeSelect.count() > 0) {
    await themeSelect.selectOption('oil_price_up')
    await page.waitForTimeout(1000)
  }
  await page.screenshot({ path: path.join(OUT_DIR, '05_opec_net_positive.png') })

  // 8. Analyze Text View
  console.log('8. Capturing 08_analyze_result.png...')
  await navButtons.filter({ hasText: /Analyze/i }).click()
  await page.waitForTimeout(600)
  const opecPreset = page.getByRole('button', { name: /OPEC production cut/i }).first()
  if (await opecPreset.count() > 0) {
    await opecPreset.click()
    await page.waitForTimeout(300)
    await page.locator('form button[type="submit"]').click()
    await page.waitForTimeout(1200)
  }
  await page.screenshot({ path: path.join(OUT_DIR, '08_analyze_result.png') })

  // 9. Calibration View
  console.log('9. Capturing 09_calibration_scatter.png...')
  await navButtons.filter({ hasText: /Calibration/i }).click()
  await page.waitForTimeout(1000)
  await page.screenshot({ path: path.join(OUT_DIR, '09_calibration_scatter.png') })

  await browser.close()
  console.log('All screenshots captured and saved to docs/screenshots/!')
}

capture().catch((err) => {
  console.error('Screenshot capture failed:', err)
  process.exit(1)
})
