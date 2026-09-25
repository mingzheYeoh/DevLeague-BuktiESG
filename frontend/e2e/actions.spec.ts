import { expect, test, type Download, type Page } from '@playwright/test'
import { CORS_HEADERS, stubActor } from './support/api-stubs'

async function openActions(page: Page, failFirst = false) {
  const actions: Record<string, unknown>[] = []
  const json = (body: unknown, status = 200) => ({ status, contentType: 'application/json', headers: CORS_HEADERS, body: JSON.stringify(body) })
  const summary = { id: 'action-case', title: 'Action test case', customer_name: 'Demo customer', status: 'DRAFT', deadline_at: null, updated_at: new Date().toISOString() }
  await page.addInitScript(() => localStorage.clear())
  await stubActor(page)
  await page.route('**/health', r => r.fulfill(json({ status: 'ok' })))
  await page.route('**/api/v1/cases', r => r.fulfill(json([summary])))
  await page.route('**/api/v1/cases/action-case', r => r.fulfill(json(summary)))
  await page.route('**/api/v1/cases/action-case/readiness', r => r.fulfill(json({ percentage: 0, confirmed_required_questions: 0, total_required_questions: 0 })))
  await page.route('**/api/v1/cases/action-case/questions', r => r.fulfill(json([])))
  await page.route('**/api/v1/cases/action-case/documents', r => r.fulfill(json([{ id: 'doc-1', original_filename: 'policy.txt', document_type: 'OTHER', processing_status: 'INDEXED', size_bytes: 10, sha256: 'abc', created_at: new Date().toISOString() }])))
  await page.route('**/api/v1/cases/action-case/actions', r => {
    if (r.request().method() === 'POST') {
      if (failFirst) {
        failFirst = false
        return r.fulfill(json({ detail: { error: { code: 'INTERNAL_ERROR', message: 'Action could not be saved. Please retry.' } } }, 503))
      }
      const body = r.request().postDataJSON()
      const action = { ...body, id: `action-${actions.length}`, case_id: summary.id, status: 'TODO', requires_closure_evidence: body.requires_closure_evidence ?? false, created_at: new Date().toISOString(), updated_at: new Date().toISOString() }
      actions.push(action)
      return r.fulfill(json(action, 201))
    }
    return r.fulfill(json(actions))
  })
  await page.goto('/')
  await page.locator('.table-card').getByText(summary.title).click()
  await page.getByRole('button', { name: 'Actions', exact: true }).click()
  return actions
}

async function fillAction(page: Page) {
  await page.getByRole('button', { name: 'New action', exact: true }).click()
  const submit = page.getByRole('button', { name: 'Create action', exact: true })
  await expect(submit).toBeDisabled()
  await page.getByLabel('Action title').fill('Collect energy records')
  await page.getByLabel('Owner', { exact: false }).first().fill('Alex Tan')
  await page.getByLabel('Next step').fill('Request the monthly electricity bills')
  await expect(submit).toBeDisabled()
  await page.getByLabel('Deadline').fill('2026-12-31')
  return submit
}

for (const type of ['SUBMISSION', 'IMPROVEMENT']) {
  test(`create ${type} action, reload, and export its register`, async ({ page }) => {
    const actions = await openActions(page)
    if (type === 'IMPROVEMENT') await page.getByRole('button', { name: /Improvement actions/ }).click()
    const submit = await fillAction(page)
    await submit.click()
    await expect(page.locator('tbody')).toContainText('Collect energy records')
    expect(actions).toHaveLength(1)
    expect(actions[0]).toMatchObject({ type, owner_name: 'Alex Tan', next_step: 'Request the monthly electricity bills', question_id: null })
    const date = await page.evaluate(value => new Date(String(value)).toLocaleDateString('en-CA'), actions[0].deadline_at)
    expect(date).toBe('2026-12-31')
    await page.reload()
    await page.getByRole('button', { name: 'Cases', exact: true }).click()
    await page.locator('.table-card').getByText('Action test case').click()
    await page.getByRole('button', { name: 'Actions', exact: true }).click()
    if (type === 'IMPROVEMENT') await page.getByRole('button', { name: /Improvement actions/ }).click()
    await expect(page.locator('tbody')).toContainText('Collect energy records')
    await page.getByRole('button', { name: 'Export', exact: true }).click()
    await page.getByRole('button', { name: 'Generate marked-up draft', exact: true }).click()
    const downloads: Download[] = []
    page.on('download', download => downloads.push(download))
    await page.getByRole('button', { name: 'Download package', exact: true }).click()
    await expect.poll(() => downloads.length).toBe(4)
    expect(downloads.map(d => d.suggestedFilename()).sort()).toEqual(['action-register.csv', 'customer-response-summary.txt', 'document-register.csv', 'evidence-index.csv'])
    const register = downloads.find(d => d.suggestedFilename() === 'action-register.csv')!
    const stream = await register.createReadStream()
    let contents = ''
    for await (const chunk of stream) contents += chunk.toString()
    expect(contents).toContain('Collect energy records')
    expect(contents).toContain('Alex Tan')
    expect(contents).toContain(type)
  })
}

test('failed creation preserves input and allows retry without a duplicate', async ({ page }) => {
  const actions = await openActions(page, true)
  const submit = await fillAction(page)
  await submit.click()
  await expect(page.getByText('Action could not be saved. Please retry.')).toBeVisible()
  await expect(page.getByLabel('Action title')).toHaveValue('Collect energy records')
  expect(actions).toHaveLength(0)
  await submit.click()
  await expect(page.locator('tbody')).toContainText('Collect energy records')
  expect(actions).toHaveLength(1)
})
