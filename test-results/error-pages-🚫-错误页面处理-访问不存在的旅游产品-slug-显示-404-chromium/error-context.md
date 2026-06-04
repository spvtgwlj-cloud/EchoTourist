# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: error-pages.spec.ts >> 🚫 错误页面处理 >> 访问不存在的旅游产品 slug 显示 404
- Location: tests/e2e/error-pages.spec.ts:26:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/zh/tours/nonexistent-tour-slug-xyz
Call log:
  - navigating to "http://localhost:3000/zh/tours/nonexistent-tour-slug-xyz", waiting until "load"

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('🚫 错误页面处理', () => {
  4  |   test('访问不存在的页面显示 404', async ({ page }) => {
  5  |     await page.goto('/zh/nonexistent-page-xyz-123');
  6  |     await page.waitForLoadState('networkidle');
  7  | 
  8  |     const bodyText = await page.locator('body').innerText();
  9  |     // 应包含 404 或 not found 相关提示
  10 |     const has404 = bodyText.includes('404') || bodyText.includes('not found')
  11 |       || bodyText.includes('Not Found') || bodyText.includes('找不到')
  12 |       || bodyText.includes('不存在') || bodyText.includes('页面');
  13 |     expect(has404).toBeTruthy();
  14 |   });
  15 | 
  16 |   test('英文下访问不存在的页面显示 404', async ({ page }) => {
  17 |     await page.goto('/en/nonexistent-page-xyz-123');
  18 |     await page.waitForLoadState('networkidle');
  19 | 
  20 |     const bodyText = await page.locator('body').innerText();
  21 |     const has404 = bodyText.includes('404') || bodyText.includes('not found')
  22 |       || bodyText.includes('Not Found') || bodyText.includes('找不到');
  23 |     expect(has404).toBeTruthy();
  24 |   });
  25 | 
  26 |   test('访问不存在的旅游产品 slug 显示 404', async ({ page }) => {
> 27 |     await page.goto('/zh/tours/nonexistent-tour-slug-xyz');
     |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/zh/tours/nonexistent-tour-slug-xyz
  28 |     await page.waitForLoadState('networkidle');
  29 | 
  30 |     const bodyText = await page.locator('body').innerText();
  31 |     const has404 = bodyText.includes('404') || bodyText.includes('not found')
  32 |       || bodyText.includes('Not Found') || bodyText.includes('找不到');
  33 |     // 可能是 404 或 API 错误提示
  34 |     expect(has404 || bodyText.includes('Error') || bodyText.includes('错误')).toBeTruthy();
  35 |   });
  36 | 
  37 |   test('访问不存在的目的地 slug 显示 404', async ({ page }) => {
  38 |     await page.goto('/zh/destinations/nonexistent-dest-slug');
  39 |     await page.waitForLoadState('networkidle');
  40 | 
  41 |     const bodyText = await page.locator('body').innerText();
  42 |     const has404 = bodyText.includes('404') || bodyText.includes('not found')
  43 |       || bodyText.includes('Not Found') || bodyText.includes('找不到');
  44 |     expect(has404).toBeTruthy();
  45 |   });
  46 | 
  47 |   test('404 页面有返回首页的链接', async ({ page }) => {
  48 |     await page.goto('/zh/nonexistent-page-xyz-123');
  49 |     await page.waitForLoadState('networkidle');
  50 | 
  51 |     // 查找能返回首页的链接或按钮
  52 |     const homeLink = page.locator('a[href="/zh"], a[href="/en"], a[href="/"]').first();
  53 |     if (await homeLink.isVisible({ timeout: 3000 }).catch(() => false)) {
  54 |       await homeLink.click();
  55 |       await expect(page).toHaveURL(/\/zh$|\/en$|\/$/);
  56 |     }
  57 |   });
  58 | 
  59 |   test('西班牙语下 404 正常工作', async ({ page }) => {
  60 |     await page.goto('/es/nonexistent-page-xyz-123');
  61 |     await page.waitForLoadState('networkidle');
  62 |     await expect(page.locator('body')).toBeVisible();
  63 |   });
  64 | });
  65 | 
  66 | test.describe('🔗 无效路由处理', () => {
  67 |   test('访问无效的 locale 前缀', async ({ page }) => {
  68 |     await page.goto('/xx/some-page');
  69 |     await page.waitForLoadState('networkidle');
  70 |     // 应该优雅处理，不崩溃
  71 |     await expect(page.locator('body')).toBeVisible();
  72 |   });
  73 | 
  74 |   test('访问管理后台不存在的子页面', async ({ page }) => {
  75 |     await page.goto('/zh/admin/nonexistent-sub-page');
  76 |     await page.waitForLoadState('networkidle');
  77 |     await expect(page.locator('body')).toBeVisible();
  78 |   });
  79 | 
  80 |   test('深度嵌套的不存在路径', async ({ page }) => {
  81 |     await page.goto('/zh/a/b/c/d/e/f/g');
  82 |     await page.waitForLoadState('networkidle');
  83 |     await expect(page.locator('body')).toBeVisible();
  84 |   });
  85 | });
  86 | 
```