# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: user-center.spec.ts >> 📦 用户订单管理 >> 订单页面内容正常显示
- Location: tests/e2e/user-center.spec.ts:63:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/zh
Call log:
  - navigating to "http://localhost:3000/zh", waiting until "load"

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | const CREDENTIALS = {
  4   |   zhangsan: { email: 'zhangsan@example.com', password: 'Test1234!' },
  5   |   lisi: { email: 'lisi@example.com', password: 'Test1234!' },
  6   | };
  7   | 
  8   | async function login(page, email: string, password: string, clearFirst = false) {
  9   |   if (clearFirst) {
  10  |     await page.context().clearCookies();
> 11  |     await page.goto('/zh');
      |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/zh
  12  |     await page.waitForLoadState('networkidle');
  13  |     await page.evaluate(() => localStorage.clear()).catch(() => {});
  14  |   }
  15  | 
  16  |   await page.goto('/zh/auth');
  17  |   await page.waitForLoadState('networkidle');
  18  | 
  19  |   // 如果已登录（无密码输入框），直接返回
  20  |   const passwordInput = page.locator('input[type="password"]').first();
  21  |   if (!(await passwordInput.isVisible({ timeout: 2000 }).catch(() => false))) {
  22  |     return;
  23  |   }
  24  | 
  25  |   const emailInput = page.locator('input[type="email"], input[name="email"]').first();
  26  |   await emailInput.fill(email);
  27  |   await passwordInput.fill(password);
  28  |   await page.locator('button[type="submit"]').click();
  29  |   await page.waitForTimeout(2000);
  30  | }
  31  | 
  32  | async function isLoggedIn(page): Promise<boolean> {
  33  |   // 检查导航栏是否有"登录"链接 — 如果没有说明已登录
  34  |   const loginLink = page.locator('header a[href*="auth"]').first();
  35  |   return !(await loginLink.isVisible({ timeout: 2000 }).catch(() => false));
  36  | }
  37  | 
  38  | test.describe('📦 用户订单管理', () => {
  39  |   test.beforeEach(async ({ page }) => {
  40  |     await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password, true);
  41  |   });
  42  | 
  43  |   test('订单页面可访问', async ({ page }) => {
  44  |     await page.goto('/zh/user/orders');
  45  |     await page.waitForLoadState('networkidle');
  46  |     await expect(page.locator('body')).toBeVisible();
  47  |   });
  48  | 
  49  |   test('英文环境下订单页正常', async ({ page }) => {
  50  |     await page.goto('/en/user/orders');
  51  |     await page.waitForLoadState('networkidle');
  52  |     await expect(page.locator('body')).toBeVisible();
  53  |   });
  54  | 
  55  |   test('不同用户登录后订单视图不同', async ({ page }) => {
  56  |     await login(page, CREDENTIALS.lisi.email, CREDENTIALS.lisi.password, true);
  57  | 
  58  |     await page.goto('/zh/user/orders');
  59  |     await page.waitForLoadState('networkidle');
  60  |     await expect(page.locator('body')).toBeVisible();
  61  |   });
  62  | 
  63  |   test('订单页面内容正常显示', async ({ page }) => {
  64  |     await page.goto('/zh/user/orders');
  65  |     await page.waitForLoadState('networkidle');
  66  |     // 页面应有内容（订单列表或空状态）
  67  |     const bodyText = await page.locator('body').innerText();
  68  |     expect(bodyText.length).toBeGreaterThan(10);
  69  |   });
  70  | });
  71  | 
  72  | test.describe('👤 个人资料管理', () => {
  73  |   test.beforeEach(async ({ page }) => {
  74  |     await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password, true);
  75  |   });
  76  | 
  77  |   test('个人资料页面可访问', async ({ page }) => {
  78  |     await page.goto('/zh/user/profile');
  79  |     await page.waitForLoadState('networkidle');
  80  |     await expect(page.locator('body')).toBeVisible();
  81  |   });
  82  | 
  83  |   test('英文个人资料页正常', async ({ page }) => {
  84  |     await page.goto('/en/user/profile');
  85  |     await page.waitForLoadState('networkidle');
  86  |     await expect(page.locator('body')).toBeVisible();
  87  |   });
  88  | 
  89  |   test('个人资料页显示用户基本信息', async ({ page }) => {
  90  |     await page.goto('/zh/user/profile');
  91  |     await page.waitForLoadState('networkidle');
  92  | 
  93  |     const bodyText = await page.locator('body').innerText();
  94  |     const hasUserInfo = bodyText.includes('zhangsan')
  95  |       || bodyText.includes('profile') || bodyText.includes('Profile')
  96  |       || bodyText.includes('资料') || bodyText.includes('邮箱')
  97  |       || bodyText.includes('name') || bodyText.includes('Name');
  98  |     expect(hasUserInfo || bodyText.length > 50).toBeTruthy();
  99  |   });
  100 | });
  101 | 
  102 | test.describe('❤️ 心愿单管理', () => {
  103 |   test.beforeEach(async ({ page }) => {
  104 |     await login(page, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password, true);
  105 |   });
  106 | 
  107 |   test('心愿单页面可访问', async ({ page }) => {
  108 |     await page.goto('/zh/user/wishlist');
  109 |     await page.waitForLoadState('networkidle');
  110 |     await expect(page.locator('body')).toBeVisible();
  111 |   });
```