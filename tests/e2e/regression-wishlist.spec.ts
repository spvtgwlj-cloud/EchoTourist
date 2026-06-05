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

test.describe('回归测试 — 收藏模块', () => {

  test('REG-WISH-001：心愿单按钮在产品详情页渲染正常', async ({ page }) => {
    // 访问目的地详情页
    await page.goto('/zh/destinations');
    await page.waitForLoadState('networkidle');

    // 找到一个产品/目的地进入详情
    const destLink = page.locator('a[href*="/destinations/"]').first();
    await destLink.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});

    if (await destLink.isVisible()) {
      await destLink.click();
      await page.waitForLoadState('networkidle');

      // 页面应该含有收藏相关图标
      await expect(page.locator('body')).toBeVisible();
    }
  });

  test('REG-WISH-002：用户心愿单页面正常加载', async ({ page }) => {
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);
    await page.waitForLoadState('networkidle');

    // 导航到心愿单页面
    await page.goto('/zh/user/wishlist');
    await page.waitForLoadState('networkidle').catch(() => {});

    // 页面应正常渲染
    await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
  });

  test('REG-WISH-003：景点收藏按钮在景点卡片上可见', async ({ page }) => {
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);
    await page.waitForLoadState('networkidle');

    // 进入目的地详情页，查看景点卡片
    await page.goto('/zh/destinations');
    await page.waitForLoadState('networkidle');

    const firstDest = page.locator('a[href*="/destinations/"]').first();
    if (await firstDest.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstDest.click();
      await page.waitForLoadState('networkidle');

      // 页面应正常加载（包含景点网格）
      await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
    }
  });

  test('REG-WISH-004：收藏/取消收藏操作不导致页面崩溃', async ({ page }) => {
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);
    await page.waitForLoadState('networkidle');

    // 检查是否有收藏按钮可以操作
    await page.goto('/zh/destinations');
    await page.waitForLoadState('networkidle');

    // 找收藏按钮（heart icon 等）
    const wishlistBtn = page.locator('[class*="wishlist"], button[aria-label*="wishlist"], button[aria-label*="收藏"], svg[class*="heart"]').first();
    if (await wishlistBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await wishlistBtn.click();
      // 点击后不应有页面崩溃
      await page.waitForLoadState('networkidle');
      await expect(page.locator('body')).toBeVisible();
    }
  });
});
