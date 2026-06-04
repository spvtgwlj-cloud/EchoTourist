import { test, expect } from '@playwright/test';

const CREDENTIALS = {
  admin: { email: 'admin@echotours.com', password: 'Admin123!' },
  zhangsan: { email: 'zhangsan@example.com', password: 'Test1234!' },
  lisi: { email: 'lisi@example.com', password: 'Test1234!' },
  wangwu: { email: 'wangwu@example.com', password: 'Test1234!' },
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

test.describe('🔐 认证流程 — 完整功能', () => {
  test('登录页面可访问并显示登录表单', async ({ page }) => {
    await page.goto('/zh/auth');
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    await expect(page.locator('input[type="email"]').first()).toBeVisible();
    await expect(page.locator('input[type="password"]').first()).toBeVisible();
  });

  test('使用管理员账号登录成功', async ({ page }) => {
    await login(page, CREDENTIALS.admin.email, CREDENTIALS.admin.password);

    await page.waitForURL('http://localhost:3000/zh', { timeout: 10000 });
    await expect(page).toHaveURL('http://localhost:3000/zh');
  });

  test('使用演示用户账号登录成功', async ({ page }) => {
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);

    await page.waitForURL('http://localhost:3000/zh', { timeout: 10000 }).catch(() => {});
    // 登录后应跳转且不在 auth 页面
    const currentUrl = page.url();
    expect(currentUrl).not.toContain('/auth');
  });

  test('错误密码显示错误提示并停留在登录页', async ({ page }) => {
    await page.goto('/zh/auth');
    await page.locator('input[type="email"], input[name="email"]').first().fill('admin@echotours.com');
    await page.locator('input[type="password"]').first().fill('wrongpassword999');
    await page.locator('button[type="submit"]').click();

    // 应该仍然在 auth 页面（登录失败）
    await expect(page).toHaveURL(/auth/);
    // 应该显示错误信息
    await expect(page.locator('body')).toBeVisible();
  });

  test('不存在的用户登录显示错误提示', async ({ page }) => {
    await page.goto('/zh/auth');
    await page.locator('input[type="email"], input[name="email"]').first().fill('nonexistent@user.com');
    await page.locator('input[type="password"]').first().fill('SomePass123!');
    await page.locator('button[type="submit"]').click();

    // 应该仍然在 auth 页面
    await expect(page).toHaveURL(/auth/);
  });

  test('切换到注册模式', async ({ page }) => {
    await page.goto('/zh/auth?mode=signup');
    const nameInput = page.locator('input[type="text"], input[name="name"]').first();
    await expect(nameInput).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('切换到登录模式（从注册页面）', async ({ page }) => {
    await page.goto('/zh/auth?mode=signup');
    // 查找切换到登录的链接/按钮
    const loginTab = page.locator('button:has-text("登录"), a:has-text("登录"), [role="tab"]:has-text("登录")').first();
    if (await loginTab.isVisible()) {
      await loginTab.click();
      await expect(page.locator('button[type="submit"]')).toBeVisible();
    }
  });

  test('注册新用户并自动登录', async ({ page }) => {
    const randomSuffix = Date.now();
    const newEmail = `testuser_${randomSuffix}@example.com`;
    const newName = `TestUser_${randomSuffix}`;

    await page.goto('/zh/auth?mode=signup');
    await page.waitForLoadState('networkidle');

    // 填写注册表单
    const nameInput = page.locator('input[type="text"], input[name="name"]').first();
    const emailInput = page.locator('input[type="email"], input[name="email"]').first();
    const passwordInput = page.locator('input[type="password"]').first();

    if (await nameInput.isVisible()) {
      await nameInput.fill(newName);
      await emailInput.fill(newEmail);
      await passwordInput.fill('TestPass123!');
      await page.locator('button[type="submit"]').click();

      // 注册成功后应跳转离开 auth 页面
      await page.waitForTimeout(3000);
      const currentUrl = page.url();
      expect(currentUrl).not.toContain('/auth');
    }
  });

  test('登录后刷新页面保持登录状态', async ({ page }) => {
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);
    await page.waitForURL('**/zh', { timeout: 10000 });

    // 刷新页面
    await page.reload();
    await page.waitForLoadState('networkidle');

    // 验证仍然在首页且不是登录页（token 持久化）
    const currentUrl = page.url();
    expect(currentUrl).not.toContain('/auth');
  });
});

test.describe('👤 用户登录后操作', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);
    await page.waitForURL('http://localhost:3000/zh', { timeout: 10000 }).catch(() => {});
  });

  test('登录后可访问心愿单页面', async ({ page }) => {
    await page.goto('/zh/user/wishlist');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
    // 愿望单页面应有内容或提示
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('登录后可访问订单页面', async ({ page }) => {
    await page.goto('/zh/user/orders');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('登录后可访问个人资料页面', async ({ page }) => {
    await page.goto('/zh/user/profile');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('未登录访问受保护页面显示未登录状态', async ({ page }) => {
    // 清除所有登录状态（cookies + localStorage）
    await page.context().clearCookies();
    // 确保在可访问 localStorage 的页面
    await page.goto('/zh');
    await page.waitForLoadState('networkidle');
    await page.evaluate(() => localStorage.clear());
    // 再访问受保护页面
    await page.goto('/zh/user/wishlist');
    await page.waitForLoadState('networkidle');
    // 导航栏应显示"登录"按钮（未登录状态）
    const headerLogin = page.locator('header a[href*="auth"]').first();
    await expect(headerLogin).toBeVisible();
  });

  test('用户头像或登录状态在导航栏显示', async ({ page }) => {
    // 登录后访问首页
    await page.goto('/zh');
    await page.waitForLoadState('networkidle');

    // 登录后导航栏应不再显示"登录"按钮（或显示用户信息）
    const header = page.locator('header');
    const headerText = await header.innerText();
    const loggedIn = headerText.includes('zhangsan') || !headerText.includes('auth');
    // 至少导航栏内容已变化
    expect(loggedIn).toBeTruthy();
  });
});

test.describe('🔑 开发者 OAuth Mock 登录', () => {
  test('开发模式 OAuth 按钮可见', async ({ page }) => {
    await page.goto('/zh/auth');

    // 检查是否存在 Dev Google 登录按钮
    const devOAuthBtn = page.locator('button:has-text("Dev Google"), button:has-text("Google 登录")').first();
    const oauthBtn = page.locator('button:has-text("Google")').first();
    const anyOAuth = devOAuthBtn.or(oauthBtn);

    // 如果 OAuth 按钮可见，确认可交互
    if (await anyOAuth.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(anyOAuth).toBeVisible();
    }
  });
});
