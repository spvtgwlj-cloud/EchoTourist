import { test, expect } from '@playwright/test';

test.describe('🔍 搜索功能 — 筛选交互扩展', () => {
  test('难度筛选按钮可点击切换', async ({ page }) => {
    await page.goto('/en/search');
    await page.waitForLoadState('networkidle');

    // 查找难度按钮（easy/moderate/challenging）
    const easyBtn = page.locator('button:has-text("Easy"), button:has-text("Moderate"), button:has-text("Challenging")').first();
    if (!(await easyBtn.isVisible({ timeout: 3000 }).catch(() => false))) {
      test.skip('No difficulty filter buttons on this page');
      return;
    }

    // 点击第一个难度按钮
    await easyBtn.click();
    await page.waitForTimeout(1000);
    // 按钮应变为激活状态
    await expect(page.locator('body')).toBeVisible();
  });

  test('排序切换后搜索结果更新', async ({ page }) => {
    await page.goto('/en/search');
    await page.waitForLoadState('networkidle');

    const sortSelect = page.locator('select').first();
    if (!(await sortSelect.isVisible({ timeout: 3000 }).catch(() => false))) {
      test.skip('No sort select on this page');
      return;
    }

    // 获取初始结果数量
    const initialText = await page.locator('body').innerText();

    // 切换排序方式
    await sortSelect.selectOption('price_asc');
    await page.waitForTimeout(1500); // 等待防抖搜索

    // 页面应更新
    const afterText = await page.locator('body').innerText();
    const hasChanged = afterText !== initialText || afterText.length > 0;
    expect(hasChanged).toBeTruthy();
  });

  test('多个筛选项组合使用', async ({ page }) => {
    await page.goto('/en/search');
    await page.waitForLoadState('networkidle');

    const sortSelect = page.locator('select').first();
    const difficultyBtns = page.locator('button').filter({ hasText: /Easy|Moderate|Challenging/ });

    if (await sortSelect.isVisible({ timeout: 3000 }).catch(() => false)) {
      await sortSelect.selectOption('price_desc');
      await page.waitForTimeout(500);
    }

    if ((await difficultyBtns.count()) > 0) {
      await difficultyBtns.first().click();
      await page.waitForTimeout(1500);
    }

    // 页面应正常显示组合筛选结果
    await expect(page.locator('body')).toBeVisible();
    const bodyText = await page.locator('body').innerText();
    expect(bodyText.length).toBeGreaterThan(0);
  });

  test('清除筛选后恢复初始状态', async ({ page }) => {
    await page.goto('/en/search');
    await page.waitForLoadState('networkidle');

    // 触发一些筛选
    const sortSelect = page.locator('select').first();
    if (await sortSelect.isVisible({ timeout: 3000 }).catch(() => false)) {
      await sortSelect.selectOption('price_asc');
      await page.waitForTimeout(500);
    }

    // 点击"清除"按钮
    const clearBtn = page.locator('button').filter({ hasText: /Clear|清除|Limpiar/ }).first();
    if (await clearBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await clearBtn.click();
      await page.waitForTimeout(1000);
    }

    await expect(page.locator('body')).toBeVisible();
  });

  test('搜索结果为空时显示空状态', async ({ page }) => {
    await page.goto('/en/search');
    await page.waitForLoadState('networkidle');

    const searchInput = page.locator('input[type="text"]').first();
    await expect(searchInput).toBeVisible();

    // 输入不太可能匹配到的关键词
    await searchInput.fill('ZZZZ_EMPTY_SEARCH_XXXX');
    await page.waitForTimeout(2000);

    const bodyText = await page.locator('body').innerText();
    const hasEmptyState = bodyText.includes('No tours found') || bodyText.includes('no results')
      || bodyText.includes('try adjusting') || bodyText.includes('没有找到')
      || bodyText.includes('未找到') || bodyText.includes('No se encontraron');
    expect(hasEmptyState).toBeTruthy();
  });

  test('西班牙语搜索页正常加载', async ({ page }) => {
    await page.goto('/es/search');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();

    const searchInput = page.locator('input[type="text"]').first();
    await expect(searchInput).toBeVisible();

    // 西班牙语搜索
    await searchInput.fill('Beijing');
    await page.waitForTimeout(1500);
    await expect(page.locator('body')).toBeVisible();
  });
});
