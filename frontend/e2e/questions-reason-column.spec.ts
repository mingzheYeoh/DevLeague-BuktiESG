import { expect, test, type Page } from '@playwright/test'

import { CORS_HEADERS as CORS, stubActor } from './support/api-stubs'

/**
 * Reason column in the Questionnaire table.
 *
 * Covers the four data shapes that broke the old layout (long, empty,
 * multi-clause, short), the two-line clamp, keyboard reachability, three
 * viewports, and the requirement that the other `.table-card` tables are
 * untouched.
 *
 * The API is stubbed with the server's real response shapes. One assertion is
 * deliberately inverted: the frontend must render `status_reason` **verbatim**,
 * proving the duplicate-clause fix lives in the rule engine and not here.
 */

const CASE_ID = 'case-reason-0001'

const CASE_SUMMARY = {
  id: CASE_ID,
  title: 'Reason column case',
  customer_name: 'Reason Customer',
  deadline_at: null,
  status: 'DRAFT',
  updated_at: new Date().toISOString(),
}

/** The real deduped reason the rule engine now produces, 468 characters. */
const LONG_REASON =
  "Candidate evidence located by automated keyword match against 'safety-incident-register-fy2025.txt'; " +
  'coverage is not yet verified by a human reviewer. Evidence exists but coverage is incomplete. ' +
  'Coverage exists but is incomplete: evidence has not been human-accepted (an unreviewed AI-proposed ' +
  'candidate cannot, by itself, satisfy VERIFIED — Main Spec §17 Gate P4: AI confidence does not ' +
  'participate in the VERIFIED determination) (same finding on 9 evidence records).'

/** Three genuinely different findings; none may be collapsed. */
const MULTI_REASON =
  'Evidence exists but coverage is incomplete. ' +
  'Coverage exists but is incomplete: evidence does not clearly support the claim. ' +
  'Coverage exists but is incomplete: numerical value has no explainable unit. ' +
  'Coverage exists but is incomplete: source location is empty.'

const SHORT_REASON = 'No evidence link found for this question.'

function question(overrides: Record<string, unknown>) {
  return {
    id: 'q-default',
    external_question_id: 'Q-X-00',
    question_text: 'Default question text.',
    is_required: true,
    pillar: 'E',
    sedg_topic_code: 'E1',
    sedg_disclosure_code: 'E1.2',
    evidence_status: 'PARTIAL',
    review_status: 'UNREVIEWED',
    priority_score: null,
    owner_name: null,
    source_location: null,
    status_reason: null,
    status_points: [],
    evidence_location: null,
    mapping_rationale: null,
    evidence_excerpt: null,
    evidence_claim_supported: null,
    evidence_document_id: null,
    evidence_document_name: null,
    evidence_candidate_count: 0,
    ...overrides,
  }
}

const QUESTIONS = [
  question({
    id: 'q-long',
    external_question_id: 'Q-E-01',
    question_text: 'Report total annual electricity consumption in kWh for the reporting period.',
    status_reason: LONG_REASON,
    status_points: ['evidence has not been accepted by a human reviewer'],
    // Deliberately the wrong document, as the running app actually produces:
    // nine candidates, and the newest-created one wins the display.
    evidence_document_id: 'doc-safety',
    evidence_document_name: 'safety-incident-register-fy2025.txt',
    evidence_candidate_count: 9,
    evidence_excerpt: 'Total days lost to work-related injury: 11.',
    evidence_claim_supported: 'Keyword overlap with question terms: total',
    evidence_location: { type: 'paragraph', heading_path: [], paragraph_index: 7 },
  }),
  question({
    id: 'q-empty',
    external_question_id: 'Q-E-06',
    question_text: 'Does the company purchase or generate renewable energy such as solar?',
    evidence_status: 'MISSING',
    status_reason: null,
  }),
  question({
    id: 'q-multi',
    external_question_id: 'Q-S-01',
    question_text: 'Report the work-related injury rate (LTIFR) and any fatalities.',
    pillar: 'S',
    status_reason: MULTI_REASON,
    // A DOCX, to exercise the format a browser cannot render.
    evidence_document_id: 'doc-handbook',
    evidence_document_name: 'employee-handbook-2022.docx',
    evidence_candidate_count: 1,
    evidence_excerpt: 'Any worker may raise a grievance through the confidential telephone line.',
    evidence_location: {
      type: 'paragraph',
      heading_path: ['Employee Handbook 2022', 'Grievance procedure'],
      paragraph_index: 0,
    },
  }),
  question({
    id: 'q-short',
    external_question_id: 'Q-G-01',
    question_text: 'Describe anti-bribery and anti-corruption controls.',
    pillar: 'G',
    evidence_status: 'CONFLICTING',
    review_status: 'HUMAN_CONFIRMED',
    status_reason: SHORT_REASON,
  }),
]

/** The safety register as the server chunks it: one fragment per non-blank line. */
const SAFETY_CHUNKS = [
  'SAFETY INCIDENT REGISTER FY2025 - BuktiPack Manufacturing Sdn. Bhd. (SYNTHETIC SAMPLE)',
  'SYNTHETIC FIXTURE. Invented incidents; no real person is described.',
  'Register covers 1 January 2025 to 31 December 2025.',
  'Hours worked across all employees and contractors: 93,600.',
  'Number of recordable work-related injuries resulting in lost time: 2.',
  'Lost time injury frequency rate (LTIFR) per million hours worked: 21.4.',
  'Number of work-related fatalities: 0.',
  'Total days lost to work-related injury: 11.',
  'No occupational illness case was recorded in FY2025.',
].map((text, i) => ({
  id: `safety-chunk-${i}`,
  sequence_no: i,
  text,
  page_number: null,
  sheet_name: null,
  cell_range: null,
  heading_path: [],
}))

/** A DOCX chunks per heading section, so it carries a heading path instead. */
const DOCX_CHUNKS = [
  {
    id: 'docx-chunk-0',
    sequence_no: 0,
    text: 'Any worker may raise a grievance through the confidential telephone line.',
    page_number: null,
    sheet_name: null,
    cell_range: null,
    heading_path: ['Employee Handbook 2022', 'Grievance procedure'],
  },
  {
    id: 'docx-chunk-1',
    sequence_no: 1,
    text: 'Standard working hours are 8.30am to 5.30pm, Monday to Friday.',
    page_number: null,
    sheet_name: null,
    cell_range: null,
    heading_path: ['Employee Handbook 2022', 'Working hours and leave'],
  },
]

async function stubApi(page: Page, overrideQuestions?: unknown[]) {
  const json = (body: unknown, status = 200) => ({
    status,
    contentType: 'application/json',
    headers: CORS,
    body: JSON.stringify(body),
  })

  await stubActor(page)
  await page.route('**/documents/doc-safety/chunks', (r) => r.fulfill(json(SAFETY_CHUNKS)))
  await page.route('**/documents/doc-handbook/chunks', (r) => r.fulfill(json(DOCX_CHUNKS)))

  await page.route('**/health', (r) => r.fulfill(json({ status: 'ok' })))
  await page.route('**/api/v1/cases', (r) => r.fulfill(json([CASE_SUMMARY])))
  await page.route(`**/api/v1/cases/${CASE_ID}`, (r) => r.fulfill(json(CASE_SUMMARY)))
  await page.route(`**/api/v1/cases/${CASE_ID}/readiness`, (r) =>
    r.fulfill(
      json({
        confirmed_required_questions: 1,
        total_required_questions: 4,
        percentage: 25.0,
      }),
    ),
  )
  await page.route(`**/api/v1/cases/${CASE_ID}/questions`, (r) =>
    r.fulfill(json(overrideQuestions ?? QUESTIONS)),
  )
  await page.route(`**/api/v1/cases/${CASE_ID}/documents`, (r) => r.fulfill(json([])))
  await page.route(`**/api/v1/cases/${CASE_ID}/actions`, (r) => r.fulfill(json([])))
}

/** Cases list -> open the case -> Questionnaire screen.
 *
 * `overrideQuestions` replaces the default four-row fixture, for tests that need
 * one specific question state. */
async function gotoQuestionnaire(page: Page, overrideQuestions?: unknown[]) {
  await page.addInitScript(() => {
    window.localStorage.clear()
  })
  await stubApi(page, overrideQuestions)
  await page.goto('/')
  await page.locator('.table-card').getByText('Reason column case', { exact: true }).click()
  await page.getByRole('button', { name: 'Questionnaire', exact: false }).first().click()
  await expect(page.getByRole('heading', { name: 'Customer questionnaire' })).toBeVisible()
}

test.describe('Reason column', () => {
  test('a long reason is clamped to two lines but kept whole in the DOM', async ({ page }) => {
    await gotoQuestionnaire(page)

    const summary = page.locator('.questions-table .reason-summary').first()

    // The complete text is present — nothing was truncated in the data.
    await expect(summary).toHaveText(LONG_REASON)

    const metrics = await summary.evaluate((el) => {
      const style = getComputedStyle(el)
      return {
        clientHeight: el.clientHeight,
        scrollHeight: el.scrollHeight,
        lineHeight: parseFloat(style.lineHeight),
        overflow: style.overflow,
        lineClamp: style.webkitLineClamp,
        textLength: (el.textContent ?? '').length,
      }
    })

    expect(metrics.lineClamp).toBe('2')
    expect(metrics.overflow).toBe('hidden')
    expect(metrics.textLength).toBe(LONG_REASON.length)
    // Two lines of box, and genuinely more content than fits.
    expect(metrics.clientHeight).toBeLessThanOrEqual(metrics.lineHeight * 2 + 2)
    expect(metrics.scrollHeight).toBeGreaterThan(metrics.clientHeight)
  })

  test('a long reason does not stretch the row', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await gotoQuestionnaire(page)

    const rows = await page.locator('.questions-table tbody tr').evaluateAll((els) =>
      els.map((row) => {
        const summary = row.querySelector('.reason-summary') as HTMLElement | null
        return {
          rowHeight: (row as HTMLElement).getBoundingClientRect().height,
          questionHeight: (
            row.querySelector('.question-cell') as HTMLElement
          ).getBoundingClientRect().height,
          reasonHeight: summary ? summary.getBoundingClientRect().height : 0,
          reasonChars: (summary?.textContent ?? '').length,
        }
      }),
    )

    expect(rows).toHaveLength(4)

    // The Reason cell is what this fix is about: no matter how long the text,
    // its rendered box stays at two lines. Row height still varies with the
    // question text, which wraps on its own and is not in scope here.
    const longRow = rows[0]
    expect(longRow.reasonChars).toBe(LONG_REASON.length)

    const tallestReason = Math.max(...rows.map((r) => r.reasonHeight))
    expect(tallestReason).toBeLessThan(44) // 2 lines at 13px/1.4 plus rounding

    // Reason never drives the row height: every row is at least as tall as its
    // own question cell, and no row is dominated by its reason.
    for (const row of rows) {
      expect(row.reasonHeight).toBeLessThanOrEqual(row.rowHeight)
      expect(row.rowHeight).toBeLessThan(160)
    }

    // Before the fix the 2,327-character reason rendered every line, which put
    // this well past 300px.
    expect(longRow.rowHeight).toBeLessThan(160)
  })

  test('every distinct clause survives; the frontend never dedupes', async ({ page }) => {
    await gotoQuestionnaire(page)

    const multi = page.locator('.questions-table .reason-summary').nth(1)

    // Rendered verbatim. If the frontend were quietly collapsing repeats, this
    // would fail — and it must fail, because the fix belongs in the rule engine.
    await expect(multi).toHaveText(MULTI_REASON)
    const clauseCount = await multi.evaluate(
      (el) => ((el.textContent ?? '').match(/Coverage exists but is incomplete:/g) ?? []).length,
    )
    expect(clauseCount).toBe(3)
  })

  test('an empty reason shows the not-available marker, not a blank cell', async ({ page }) => {
    await gotoQuestionnaire(page)

    const cells = page.locator('.questions-table .reason-cell')
    // Row order: long, empty, multi, short.
    await expect(cells.nth(1).locator('.not-available')).toBeVisible()
    await expect(cells.nth(1).locator('.reason-summary')).toHaveCount(0)
  })

  test('the icon never shrinks and the cell is not a flex container', async ({ page }) => {
    await gotoQuestionnaire(page)

    const cellDisplay = await page
      .locator('.questions-table .reason-cell')
      .first()
      .evaluate((el) => getComputedStyle(el).display)
    // Regression: the <td> used to be display:flex, which removed it from the
    // table layout algorithm.
    expect(cellDisplay).toBe('table-cell')

    const icon = await page
      .locator('.questions-table .reason-content svg')
      .first()
      .evaluate((el) => {
        const style = getComputedStyle(el)
        return { shrink: style.flexShrink, width: el.getBoundingClientRect().width }
      })
    expect(icon.shrink).toBe('0')
    expect(icon.width).toBeGreaterThan(10)
  })

  test('the detail screen leads with a plain conclusion, not the audit sentence', async ({
    page,
  }) => {
    await gotoQuestionnaire(page)
    await page.locator('.questions-table tbody tr').first().click()

    await expect(page.getByRole('heading', { level: 1 })).toContainText(
      'Report total annual electricity consumption',
    )

    // One readable conclusion, plus the specific finding as a bullet.
    await expect(page.locator('.status-summary-head b')).toHaveText(
      'Evidence found, but not enough to rely on yet',
    )
    await expect(page.locator('.status-points li')).toHaveText([
      'evidence has not been accepted by a human reviewer',
    ])

    // The audit sentence is folded away, not deleted.
    const full = page.locator('.status-reason-full')
    await expect(full).toBeHidden()
    await expect(full).toHaveText(LONG_REASON)
  })

  test('the full reason is one click away and complete', async ({ page }) => {
    await gotoQuestionnaire(page)
    await page.locator('.questions-table tbody tr').first().click()

    await page.getByText('Technical detail').first().click()

    const full = page.locator('.status-reason-full')
    await expect(full).toBeVisible()
    await expect(full).toHaveText(LONG_REASON)

    // Not clamped once open — the detail view shows everything.
    const clamped = await full.evaluate((el) => getComputedStyle(el).webkitLineClamp)
    expect(clamped === 'none' || clamped === '' || clamped === 'auto').toBe(true)
  })

  test('the audit sentence appears once on the detail screen, not in both columns', async ({
    page,
  }) => {
    await gotoQuestionnaire(page)
    await page.locator('.questions-table tbody tr').first().click()

    // Regression: the same 460-character sentence used to render in the left
    // column and again in the right column's Gap & action tab.
    const occurrences = await page.evaluate((reason) => {
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)
      let count = 0
      while (walker.nextNode()) {
        if ((walker.currentNode.textContent ?? '').includes(reason)) count += 1
      }
      return count
    }, LONG_REASON)

    expect(occurrences).toBe(1)
  })

  test('the citation names its document and says how many matches there were', async ({
    page,
  }) => {
    await gotoQuestionnaire(page)
    await page.locator('.questions-table tbody tr').first().click()

    // Filename, not just a bare location. "Paragraph 8" on its own gave a
    // reviewer no way to know paragraph 8 of what.
    await expect(page.locator('.evidence-where')).toHaveText(
      'safety-incident-register-fy2025.txt',
    )

    // A .txt file is chunked one fragment per line, so the location is a line
    // number. Calling it "Paragraph 8" described the location type, not the
    // file.
    await expect(page.locator('.evidence-locus')).toHaveText(
      'Line 8 · showing 1 of 9 possible matches',
    )

    // And it says out loud that this is the most recent match rather than the
    // closest one.
    await expect(
      page.getByText('found 9 passages that share words with this question', { exact: false }),
    ).toBeVisible()
  })

  test('opening the document highlights the cited fragment in context', async ({ page }) => {
    await gotoQuestionnaire(page)
    await page.locator('.questions-table tbody tr').first().click()

    await page.getByRole('button', { name: 'Open document' }).click()

    const dialog = page.getByRole('dialog', {
      name: 'Preview of safety-incident-register-fy2025.txt',
    })
    await expect(dialog).toBeVisible()

    // Whole document in context, with the cited line marked.
    await expect(dialog.locator('.chunk')).toHaveCount(SAFETY_CHUNKS.length)
    const cited = dialog.locator('.chunk.cited')
    await expect(cited).toHaveCount(1)
    await expect(cited).toContainText('Total days lost to work-related injury: 11.')
    await expect(cited.locator('.chunk-locus')).toHaveText('Line 8')
    await expect(cited.locator('.chunk-badge')).toHaveText('Cited here')

    // Esc closes it, and focus started inside the dialog.
    await page.keyboard.press('Escape')
    await expect(dialog).toBeHidden()
  })

  test('a format a browser cannot render offers a download instead of pretending', async ({
    page,
  }) => {
    await gotoQuestionnaire(page)
    await page.locator('.questions-table tbody tr').nth(2).click()

    await page.getByRole('button', { name: 'Open document' }).click()
    const dialog = page.getByRole('dialog', { name: /Preview of employee-handbook-2022.docx/ })
    await expect(dialog).toBeVisible()

    // Extracted text still works for DOCX — that is the point of that view.
    await expect(dialog.locator('.chunk')).toHaveCount(DOCX_CHUNKS.length)
    await expect(dialog.locator('.chunk-locus').first()).toContainText('Grievance procedure')

    // The original, however, is honestly declared unrenderable.
    await dialog.getByRole('tab', { name: 'Original file' }).click()
    await expect(dialog.getByText('A browser cannot display Word files')).toBeVisible()
    await expect(dialog.getByRole('link', { name: /Download employee-handbook-2022.docx/ })).toBeVisible()
    await expect(dialog.locator('iframe')).toHaveCount(0)
  })

  test('a single-candidate question does not claim there are others', async ({ page }) => {
    await gotoQuestionnaire(page)
    // Row 4 (Q-G-01) has a short reason and no evidence candidates at all.
    await page.locator('.questions-table tbody tr').nth(3).click()

    await expect(page.locator('.evidence-locus')).toHaveCount(0)
    await expect(page.getByText('other candidate', { exact: false })).toHaveCount(0)
  })

  test('a not-applicable question offers only Reopen, not answer buttons', async ({ page }) => {
    // The server refuses ACCEPT and EDIT while a question is not applicable, so
    // offering those buttons would only produce a 422.
    await gotoQuestionnaire(page, [
      question({
        id: 'q-na',
        external_question_id: 'Q-E-06',
        question_text: 'Does the company operate a vehicle fleet?',
        evidence_status: 'NOT_APPLICABLE',
        review_status: 'HUMAN_CONFIRMED',
        status_reason: 'Marked NOT_APPLICABLE by Nur Aina. Reason: No vehicles.',
        status_points: ['Marked not applicable by Nur Aina'],
      }),
    ])
    await page.locator('.questions-table tbody tr').first().click()

    await expect(page.getByRole('button', { name: 'Reopen this question' })).toBeVisible()
    for (const name of ['Write the answer', 'Confirm draft', 'Not applicable']) {
      await expect(page.getByRole('button', { name, exact: true })).toHaveCount(0)
    }
    await expect(page.getByText('there is nothing to answer', { exact: false })).toBeVisible()
  })

  test('Reopen asks for a reason and warns what it withdraws', async ({ page }) => {
    await gotoQuestionnaire(page, [
      question({
        id: 'q-na',
        external_question_id: 'Q-E-06',
        question_text: 'Does the company operate a vehicle fleet?',
        evidence_status: 'NOT_APPLICABLE',
        review_status: 'HUMAN_CONFIRMED',
        status_points: ['Marked not applicable by Nur Aina'],
      }),
    ])
    await page.locator('.questions-table tbody tr').first().click()
    await page.getByRole('button', { name: 'Reopen this question' }).click()

    await expect(page.getByText('This withdraws your decision')).toBeVisible()
    await expect(page.getByPlaceholder('Why are you withdrawing the earlier decision?')).toBeVisible()
  })

  test('a confirmed question offers Undo alongside the other decisions', async ({ page }) => {
    await gotoQuestionnaire(page, [
      question({
        id: 'q-done',
        external_question_id: 'Q-S-03',
        question_text: 'Report gender diversity, including women in management.',
        evidence_status: 'PARTIAL',
        review_status: 'HUMAN_CONFIRMED',
        status_points: ['evidence has not been accepted by a human reviewer'],
      }),
    ])
    await page.locator('.questions-table tbody tr').first().click()

    await expect(page.getByRole('button', { name: 'Undo' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Write the answer' })).toBeVisible()
  })

  test('marking not applicable warns that it counts toward readiness', async ({ page }) => {
    await gotoQuestionnaire(page)
    await page.locator('.questions-table tbody tr').first().click()

    await page.getByRole('button', { name: 'Not applicable', exact: true }).click()

    await expect(
      page.getByText('Only for questions that genuinely do not apply'),
    ).toBeVisible()
    await expect(page.getByText('readiness goes up', { exact: false })).toBeVisible()
  })

  test('the detail screen keeps the reviewer to a small number of blocks', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await gotoQuestionnaire(page)
    await page.locator('.questions-table tbody tr').first().click()

    // Left column: the status summary and the decision block. Nothing else.
    const leftBlocks = await page
      .locator('.answer-panel > *')
      .evaluateAll((els) => els.map((el) => el.className))
    expect(leftBlocks).toHaveLength(2)
    expect(leftBlocks[0]).toContain('status-summary')
    expect(leftBlocks[1]).toContain('review-block')

    // The four decisions are all reachable without opening anything.
    for (const name of ['Reject', 'Not applicable', 'Write the answer', 'Confirm draft']) {
      await expect(page.getByRole('button', { name, exact: true })).toBeVisible()
    }
  })

  test('a keyboard-only user can reach the detail screen', async ({ page }) => {
    await gotoQuestionnaire(page)

    // Tab until the first row's open button has focus. No mouse involved.
    let reached = false
    for (let i = 0; i < 60 && !reached; i += 1) {
      await page.keyboard.press('Tab')
      reached = await page.evaluate(() => {
        const active = document.activeElement
        const first = document.querySelector('.questions-table .row-open-btn')
        return Boolean(active && first && active === first)
      })
    }
    expect(reached, 'the first row open button should be reachable by Tab').toBe(true)

    const label = await page
      .locator('.questions-table .row-open-btn')
      .first()
      .getAttribute('aria-label')
    expect(label).toContain('View question Q-E-01')

    await page.keyboard.press('Enter')
    await expect(page.getByRole('heading', { name: 'Response readiness' })).toHaveCount(0)
    await expect(page.getByRole('heading', { level: 1 })).toContainText(
      'Report total annual electricity consumption',
    )
  })

  for (const [name, width, height] of [
    ['wide desktop', 1920, 1080],
    ['laptop', 1440, 900],
    ['narrow', 800, 900],
  ] as const) {
    test(`status columns stay readable and separate at ${name} (${width}px)`, async ({ page }) => {
      await page.setViewportSize({ width, height })
      await gotoQuestionnaire(page)

      const evidence = await page
        .locator('.questions-table tbody tr')
        .first()
        .locator('td')
        .nth(2)
        .boundingBox()
      const review = await page
        .locator('.questions-table tbody tr')
        .first()
        .locator('td')
        .nth(3)
        .boundingBox()
      const reason = await page
        .locator('.questions-table tbody tr')
        .first()
        .locator('td')
        .nth(4)
        .boundingBox()

      expect(evidence && review && reason).toBeTruthy()
      if (!evidence || !review || !reason) return

      // No overlap, in order, and none collapsed to nothing.
      expect(evidence.x + evidence.width).toBeLessThanOrEqual(review.x + 1)
      expect(review.x + review.width).toBeLessThanOrEqual(reason.x + 1)
      expect(evidence.width).toBeGreaterThan(70)
      expect(review.width).toBeGreaterThan(70)
      expect(reason.width).toBeGreaterThanOrEqual(260)

      // The pills are not clipped by their columns.
      const pill = await page
        .locator('.questions-table tbody tr')
        .first()
        .locator('td')
        .nth(2)
        .locator('.pill')
        .boundingBox()
      expect(pill).toBeTruthy()
      if (pill) expect(pill.width).toBeLessThanOrEqual(evidence.width)
    })
  }

  test('the narrow viewport scrolls horizontally instead of crushing columns', async ({ page }) => {
    await page.setViewportSize({ width: 800, height: 900 })
    await gotoQuestionnaire(page)

    const card = await page.locator('.questions-table').evaluate((el) => ({
      clientWidth: el.clientWidth,
      scrollWidth: el.scrollWidth,
      overflowX: getComputedStyle(el).overflowX,
    }))
    expect(card.overflowX).toBe('auto')
    expect(card.scrollWidth).toBeGreaterThan(card.clientWidth)
  })

  test('the other table-card screens are unaffected', async ({ page }) => {
    await gotoQuestionnaire(page)

    // Cases table: no fixed layout, no reason cell, no forced min-width.
    await page.getByRole('button', { name: 'Cases', exact: true }).click()
    await expect(page.getByRole('heading', { name: 'Response cases' })).toBeVisible()

    const cases = await page.locator('.table-card').first().evaluate((el) => {
      const table = el.querySelector('table') as HTMLElement
      return {
        isQuestionsTable: el.classList.contains('questions-table'),
        tableLayout: getComputedStyle(table).tableLayout,
        minWidth: getComputedStyle(table).minWidth,
        reasonCells: el.querySelectorAll('.reason-cell').length,
      }
    })
    expect(cases.isQuestionsTable).toBe(false)
    expect(cases.tableLayout).toBe('auto')
    expect(cases.minWidth).toBe('0px')
    expect(cases.reasonCells).toBe(0)
  })
})
