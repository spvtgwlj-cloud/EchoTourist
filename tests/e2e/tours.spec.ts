import { test, expect } from '@playwright/test';

test.describe('🏛️ 旅游产品列表', () => {
  test('产品列表页 SSR 渲染显示产品卡片', async ({ page }) => {
    await page.goto('/zh/tours');
    await page.waitForLoadState('domcontentloaded');

    const tourLinks = page.locator('a[href*="/zh/tours/"]:not([href$="/zh/tours"])');
    await expect(tourLinks.first()).toBeVisible({ timeout: 10000 });
    const count = await tourLinks.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('产品卡片显示价格信息', async ({ page }) => {
    await page.goto('/zh/tours');
    await page.waitForLoadState('domcontentloaded');

    const bodyText = await page.locator('body').innerText();
    const hasPrice = bodyText.includes('¥') || bodyText.includes('$') || bodyText.includes('price');
    expect(hasPrice).toBeTruthy();
  });

  test('点击产品卡片进入详情页', async ({ page }) => {
    await page.goto('/zh/tours');

    const tourLink = page.locator('a[href*="/zh/tours/"]:not([href$="/zh/tours"])').first();
    await expect(tourLink).toBeVisible({ timeout: 10000 });
    await tourLink.click();
    await page.waitForURL('**/tours/**');
    await expect(page.locator('body')).toBeVisible();
  });

  test('英文环境产品列表正常显示', async ({ page }) => {
    await page.goto('/en/tours');
    await page.waitForLoadState('domcontentloaded');

    const tourLinks = page.locator('a[href*="/en/tours/"]:not([href$="/en/tours"])');
    await expect(tourLinks.first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe('📄 旅游产品详情 — 完整功能', () => {
  const KNOWN_TOURS = [
    'forbidden-city-royal-walk',
    'great-wall-badaling-hike',
    'beijing-essence-3-day',
    'xian-terracotta-warriors-2day',
  ];

  for (const slug of KNOWN_TOURS) {
    test(`直接访问产品详情页: ${slug}`, async ({ page }) => {
      await page.goto(`/zh/tours/${slug}`);
      await page.waitForLoadState('networkidle');
      await expect(page.locator('body')).toBeVisible();

      // 验证不是 404 页面
      const bodyText = await page.locator('body').innerText();
      expect(bodyText.length).toBeGreaterThan(50);
    });
  }

  test('产品详情页显示核心信息', async ({ page }) => {
    await page.goto('/zh/tours/forbidden-city-royal-walk');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').innerText();

    // 应包含价格信息
    expect(bodyText).toContain('¥');

    // 应包含预订/购买按钮
    const hasBookingButton = bodyText.includes('Book') || bodyText.includes('预订')
      || bodyText.includes('立即');
    expect(hasBookingButton).toBeTruthy();
  });

  test('产品详情页有选择日期选项', async ({ page }) => {
    await page.goto('/zh/tours/beijing-essence-3-day');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').innerText();
    const hasDateOptions = bodyText.includes('Date') || bodyText.includes('日期')
      || bodyText.includes('出发') || bodyText.includes('团期');
    expect(hasDateOptions).toBeTruthy();
  });

  test('从列表页导航到详情页 URL 格式正确', async ({ page }) => {
    await page.goto('/zh/tours');
    await page.waitForLoadState('domcontentloaded');

    const tourLink = page.locator('a[href*="/zh/tours/"]:not([href$="/zh/tours"])').first();
    const href = await tourLink.getAttribute('href');

    expect(href).toMatch(/^\/zh\/tours\//);
    expect(href?.split('/').pop()).toBeTruthy();
  });

  test('英文产品详情页正常工作', async ({ page }) => {
    await page.goto('/en/tours/forbidden-city-royal-walk');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();

    const bodyText = await page.locator('body').innerText();
    const hasPrice = bodyText.includes('$') || bodyText.includes('price') || bodyText.includes('Book');
    expect(hasPrice).toBeTruthy();
  });
});
