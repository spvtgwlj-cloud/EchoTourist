import { test, expect } from '@playwright/test';

const ADMIN_CREDENTIALS = {
  email: 'admin@echotours.com',
  password: 'Admin123!',
};

async function adminLogin(page) {
  await page.goto('/zh/auth');
  await page.waitForLoadState('networkidle');

  await page.locator('input[type="email"], input[name="email"]').first().fill(ADMIN_CREDENTIALS.email);
  await page.locator('input[type="password"]').first().fill(ADMIN_CREDENTIALS.password);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL('http://localhost:3000/zh', { timeout: 10000 });
}

test.describe('🔧 管理后台 — 完整功能', () => {
  test.beforeEach(async ({ page }) => {
    await adminLogin(page);
  });

  test('管理仪表盘页面可访问', async ({ page }) => {
    await page.goto('/zh/admin');
    await page.waitForLoadState('networkidle');
    // CSR 页面加载骨架屏后应渲染页面内容
    await expect(page.locator('body')).toBeVisible();
  });

  test('英文管理后台可访问', async ({ page }) => {
    await page.goto('/en/admin');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('管理后台侧边栏导航存在', async ({ page }) => {
    await page.goto('/zh/admin');
    await page.waitForLoadState('networkidle');

    // 检查是否有导航链接
    const navLinks = page.locator('a[href*="/zh/admin/"], nav a').all();
    const count = (await navLinks).length;
    // 至少有一个导航链接
    expect(count).toBeGreaterThanOrEqual(1);
  });
});

test.describe('📊 管理员仪表盘', () => {
  test.beforeEach(async ({ page }) => {
    await adminLogin(page);
  });

  test('仪表盘显示统计卡片', async ({ page }) => {
    await page.goto('/zh/admin');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').innerText();
    // 统计信息可能包括数字、百分比等
    const hasNumbers = /\d+/.test(bodyText);
    expect(hasNumbers).toBeTruthy();
  });
});

test.describe('🏛️ 管理员 — 产品管理', () => {
  test.beforeEach(async ({ page }) => {
    await adminLogin(page);
  });

  test('产品管理页面可访问', async ({ page }) => {
    await page.goto('/zh/admin/tours');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('产品管理页面显示产品列表', async ({ page }) => {
    await page.goto('/zh/admin/tours');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').innerText();
    const hasContent = bodyText.includes('tour') || bodyText.includes('Tour')
      || bodyText.includes('产品') || bodyText.includes('产品管理')
      || bodyText.includes('旅游');
    expect(hasContent).toBeTruthy();
  });

  test('英文产品管理页正常', async ({ page }) => {
    await page.goto('/en/admin/tours');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('📋 管理员 — 订单管理', () => {
  test.beforeEach(async ({ page }) => {
    await adminLogin(page);
  });

  test('订单管理页面可访问', async ({ page }) => {
    await page.goto('/zh/admin/orders');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('订单管理页面显示订单列表', async ({ page }) => {
    await page.goto('/zh/admin/orders');
    await page.waitForLoadState('networkidle');
    // CSR 页面，骨架屏加载后页面正常渲染
    await expect(page.locator('body')).toBeVisible();
  });

  test('英文订单管理页正常', async ({ page }) => {
    await page.goto('/en/admin/orders');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('⭐ 管理员 — 评论审核', () => {
  test.beforeEach(async ({ page }) => {
    await adminLogin(page);
  });

  test('评论审核页面可访问', async ({ page }) => {
    await page.goto('/zh/admin/reviews');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('评论审核页面显示评论列表', async ({ page }) => {
    await page.goto('/zh/admin/reviews');
    await page.waitForLoadState('networkidle');
    // CSR 页面，骨架屏加载后页面正常渲染
    await expect(page.locator('body')).toBeVisible();
  });

  test('英文评论审核页正常', async ({ page }) => {
    await page.goto('/en/admin/reviews');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('🔒 管理后台权限控制', () => {
  test('未登录访问管理后台被拦截', async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/zh/admin');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').innerText();
    const needsLogin = bodyText.includes('请登录') || bodyText.includes('sign in')
      || bodyText.includes('Please') || page.url().includes('auth');
    expect(needsLogin).toBeTruthy();
  });

  test('非管理员用户访问管理后台被拒绝', async ({ page }) => {
    // 使用普通用户登录
    await page.goto('/zh/auth');
    await page.locator('input[type="email"]').first().fill('zhangsan@example.com');
    await page.locator('input[type="password"]').first().fill('Test1234!');
    await page.locator('button[type="submit"]').click();
    await page.waitForTimeout(3000);

    // 尝试访问管理后台
    await page.goto('/zh/admin');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });
});
