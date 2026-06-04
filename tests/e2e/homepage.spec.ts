import { test, expect } from '@playwright/test';

test.describe('🏠 首页 — 完整功能', () => {
  test('页面加载并显示核心元素', async ({ page }) => {
    await page.goto('/zh');

    // 品牌标识
    await expect(page.locator('header')).toContainText('Echo');
    await expect(page.locator('header')).toContainText('Tours');

    // 主导航
    const nav = page.locator('header nav, header [role="navigation"]');
    await expect(nav).toBeVisible();

    // 页脚
    await expect(page.locator('footer')).toBeVisible();

    // Hero 区域
    await expect(page.locator('section').first()).toBeVisible();
  });

  test('首页显示 SSR 渲染的推荐旅游产品', async ({ page }) => {
    await page.goto('/zh');
    await page.waitForLoadState('networkidle');

    const tourLinks = page.locator('a[href*="/zh/tours/"]:not([href$="/zh/tours"])');
    await expect(tourLinks.first()).toBeVisible({ timeout: 10000 });
    const count = await tourLinks.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('Hero 区域 CTA 按钮可点击跳转', async ({ page }) => {
    await page.goto('/zh');

    const cta = page.locator('section a[href*="tours"]').first();
    await expect(cta).toBeVisible();
    await cta.click();
    await page.waitForURL('**/tours');
    await expect(page.locator('h1, [class*="title"]').first()).toBeVisible();
  });

  test('首页有目的地导航入口', async ({ page }) => {
    await page.goto('/zh');
    await page.waitForLoadState('networkidle');

    // 导航到目的地页面（导航链接）
    const destNav = page.locator('header a[href*="destinations"]').first();
    await expect(destNav).toBeVisible();
  });

  test('从首页可导航到注册页', async ({ page }) => {
    await page.goto('/zh');

    const signupLink = page.locator('a[href*="signup"], a[href*="auth?mode=signup"]').first();
    await expect(signupLink).toBeVisible();
    await signupLink.click();
    await expect(page).toHaveURL(/auth/);
  });

  test('品牌 Logo 链接回到首页', async ({ page }) => {
    await page.goto('/zh/tours');

    const logo = page.locator('header a[href="/zh"]').first();
    await expect(logo).toBeVisible();
    await logo.click();
    await expect(page).toHaveURL('http://localhost:3000/zh');
  });
});
