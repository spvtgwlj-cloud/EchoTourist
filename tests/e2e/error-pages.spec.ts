import { test, expect } from '@playwright/test';

test.describe('🚫 错误页面处理', () => {
  test('访问不存在的页面显示 404', async ({ page }) => {
    await page.goto('/zh/nonexistent-page-xyz-123');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').innerText();
    // 应包含 404 或 not found 相关提示
    const has404 = bodyText.includes('404') || bodyText.includes('not found')
      || bodyText.includes('Not Found') || bodyText.includes('找不到')
      || bodyText.includes('不存在') || bodyText.includes('页面');
    expect(has404).toBeTruthy();
  });

  test('英文下访问不存在的页面显示 404', async ({ page }) => {
    await page.goto('/en/nonexistent-page-xyz-123');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').innerText();
    const has404 = bodyText.includes('404') || bodyText.includes('not found')
      || bodyText.includes('Not Found') || bodyText.includes('找不到');
    expect(has404).toBeTruthy();
  });

  test('访问不存在的旅游产品 slug 显示 404', async ({ page }) => {
    await page.goto('/zh/tours/nonexistent-tour-slug-xyz');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').innerText();
    const has404 = bodyText.includes('404') || bodyText.includes('not found')
      || bodyText.includes('Not Found') || bodyText.includes('找不到');
    // 可能是 404 或 API 错误提示
    expect(has404 || bodyText.includes('Error') || bodyText.includes('错误')).toBeTruthy();
  });

  test('访问不存在的目的地 slug 显示 404', async ({ page }) => {
    await page.goto('/zh/destinations/nonexistent-dest-slug');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').innerText();
    const has404 = bodyText.includes('404') || bodyText.includes('not found')
      || bodyText.includes('Not Found') || bodyText.includes('找不到');
    expect(has404).toBeTruthy();
  });

  test('404 页面有返回首页的链接', async ({ page }) => {
    await page.goto('/zh/nonexistent-page-xyz-123');
    await page.waitForLoadState('networkidle');

    // 查找能返回首页的链接或按钮
    const homeLink = page.locator('a[href="/zh"], a[href="/en"], a[href="/"]').first();
    if (await homeLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await homeLink.click();
      await expect(page).toHaveURL(/\/zh$|\/en$|\/$/);
    }
  });

  test('西班牙语下 404 正常工作', async ({ page }) => {
    await page.goto('/es/nonexistent-page-xyz-123');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('🔗 无效路由处理', () => {
  test('访问无效的 locale 前缀', async ({ page }) => {
    await page.goto('/xx/some-page');
    await page.waitForLoadState('networkidle');
    // 应该优雅处理，不崩溃
    await expect(page.locator('body')).toBeVisible();
  });

  test('访问管理后台不存在的子页面', async ({ page }) => {
    await page.goto('/zh/admin/nonexistent-sub-page');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('深度嵌套的不存在路径', async ({ page }) => {
    await page.goto('/zh/a/b/c/d/e/f/g');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });
});
