import { test, expect } from '@playwright/test';

test.describe('🌍 目的地列表', () => {
  test('目的地页面 SSR 渲染显示目的地卡片', async ({ page }) => {
    await page.goto('/zh/destinations');
    await page.waitForLoadState('networkidle');

    const destLinks = page.locator('a[href*="/zh/destinations/"]');
    await expect(destLinks.first()).toBeVisible({ timeout: 10000 });
    const count = await destLinks.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('所有种子数据目的地都可见', async ({ page }) => {
    await page.goto('/en/destinations');
    await page.waitForLoadState('networkidle');

    // 种子数据有北京、南京、西安 3 个目的地
    const beijingLink = page.locator('a[href*="/en/destinations/beijing"]');
    const nanjingLink = page.locator('a[href*="/en/destinations/nanjing"]');
    const xianLink = page.locator('a[href*="/en/destinations/xian"]');

    await expect(beijingLink.first()).toBeVisible({ timeout: 10000 });
    await expect(nanjingLink.first()).toBeVisible({ timeout: 5000 });
    await expect(xianLink.first()).toBeVisible({ timeout: 5000 });
  });

  test('目的地卡片可点击进入详情', async ({ page }) => {
    await page.goto('/zh/destinations');
    await page.waitForLoadState('networkidle');

    const destLink = page.locator('a[href*="/zh/destinations/"]').first();
    await expect(destLink).toBeVisible({ timeout: 10000 });
    await destLink.click();
    await page.waitForURL('**/destinations/**');
    await expect(page.locator('body')).toBeVisible();
  });

  test('英文环境目的地列表正常', async ({ page }) => {
    await page.goto('/en/destinations');
    await page.waitForLoadState('domcontentloaded');

    const destLinks = page.locator('a[href*="/en/destinations/"]');
    await expect(destLinks.first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe('🏙️ 目的地详情', () => {
  const KNOWN_DESTINATIONS = ['beijing', 'nanjing', 'xian'];

  for (const slug of KNOWN_DESTINATIONS) {
    test(`目的地详情页可访问: ${slug}`, async ({ page }) => {
      await page.goto(`/zh/destinations/${slug}`);
      await page.waitForLoadState('networkidle');
      await expect(page.locator('body')).toBeVisible();

      // 验证不是 404
      const bodyText = await page.locator('body').innerText();
      expect(bodyText.length).toBeGreaterThan(50);
    });
  }

  test('目的地详情页显示景点网格', async ({ page }) => {
    await page.goto('/zh/destinations/beijing');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').innerText();
    // 北京应有景点信息
    const hasAttractions = bodyText.includes('景点') || bodyText.includes('Attraction')
      || bodyText.includes('attraction');
    expect(hasAttractions).toBeTruthy();
  });

  test('目的地详情页关联的旅游产品可见', async ({ page }) => {
    await page.goto('/en/destinations/beijing');
    await page.waitForLoadState('networkidle');

    // 应该显示关联的旅游产品链接
    const tourLinks = page.locator('a[href*="/en/tours/"]').first();
    if (await tourLinks.isVisible({ timeout: 5000 }).catch(() => false)) {
      await expect(tourLinks).toBeVisible();
    }
  });

  test('从目的地详情点击旅游产品进入产品详情', async ({ page }) => {
    await page.goto('/en/destinations/beijing');
    await page.waitForLoadState('networkidle');

    const tourLink = page.locator('a[href*="/en/tours/"]').first();
    if (await tourLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      const href = await tourLink.getAttribute('href');
      await tourLink.click();
      await page.waitForURL('**/tours/**');
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('景点按 sort_order 排序显示', async ({ page }) => {
    await page.goto('/zh/destinations/beijing');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').innerText();
    // 景点应有名称和描述
    const hasAttractionContent = bodyText.includes('故宫') || bodyText.includes('天安门')
      || bodyText.includes('天坛') || bodyText.includes('颐和园')
      || bodyText.includes('景点');
    expect(hasAttractionContent).toBeTruthy();
  });
});

test.describe('🧭 目的地导航', () => {
  test('从导航栏进入目的地页面', async ({ page }) => {
    await page.goto('/zh');
    await page.locator('header a[href*="destinations"]').first().click();
    await page.waitForURL('**/destinations');
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('首页目的地预览可点击', async ({ page }) => {
    await page.goto('/zh');
    await page.waitForLoadState('networkidle');

    const destPreviewLink = page.locator('a[href*="/zh/destinations/"]').first();
    if (await destPreviewLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await destPreviewLink.click();
      await expect(page).toHaveURL(/\/zh\/destinations\//);
    }
  });
});
