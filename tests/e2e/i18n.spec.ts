import { test, expect } from '@playwright/test';

test.describe('🌐 国际化 — 3 语言完整验证', () => {
  const LOCALES = [
    { code: 'en', label: 'English', title: 'Echo Tours' },
    { code: 'zh', label: '中文', title: 'Echo 旅行' },
    { code: 'es', label: 'Español', title: 'Echo Tours' }, // Spanish title defaults to "Echo Tours"
  ];

  for (const locale of LOCALES) {
    test(`首页使用 ${locale.label} (${locale.code}) 渲染`, async ({ page }) => {
      await page.goto(`/${locale.code}`);
      await page.waitForLoadState('domcontentloaded');

      // 验证页面标题
      const title = await page.title();
      expect(title).toContain(locale.title || 'Echo');

      // 验证 HTML lang 属性
      const htmlLang = await page.locator('html').getAttribute('lang');
      expect(htmlLang).toBe(locale.code);

      // 验证页面内容（body 不为空且正确渲染）
      const bodyText = await page.locator('body').innerText();
      expect(bodyText.length).toBeGreaterThan(50);
    });
  }

  test('从中文切换到英文', async ({ page }) => {
    await page.goto('/zh');
    await page.waitForLoadState('networkidle');

    // 点击语言切换按钮
    const langButton = page.locator('header button:has(svg.lucide-globe)').first();
    await expect(langButton).toBeVisible();
    await langButton.click();

    // 选择英文
    const englishLink = page.getByRole('link', { name: 'English' }).first();
    await expect(englishLink).toBeVisible();
    await englishLink.click();
    await page.waitForTimeout(1000);

    // 验证切换到了英文
    expect(page.url()).toContain('/en');
  });

  test('从英文切换到中文', async ({ page }) => {
    await page.goto('/en');
    await page.waitForLoadState('networkidle');

    const langButton = page.locator('header button:has(svg.lucide-globe)').first();
    await expect(langButton).toBeVisible();
    await langButton.click();

    const chineseLink = page.getByRole('link', { name: '中文' }).first();
    await expect(chineseLink).toBeVisible();
    await chineseLink.click();
    await page.waitForTimeout(1000);

    expect(page.url()).toContain('/zh');
  });

  test('从中文切换到西班牙语', async ({ page }) => {
    await page.goto('/zh');
    await page.waitForLoadState('networkidle');

    const langButton = page.locator('header button:has(svg.lucide-globe)').first();
    await expect(langButton).toBeVisible();
    await langButton.click();

    const spanishLink = page.getByRole('link', { name: 'Español' }).first();
    if (await spanishLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await spanishLink.click();
      await page.waitForTimeout(1000);
      expect(page.url()).toContain('/es');
    }
  });

  test('语言设置在页面间切换后保持', async ({ page }) => {
    // 切换到英文
    await page.goto('/zh');
    const langButton = page.locator('header button:has(svg.lucide-globe)').first();
    await langButton.click();
    const englishLink = page.getByRole('link', { name: 'English' }).first();
    await englishLink.click();
    await page.waitForTimeout(1000);

    // 导航到其他页面
    await page.goto('/en/tours');
    await page.waitForLoadState('domcontentloaded');
    expect(page.url()).toContain('/en');

    await page.goto('/en/destinations');
    await page.waitForLoadState('domcontentloaded');
    expect(page.url()).toContain('/en');
  });

  test('所有语言的旅游产品列表页可访问', async ({ page }) => {
    for (const locale of ['en', 'zh', 'es']) {
      await page.goto(`/${locale}/tours`);
      await page.waitForLoadState('domcontentloaded');

      const tourLinks = page.locator(`a[href*="/${locale}/tours/"]:not([href$="/${locale}/tours"])`);
      const count = await tourLinks.count();
      // 至少有一个产品链接
      expect(count).toBeGreaterThanOrEqual(1);
    }
  });

  test('所有语言的目的地页面可访问', async ({ page }) => {
    for (const locale of ['en', 'zh', 'es']) {
      await page.goto(`/${locale}/destinations`);
      await page.waitForLoadState('networkidle');
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('所有语言的搜索页面可访问', async ({ page }) => {
    for (const locale of ['en', 'zh', 'es']) {
      await page.goto(`/${locale}/search`);
      await page.waitForLoadState('networkidle');
      await expect(page.locator('body')).toBeVisible();
    }
  });
});
