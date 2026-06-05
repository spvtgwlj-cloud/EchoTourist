import { test, expect } from '@playwright/test';

test.describe('回归测试 — 国际化 (i18n)', () => {

  test('REG-I18N-001：所有语言版本首页正常渲染', async ({ page }) => {
    const locales = ['/zh', '/en'];

    for (const locale of locales) {
      const response = await page.goto(locale);
      await page.waitForLoadState('networkidle');

      expect(response?.status()).toBe(200);
      await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
      const text = await page.locator('body').textContent() || '';
      expect(text.length).toBeGreaterThan(100);
    }
  });

  test('REG-I18N-002：多语言切换后页面不崩溃', async ({ page }) => {
    // 进入中文首页
    await page.goto('/zh');
    await page.waitForLoadState('networkidle');

    // 找到语言切换器
    const langSwitch = page.locator(
      'a[href*="/en"], button:has-text("EN"), button:has-text("English"), '
      + 'a[href*="/zh"], button:has-text("中文"), [role="tab"]:has-text("EN"), '
      + '[role="tab"]:has-text("中文")'
    ).first();

    if (await langSwitch.isVisible({ timeout: 5000 }).catch(() => false)) {
      await langSwitch.click();
      await page.waitForLoadState('networkidle');
    }

    // 无论切换到哪个语言，页面应正常
    await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
    const text = await page.locator('body').textContent() || '';
    expect(text.length).toBeGreaterThan(100);
  });

  test('REG-I18N-003：各语言搜索页面正常', async ({ page }) => {
    const locales = ['/zh', '/en'];

    for (const locale of locales) {
      await page.goto(`${locale}/search?q=beijing`);
      await page.waitForLoadState('networkidle').catch(() => {});

      await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
    }
  });
});
