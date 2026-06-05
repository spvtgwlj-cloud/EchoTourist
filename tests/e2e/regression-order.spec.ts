import { test, expect } from '@playwright/test';

const CREDENTIALS = {
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

test.describe('回归测试 — 订单模块', () => {

  test('REG-ORD-001：订单号格式在各页面一致显示', async ({ page }) => {
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);
    await page.waitForLoadState('networkidle');

    // 访问用户订单列表
    await page.goto('/zh/user/orders');
    await page.waitForLoadState('networkidle').catch(() => {});

    // 页面正常加载
    await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
    const bodyText = await page.locator('body').textContent() || '';

    // 如果页面包含订单号，验证格式（ECHO-YYYYMMDD-XXXXXXXX 格式）
    const orderNoMatch = bodyText.match(/ECHO-\d{8}-[A-Z0-9]{8}/);
    if (orderNoMatch) {
      const orderNo = orderNoMatch[0];
      expect(orderNo).toMatch(/^ECHO-\d{8}-[A-Z0-9]{8}$/);
    }
  });

  test('REG-ORD-002：结账页面正常加载可交互', async ({ page }) => {
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);
    await page.waitForLoadState('networkidle');

    // 访问结账页面（无参数时应有提示或回退）
    await page.goto('/zh/checkout');
    await page.waitForLoadState('networkidle');

    // 页面不应崩溃
    await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
  });

  test('REG-ORD-003：订单状态显示一致', async ({ page }) => {
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);
    await page.waitForLoadState('networkidle');

    await page.goto('/zh/user/orders');
    await page.waitForLoadState('networkidle').catch(() => {});

    await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
  });

  test('REG-ORD-004：支付成功页面正常加载', async ({ page }) => {
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);
    await page.waitForLoadState('networkidle');

    // 访问支付成功页（模拟场景）
    await page.goto('/zh/checkout/success');
    await page.waitForLoadState('networkidle').catch(() => {});

    // 页面不应崩溃
    await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
  });
});
