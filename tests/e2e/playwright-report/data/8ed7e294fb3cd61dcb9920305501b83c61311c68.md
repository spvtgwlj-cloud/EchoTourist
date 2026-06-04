# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: homepage.spec.ts >> 🏠 首页 — 完整功能 >> 页面加载并显示核心元素
- Location: tests/e2e/homepage.spec.ts:4:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/zh
Call log:
  - navigating to "http://localhost:3000/zh", waiting until "load"

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('🏠 首页 — 完整功能', () => {
  4  |   test('页面加载并显示核心元素', async ({ page }) => {
> 5  |     await page.goto('/zh');
     |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/zh
  6  | 
  7  |     // 品牌标识
  8  |     await expect(page.locator('header')).toContainText('Echo');
  9  |     await expect(page.locator('header')).toContainText('Tours');
  10 | 
  11 |     // 主导航
  12 |     const nav = page.locator('header nav, header [role="navigation"]');
  13 |     await expect(nav).toBeVisible();
  14 | 
  15 |     // 页脚
  16 |     await expect(page.locator('footer')).toBeVisible();
  17 | 
  18 |     // Hero 区域
  19 |     await expect(page.locator('section').first()).toBeVisible();
  20 |   });
  21 | 
  22 |   test('首页显示 SSR 渲染的推荐旅游产品', async ({ page }) => {
  23 |     await page.goto('/zh');
  24 |     await page.waitForLoadState('networkidle');
  25 | 
  26 |     const tourLinks = page.locator('a[href*="/zh/tours/"]:not([href$="/zh/tours"])');
  27 |     await expect(tourLinks.first()).toBeVisible({ timeout: 10000 });
  28 |     const count = await tourLinks.count();
  29 |     expect(count).toBeGreaterThanOrEqual(1);
  30 |   });
  31 | 
  32 |   test('Hero 区域 CTA 按钮可点击跳转', async ({ page }) => {
  33 |     await page.goto('/zh');
  34 | 
  35 |     const cta = page.locator('section a[href*="tours"]').first();
  36 |     await expect(cta).toBeVisible();
  37 |     await cta.click();
  38 |     await page.waitForURL('**/tours');
  39 |     await expect(page.locator('h1, [class*="title"]').first()).toBeVisible();
  40 |   });
  41 | 
  42 |   test('首页有目的地导航入口', async ({ page }) => {
  43 |     await page.goto('/zh');
  44 |     await page.waitForLoadState('networkidle');
  45 | 
  46 |     // 导航到目的地页面（导航链接）
  47 |     const destNav = page.locator('header a[href*="destinations"]').first();
  48 |     await expect(destNav).toBeVisible();
  49 |   });
  50 | 
  51 |   test('从首页可导航到注册页', async ({ page }) => {
  52 |     await page.goto('/zh');
  53 | 
  54 |     const signupLink = page.locator('a[href*="signup"], a[href*="auth?mode=signup"]').first();
  55 |     await expect(signupLink).toBeVisible();
  56 |     await signupLink.click();
  57 |     await expect(page).toHaveURL(/auth/);
  58 |   });
  59 | 
  60 |   test('品牌 Logo 链接回到首页', async ({ page }) => {
  61 |     await page.goto('/zh/tours');
  62 | 
  63 |     const logo = page.locator('header a[href="/zh"]').first();
  64 |     await expect(logo).toBeVisible();
  65 |     await logo.click();
  66 |     await expect(page).toHaveURL('http://localhost:3000/zh');
  67 |   });
  68 | });
  69 | 
```