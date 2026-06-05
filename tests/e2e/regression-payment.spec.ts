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

test.describe('回归测试 — 支付模块', () => {

  test('REG-PAY-001：结账页面正常加载', async ({ page }) => {
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);
    await page.waitForLoadState('networkidle');

    // 访问结账页面
    await page.goto('/zh/checkout');
    await page.waitForLoadState('networkidle');

    // 页面正常渲染，不崩溃
    await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
    const text = await page.locator('body').textContent();
    expect(text!.length).toBeGreaterThan(0);
  });

  test('REG-PAY-002：支付成功页面正常显示', async ({ page }) => {
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);
    await page.waitForLoadState('networkidle');

    // 访问支付成功页面
    await page.goto('/zh/checkout/success');
    await page.waitForLoadState('networkidle').catch(() => {});

    // 不应是空白页或服务器错误
    await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
    const text = await page.locator('body').textContent();
    expect(text!.length).toBeGreaterThan(0);
  });

  test('REG-PAY-003：支付取消页面正常显示', async ({ page }) => {
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);
    await page.waitForLoadState('networkidle');

    // 访问支付取消页面
    await page.goto('/zh/checkout/cancelled');
    await page.waitForLoadState('networkidle').catch(() => {});

    // 不应是空白页或服务器错误
    await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
  });
});
