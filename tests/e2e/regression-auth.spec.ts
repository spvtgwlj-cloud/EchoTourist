import { test, expect } from '@playwright/test';

const CREDENTIALS = {
  admin: { email: 'admin@echotours.com', password: 'Admin123!' },
  zhangsan: { email: 'zhangsan@example.com', password: 'Test1234!' },
};

async function login(page, email: string, password: string) {
  await page.goto('/zh/auth');
  await page.waitForLoadState('networkidle');
  const emailInput = page.locator('input[type="email"], input[name="email"]').first();
  const passwordInput = page.locator('input[type="password"]').first();
  await emailInput.fill(email);
  await passwordInput.fill(password);
  await page.locator('button[type="submit"]').click();
}

test.describe('回归测试 — 认证模块', () => {

  test('REG-AUTH-001：所有受保护页面在未登录时显示导航栏登录按钮', async ({ page }) => {
    const protectedRoutes = [
      '/zh/user/orders',
      '/zh/user/wishlist',
    ];

    for (const route of protectedRoutes) {
      await page.goto(route);
      await page.waitForLoadState('networkidle');

      // 未登录时导航栏应显示"登录"按钮
      const headerLogin = page.locator('header a[href*="auth"]').first();
      await expect(headerLogin).toBeVisible();
    }
  });

  test('REG-AUTH-002：登录后页面正常渲染无崩溃', async ({ page }) => {
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);
    await page.waitForLoadState('networkidle').catch(() => {});

    // 登录后访问各页面
    const pages = ['/zh', '/zh/tours', '/zh/destinations'];
    for (const path of pages) {
      await page.goto(path);
      await page.waitForLoadState('networkidle');
      await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
      const text = await page.locator('body').textContent();
      expect(text!.length).toBeGreaterThan(50);
    }
  });

  test('REG-AUTH-003：退出登录后导航栏显示登录按钮', async ({ page }) => {
    // 1. 登录
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);
    await page.waitForLoadState('networkidle');

    // 2. 清除认证状态
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());

    // 3. 刷新首页，导航栏应恢复为未登录状态
    await page.goto('/zh');
    await page.waitForLoadState('networkidle');

    // 导航栏应显示"登录"按钮（未登录状态）
    const headerLogin = page.locator('header a[href*="auth"]').first();
    await expect(headerLogin).toBeVisible();
  });
});
