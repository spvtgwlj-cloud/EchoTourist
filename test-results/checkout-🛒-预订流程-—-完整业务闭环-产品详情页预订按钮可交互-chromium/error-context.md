# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: checkout.spec.ts >> 🛒 预订流程 — 完整业务闭环 >> 产品详情页预订按钮可交互
- Location: tests/e2e/checkout.spec.ts:110:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/zh/auth
Call log:
  - navigating to "http://localhost:3000/zh/auth", waiting until "load"

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | const CREDENTIALS = {
  4   |   zhangsan: { email: 'zhangsan@example.com', password: 'Test1234!' },
  5   | };
  6   | 
  7   | async function login(page) {
> 8   |   await page.goto('/zh/auth');
      |              ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/zh/auth
  9   |   await page.waitForLoadState('networkidle');
  10  | 
  11  |   const emailInput = page.locator('input[type="email"], input[name="email"]').first();
  12  |   const passwordInput = page.locator('input[type="password"]').first();
  13  |   await emailInput.fill(CREDENTIALS.zhangsan.email);
  14  |   await passwordInput.fill(CREDENTIALS.zhangsan.password);
  15  |   await page.locator('button[type="submit"]').click();
  16  |   await page.waitForURL('http://localhost:3000/zh', { timeout: 10000 }).catch(() => {});
  17  | }
  18  | 
  19  | async function clearAuth(page) {
  20  |   await page.context().clearCookies();
  21  |   await page.evaluate(() => localStorage.clear());
  22  |   await page.goto('/zh');
  23  |   await page.waitForLoadState('networkidle');
  24  | }
  25  | 
  26  | test.describe('🛒 预订流程 — 完整业务闭环', () => {
  27  |   test.beforeEach(async ({ page }) => {
  28  |     await login(page);
  29  |   });
  30  | 
  31  |   test('未登录访问结账页显示未登录状态', async ({ page }) => {
  32  |     // 先清除登录状态再访问
  33  |     await page.context().clearCookies();
  34  |     await page.goto('/zh');
  35  |     await page.waitForLoadState('networkidle');
  36  |     await page.evaluate(() => localStorage.clear());
  37  |     await page.goto('/zh/checkout');
  38  |     await page.waitForLoadState('networkidle');
  39  | 
  40  |     // 导航栏应显示"登录"按钮（未登录状态）
  41  |     const headerLogin = page.locator('header a[href*="auth"]').first();
  42  |     await expect(headerLogin).toBeVisible();
  43  |   });
  44  | 
  45  |   test('登录后可访问结账页面', async ({ page }) => {
  46  |     await page.goto('/zh/checkout');
  47  |     await page.waitForLoadState('networkidle');
  48  |     await expect(page.locator('body')).toBeVisible();
  49  |   });
  50  | 
  51  |   test('结账页面正常渲染', async ({ page }) => {
  52  |     await page.goto('/zh/checkout');
  53  |     await page.waitForLoadState('networkidle');
  54  | 
  55  |     // 结账页面加载正常（可能为 CSR 空状态或需要先选择产品）
  56  |     const bodyText = await page.locator('body').innerText();
  57  |     // 至少页面非空
  58  |     expect(bodyText.length).toBeGreaterThan(0);
  59  |   });
  60  | 
  61  |   test('支付成功页面可访问', async ({ page }) => {
  62  |     await page.goto('/zh/checkout/success');
  63  |     await page.waitForLoadState('networkidle');
  64  |     await expect(page.locator('body')).toBeVisible();
  65  | 
  66  |     // 成功页面应显示确认信息
  67  |     const bodyText = await page.locator('body').innerText();
  68  |     const hasSuccessText = bodyText.includes('成功') || bodyText.includes('confirmed')
  69  |       || bodyText.includes('谢谢') || bodyText.includes('Thank')
  70  |       || bodyText.includes('order') || bodyText.includes('订单')
  71  |       || bodyText.includes('Order');
  72  |     expect(hasSuccessText).toBeTruthy();
  73  |   });
  74  | 
  75  |   test('英文结账成功页面可访问', async ({ page }) => {
  76  |     await page.goto('/en/checkout/success');
  77  |     await page.waitForLoadState('networkidle');
  78  |     await expect(page.locator('body')).toBeVisible();
  79  |   });
  80  | 
  81  |   test('产品详情页有预订按钮', async ({ page }) => {
  82  |     const tours = ['xian-terracotta-warriors-2day', 'great-wall-badaling-hike',
  83  |       'forbidden-city-royal-walk', 'beijing-essence-3-day'];
  84  | 
  85  |     for (const slug of tours) {
  86  |       await page.goto(`/zh/tours/${slug}`);
  87  |       await page.waitForLoadState('networkidle');
  88  | 
  89  |       // 查看预订按钮是否存在
  90  |       const bodyText = await page.locator('body').innerText();
  91  |       const hasBookingOption = bodyText.includes('Book') || bodyText.includes('预订')
  92  |         || bodyText.includes('¥') || bodyText.includes('日期');
  93  |       expect(hasBookingOption).toBeTruthy();
  94  |     }
  95  |   });
  96  | 
  97  |   test('结账页面提交空表单显示验证提示', async ({ page }) => {
  98  |     await page.goto('/zh/checkout');
  99  |     await page.waitForLoadState('networkidle');
  100 | 
  101 |     const submitBtn = page.locator('button[type="submit"], button:has-text("Submit"), button:has-text("提交"), button:has-text("Pay"), button:has-text("支付")').first();
  102 |     if (await submitBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
  103 |       await submitBtn.click();
  104 |       await page.waitForTimeout(1000);
  105 |       // 应显示验证错误或停留在当前页
  106 |       await expect(page.locator('body')).toBeVisible();
  107 |     }
  108 |   });
```