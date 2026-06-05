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

  test('REG-AUTH-001：所有受保护页面在未登录时跳转到登录页', async ({ page }) => {
    const protectedRoutes = [
      '/zh/user',
      '/zh/user/orders',
      '/zh/user/wishlist',
    ];

    for (const route of protectedRoutes) {
      await page.goto(route);
      await page.waitForLoadState('networkidle');

      // 未登录时应跳转到登录页或显示登录提示
      const currentUrl = page.url();
      const isOnLogin = currentUrl.includes('/auth')
        || currentUrl.includes('/login')
        || currentUrl.includes('signin');
      const hasLoginForm = await page.locator('input[type="email"], input[name="email"]').first().isVisible()
        .catch(() => false);

      // 至少满足一个条件：已跳转或页面上有登录元素
      expect(isOnLogin || hasLoginForm).toBeTruthy();
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

  test('REG-AUTH-003：退出登录后受保护页面不可访问', async ({ page }) => {
    // 1. 登录
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);
    await page.waitForLoadState('networkidle');

    // 2. 清除认证状态
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());

    // 3. 尝试访问用户中心
    await page.goto('/zh/user');
    await page.waitForLoadState('networkidle');

    // 应跳转到登录或显示未登录提示
    const currentUrl = page.url();
    const redirected = currentUrl.includes('/auth')
      || currentUrl.includes('/login')
      || currentUrl.includes('signin');
    expect(redirected).toBeTruthy();
  });
});
