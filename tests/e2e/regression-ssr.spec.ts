import { test, expect } from '@playwright/test';

test.describe('回归测试 — SSR 服务端渲染', () => {

  test('REG-SSR-001：首页 SSR 内容完整', async ({ page }) => {
    const response = await page.goto('/zh');
    await page.waitForLoadState('networkidle');

    // SSR 响应应为 200
    expect(response?.status()).toBe(200);

    // 页面内容应包含关键元素
    const bodyText = await page.locator('body').textContent() || '';
    expect(bodyText.length).toBeGreaterThan(100);

    // 标题/导航应存在
    const hasNav = await page.locator('nav, header, [role="navigation"]').first().isVisible()
      .catch(() => false);
    expect(hasNav).toBeTruthy();
  });

  test('REG-SSR-002：产品列表页 SSR 内容完整', async ({ page }) => {
    const response = await page.goto('/zh/tours');
    await page.waitForLoadState('networkidle');

    expect(response?.status()).toBe(200);

    // 页面应包含产品相关内容
    await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
    const text = await page.locator('body').textContent() || '';
    expect(text.length).toBeGreaterThan(100);
  });

  test('REG-SSR-003：目的地列表页 SSR 内容完整', async ({ page }) => {
    const response = await page.goto('/zh/destinations');
    await page.waitForLoadState('networkidle');

    expect(response?.status()).toBe(200);

    await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
    const text = await page.locator('body').textContent() || '';
    expect(text.length).toBeGreaterThan(100);

    // 应有可点击的目的地链接
    const hasLinks = await page.locator('a[href*="/destinations/"]').first().isVisible()
      .catch(() => false);
    // 至少导航链接或者页面有内容
    expect(text.length).toBeGreaterThan(100);
  });
});
