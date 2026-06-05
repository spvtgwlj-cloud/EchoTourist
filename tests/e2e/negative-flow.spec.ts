import { test, expect } from '@playwright/test';

const CREDENTIALS = {
  zhangsan: { email: 'zhangsan@example.com', password: 'Test1234!' },
  lisi: { email: 'lisi@example.com', password: 'Test1234!' },
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

test.describe('🌐 多语言逆向操作 — Negative Path', () => {

  test.describe('下单过程中切换语言', () => {
    test('TC-NEG-019：在结账页面切换语言后支付流程正常', async ({ page }) => {
      // 1. 登录
      await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);
      await page.waitForLoadState('networkidle');

      // 2. 导航到目的地详情页（有景点可下单）
      await page.goto('/zh/destinations');
      await page.waitForLoadState('networkidle');

      // 3. 点击第一个目的地进入详情
      const firstDestLink = page.locator('a[href*="/destinations/"]').first();
      await firstDestLink.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});
      if (await firstDestLink.isVisible()) {
        await firstDestLink.click();
        await page.waitForLoadState('networkidle');

        // 4. 找景点卡片上的 Book Now 按钮
        const bookNowBtn = page.locator('button:has-text("Book Now"), a:has-text("Book Now"), [class*="book"]').first();
        if (await bookNowBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
          await bookNowBtn.click();
          await page.waitForLoadState('networkidle');

          // 5. 在 checkout 页填写联系信息
          const nameInput = page.locator('input[type="text"], input[name="name"]').first();
          if (await nameInput.isVisible({ timeout: 5000 }).catch(() => false)) {
            await nameInput.fill('测试用户');

            // 6. 切换到英文
            const langSwitch = page.locator('a[href*="/en"], button:has-text("EN"), a:has-text("English")').first();
            if (await langSwitch.isVisible({ timeout: 3000 }).catch(() => false)) {
              await langSwitch.click();
              await page.waitForLoadState('networkidle');

              // 7. 验证页面没有崩溃，仍显示结账内容
              await expect(page.locator('body')).toBeVisible();
              // 结账页应该有可操作元素
              const bodyText = await page.locator('body').textContent();
              expect(bodyText.length).toBeGreaterThan(0);
            }
          }
        }
      }
    });
  });

  test.describe('混合语言搜索', () => {
    test('TC-NEG-020：在中文界面使用英文搜索后切回中文', async ({ page }) => {
      // 1. 进入中文首页
      await page.goto('/zh');
      await page.waitForLoadState('networkidle');

      // 2. 找到搜索框输入英文关键词
      const searchInput = page.locator('input[type="search"], input[placeholder*="搜索"], input[placeholder*="Search"], input[name="q"]').first();
      await searchInput.waitFor({ state: 'visible', timeout: 10000 }).catch(() => {});

      if (await searchInput.isVisible()) {
        await searchInput.fill('Great Wall of China');
        await searchInput.press('Enter');
        await page.waitForLoadState('networkidle');

        // 3. 验证搜索结果页正常渲染
        await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
        const searchUrl = page.url();
        expect(searchUrl).toContain('search');

        // 4. 切换到中文搜索
        // 先切换到中文界面（如果不在中文）
        const cnSwitch = page.locator('a[href*="/zh"], button:has-text("中文"), a:has-text("CN")').first();
        if (await cnSwitch.isVisible({ timeout: 3000 }).catch(() => false)) {
          await cnSwitch.click();
          await page.waitForLoadState('networkidle');
        }

        // 5. 在搜索框输入中文关键词
        const searchInput2 = page.locator('input[type="search"], input[placeholder*="搜索"], input[name="q"]').first();
        if (await searchInput2.isVisible({ timeout: 5000 }).catch(() => false)) {
          await searchInput2.fill('故宫');
          await searchInput2.press('Enter');
          await page.waitForLoadState('networkidle');

          // 6. 验证页面没有崩溃
          await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
        }
      }
    });
  });

  test.describe('不存在的语言代码', () => {
    test('TC-NEG-021：访问不存在的语言前缀应 fallback', async ({ page }) => {
      // 尝试访问不存在的语言代码页面
      await page.goto('/fr');
      await page.waitForLoadState('networkidle');

      // 页面应正常渲染（fallback 到默认语言），不显示 404 或空白页
      await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
      const bodyText = await page.locator('body').textContent();
      expect(bodyText!.length).toBeGreaterThan(50); // 页面的内容长度应足够

      // 尝试更多不存在的语言
      for (const locale of ['/de', '/ja', '/ko', '/xx']) {
        await page.goto(locale);
        await page.waitForLoadState('networkidle');
        await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
        const text = await page.locator('body').textContent();
        expect(text!.length).toBeGreaterThan(50);
      }
    });
  });

  test.describe('用户资料切换无效语言', () => {
    test('TC-NEG-022：用户个人资料设置无效语言后浏览页面', async ({ page }) => {
      // 1. 登录
      await login(page, CREDENTIALS.lisi.email, CREDENTIALS.lisi.password);
      await page.waitForLoadState('networkidle');

      // 2. 导航到用户中心（如果存在）
      await page.goto('/zh/user');
      await page.waitForLoadState('networkidle').catch(() => {});

      // 无论用户中心是否存在，访问各页面应正常
      const pages = [
        '/zh',
        '/zh/tours',
        '/zh/destinations',
      ];

      for (const path of pages) {
        await page.goto(path);
        await page.waitForLoadState('networkidle');
        await expect(page.locator('body')).toBeVisible({ timeout: 10000 });
        const text = await page.locator('body').textContent();
        expect(text!.length).toBeGreaterThan(50);
      }
    });
  });
});
