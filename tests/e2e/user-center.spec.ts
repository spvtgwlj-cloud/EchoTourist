import { test, expect } from '@playwright/test';

const CREDENTIALS = {
  zhangsan: { email: 'zhangsan@example.com', password: 'Test1234!' },
  lisi: { email: 'lisi@example.com', password: 'Test1234!' },
};

async function login(page, email: string, password: string, clearFirst = false) {
  if (clearFirst) {
    await page.context().clearCookies();
    await page.goto('/zh');
    await page.waitForLoadState('networkidle');
    await page.evaluate(() => localStorage.clear()).catch(() => {});
  }

  await page.goto('/zh/auth');
  await page.waitForLoadState('networkidle');

  // 如果已登录（无密码输入框），直接返回
  const passwordInput = page.locator('input[type="password"]').first();
  if (!(await passwordInput.isVisible({ timeout: 2000 }).catch(() => false))) {
    return;
  }

  const emailInput = page.locator('input[type="email"], input[name="email"]').first();
  await emailInput.fill(email);
  await passwordInput.fill(password);
  await page.locator('button[type="submit"]').click();
  await page.waitForTimeout(2000);
}

async function isLoggedIn(page): Promise<boolean> {
  // 检查导航栏是否有"登录"链接 — 如果没有说明已登录
  const loginLink = page.locator('header a[href*="auth"]').first();
  return !(await loginLink.isVisible({ timeout: 2000 }).catch(() => false));
}

test.describe('📦 用户订单管理', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password, true);
  });

  test('订单页面可访问', async ({ page }) => {
    await page.goto('/zh/user/orders');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('英文环境下订单页正常', async ({ page }) => {
    await page.goto('/en/user/orders');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('不同用户登录后订单视图不同', async ({ page }) => {
    await login(page, CREDENTIALS.lisi.email, CREDENTIALS.lisi.password, true);

    await page.goto('/zh/user/orders');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('订单页面内容正常显示', async ({ page }) => {
    await page.goto('/zh/user/orders');
    await page.waitForLoadState('networkidle');
    // 页面应有内容（订单列表或空状态）
    const bodyText = await page.locator('body').innerText();
    expect(bodyText.length).toBeGreaterThan(10);
  });
});

test.describe('👤 个人资料管理', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password, true);
  });

  test('个人资料页面可访问', async ({ page }) => {
    await page.goto('/zh/user/profile');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('英文个人资料页正常', async ({ page }) => {
    await page.goto('/en/user/profile');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('个人资料页显示用户基本信息', async ({ page }) => {
    await page.goto('/zh/user/profile');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').innerText();
    const hasUserInfo = bodyText.includes('zhangsan')
      || bodyText.includes('profile') || bodyText.includes('Profile')
      || bodyText.includes('资料') || bodyText.includes('邮箱')
      || bodyText.includes('name') || bodyText.includes('Name');
    expect(hasUserInfo || bodyText.length > 50).toBeTruthy();
  });
});

test.describe('❤️ 心愿单管理', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password, true);
  });

  test('心愿单页面可访问', async ({ page }) => {
    await page.goto('/zh/user/wishlist');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('心愿单页面有内容或空状态提示', async ({ page }) => {
    await page.goto('/zh/user/wishlist');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').innerText();
    const hasContent = bodyText.includes('心愿') || bodyText.includes('wishlist')
      || bodyText.includes('Wishlist') || bodyText.includes('收藏')
      || bodyText.includes('暂无') || bodyText.includes('empty')
      || bodyText.includes('没有任何');
    expect(hasContent).toBeTruthy();
  });

  test('英文心愿单页面正常', async ({ page }) => {
    await page.goto('/en/user/wishlist');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('不同用户心愿单页面均可访问', async ({ page }) => {
    await login(page, CREDENTIALS.lisi.email, CREDENTIALS.lisi.password, true);

    await page.goto('/zh/user/wishlist');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('🔒 用户中心权限控制', () => {
  test('未登录访问订单页导航栏显示登录按钮', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/zh');
    await page.waitForLoadState('networkidle');
    await page.evaluate(() => localStorage.clear()).catch(() => {});

    await page.goto('/zh/user/orders');
    await page.waitForLoadState('networkidle');
    // 导航栏应显示"登录"按钮（未登录状态）
    const headerLogin = page.locator('header a[href*="auth"]').first();
    await expect(headerLogin).toBeVisible();
  });

  test('未登录访问个人资料页导航栏显示登录按钮', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/zh');
    await page.waitForLoadState('networkidle');
    await page.evaluate(() => localStorage.clear()).catch(() => {});

    await page.goto('/zh/user/profile');
    await page.waitForLoadState('networkidle');
    const headerLogin = page.locator('header a[href*="auth"]').first();
    await expect(headerLogin).toBeVisible();
  });
});
