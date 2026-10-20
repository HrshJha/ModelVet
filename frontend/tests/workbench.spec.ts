import { test, expect, type BrowserContextOptions } from '@playwright/test';

let authenticated: NonNullable<BrowserContextOptions['storageState']>;
test.beforeAll(async ({ browser }) => {
  const context = await browser.newContext();
  const response = await context.request.post('http://127.0.0.1:48231/api/v1/session', {
    data: { token: 'browser-fixture-launch-token-' + 'a'.repeat(32) },
    headers: { Origin: 'http://127.0.0.1:48231' },
  });
  expect(response.ok()).toBeTruthy();
  authenticated = await context.storageState();
  await context.close();
});
test.use({ storageState: async ({}, use) => { await use(authenticated); } });

test('overview has real empty state and working navigation', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Evidence before execution.' })).toBeVisible();
  await expect(page.getByText('Your first evidence trail starts here.')).toBeVisible();
  await page.getByRole('button', { name: 'Jump to…' }).click();
  await page.getByRole('textbox', { name: 'Find a page' }).fill('environment');
  await page.getByRole('dialog').getByRole('button', { name: 'Environment' }).click();
  await expect(page.getByRole('heading', { name: 'Know your environment.' })).toBeVisible();
});

test('folder browser runs a genuine supported static scan', async ({ page }) => {
  await page.goto('/#/scan');
  await page.getByRole('button', { name: 'Browse folders' }).click();
  await page.getByRole('button', { name: 'tiny-safetensors', exact: true }).click();
  await page.getByRole('button', { name: 'Use this folder' }).click();
  await expect(page.getByLabel('Model folder')).toHaveValue('tiny-safetensors');
  await page.getByRole('button', { name: 'Start scan' }).click();
  await expect(page.getByRole('heading', { name: 'tiny-safetensors' })).toBeVisible({ timeout: 15000 });
  await expect(page.locator('.verdict-panel').getByText('APPROVE', { exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Scan history', exact: true }).click();
  await expect(page.getByRole('link', { name: /tiny-safetensors/ })).toBeVisible();
});
