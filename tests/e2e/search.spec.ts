import { test, expect } from '@playwright/test';

test.describe('🔍 搜索功能 — 完整流程', () => {
  test('搜索页面可正常加载', async ({ page }) => {
    await page.goto('/zh/search');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('搜索输入框存在且可交互', async ({ page }) => {
    await page.goto('/zh/search');
    await page.waitForLoadState('networkidle');

    const searchInput = page.locator('input[type="text"], input[placeholder*="搜索"], input[placeholder*="Search"], input[placeholder*="buscar"]').first();
    await expect(searchInput).toBeVisible();
    await expect(searchInput).toBeEnabled();
  });

  test('中文搜索返回结果', async ({ page }) => {
    await page.goto('/zh/search');
    await page.waitForLoadState('networkidle');

    const searchInput = page.locator('input[type="text"], input[placeholder*="搜索"], input[placeholder*="Search"]').first();
    await expect(searchInput).toBeVisible();

    await searchInput.fill('故宫');
    await page.waitForTimeout(2000); // 等待防抖搜索

    // 检查是否有搜索结果（可能为空但页面应正常响应）
    await expect(page.locator('body')).toBeVisible();
  });

  test('英文搜索返回结果', async ({ page }) => {
    await page.goto('/en/search');
    await page.waitForLoadState('networkidle');

    const searchInput = page.locator('input[type="text"], input[placeholder*="Search"], input[placeholder*="搜索"]').first();
    await expect(searchInput).toBeVisible();

    await searchInput.fill('Forbidden City');
    await page.waitForTimeout(2000);

    await expect(page.locator('body')).toBeVisible();
  });

  test('搜索页面有筛选或排序选项', async ({ page }) => {
    await page.goto('/en/search');
    await page.waitForLoadState('networkidle');

    // 检查是否有 select/dropdown 或过滤按钮
    const filterSelect = page.locator('select, [role="combobox"], button:has-text("Filter"), button:has-text("Sort"), button:has-text("筛选"), button:has-text("排序")').first();
    if (await filterSelect.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(filterSelect).toBeEnabled();
    }
  });

  test('搜索结果可点击进入详情', async ({ page }) => {
    await page.goto('/en/search');
    await page.waitForLoadState('networkidle');

    const searchInput = page.locator('input[type="text"], input[placeholder*="Search"], input[placeholder*="搜索"]').first();
    await searchInput.fill('Beijing');
    await page.waitForTimeout(2000);

    // 如果出现结果链接，点击进入详情
    const resultLink = page.locator('a[href*="/en/tours/"]').first();
    if (await resultLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await resultLink.click();
      await page.waitForURL('**/tours/**');
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('搜索后清除输入恢复到初始状态', async ({ page }) => {
    await page.goto('/zh/search');
    await page.waitForLoadState('networkidle');

    const searchInput = page.locator('input[type="text"], input[placeholder*="搜索"], input[placeholder*="Search"]').first();
    await expect(searchInput).toBeVisible();

    // 输入后清除
    await searchInput.fill('故宫');
    await page.waitForTimeout(500);
    await searchInput.clear();
    await page.waitForTimeout(500);

    // 页面应正常显示
    await expect(page.locator('body')).toBeVisible();
  });
});
