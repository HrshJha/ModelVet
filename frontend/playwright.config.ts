import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests', workers: 1, fullyParallel: false, timeout: 30000,
  use: { baseURL: 'http://127.0.0.1:48231', viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce', screenshot: 'only-on-failure' },
  reporter: 'list',
  webServer: {
    command: 'uv run --project .. --extra ui python ../tools/workbench_browser.py',
    url: 'http://127.0.0.1:48231', reuseExistingServer: false, timeout: 30000,
    env: { MODELVET_BROWSER_TEST: '1' },
  },
});
