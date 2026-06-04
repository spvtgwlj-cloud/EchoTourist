# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: search.spec.ts >> 🔍 搜索功能 — 完整流程 >> 中文搜索返回结果
- Location: tests/e2e/search.spec.ts:19:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/zh/search
Call log:
  - navigating to "http://localhost:3000/zh/search", waiting until "load"

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test.describe('🔍 搜索功能 — 完整流程', () => {
  4  |   test('搜索页面可正常加载', async ({ page }) => {
  5  |     await page.goto('/zh/search');
  6  |     await page.waitForLoadState('networkidle');
  7  |     await expect(page.locator('body')).toBeVisible();
  8  |   });
  9  | 
  10 |   test('搜索输入框存在且可交互', async ({ page }) => {
  11 |     await page.goto('/zh/search');
  12 |     await page.waitForLoadState('networkidle');
  13 | 
  14 |     const searchInput = page.locator('input[type="text"], input[placeholder*="搜索"], input[placeholder*="Search"], input[placeholder*="buscar"]').first();
  15 |     await expect(searchInput).toBeVisible();
  16 |     await expect(searchInput).toBeEnabled();
  17 |   });
  18 | 
  19 |   test('中文搜索返回结果', async ({ page }) => {
> 20 |     await page.goto('/zh/search');
     |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/zh/search
  21 |     await page.waitForLoadState('networkidle');
  22 | 
  23 |     const searchInput = page.locator('input[type="text"], input[placeholder*="搜索"], input[placeholder*="Search"]').first();
  24 |     await expect(searchInput).toBeVisible();
  25 | 
  26 |     await searchInput.fill('故宫');
  27 |     await page.waitForTimeout(2000); // 等待防抖搜索
  28 | 
  29 |     // 检查是否有搜索结果（可能为空但页面应正常响应）
  30 |     await expect(page.locator('body')).toBeVisible();
  31 |   });
  32 | 
  33 |   test('英文搜索返回结果', async ({ page }) => {
  34 |     await page.goto('/en/search');
  35 |     await page.waitForLoadState('networkidle');
  36 | 
  37 |     const searchInput = page.locator('input[type="text"], input[placeholder*="Search"], input[placeholder*="搜索"]').first();
  38 |     await expect(searchInput).toBeVisible();
  39 | 
  40 |     await searchInput.fill('Forbidden City');
  41 |     await page.waitForTimeout(2000);
  42 | 
  43 |     await expect(page.locator('body')).toBeVisible();
  44 |   });
  45 | 
  46 |   test('搜索页面有筛选或排序选项', async ({ page }) => {
  47 |     await page.goto('/en/search');
  48 |     await page.waitForLoadState('networkidle');
  49 | 
  50 |     // 检查是否有 select/dropdown 或过滤按钮
  51 |     const filterSelect = page.locator('select, [role="combobox"], button:has-text("Filter"), button:has-text("Sort"), button:has-text("筛选"), button:has-text("排序")').first();
  52 |     if (await filterSelect.isVisible({ timeout: 3000 }).catch(() => false)) {
  53 |       await expect(filterSelect).toBeEnabled();
  54 |     }
  55 |   });
  56 | 
  57 |   test('搜索结果可点击进入详情', async ({ page }) => {
  58 |     await page.goto('/en/search');
  59 |     await page.waitForLoadState('networkidle');
  60 | 
  61 |     const searchInput = page.locator('input[type="text"], input[placeholder*="Search"], input[placeholder*="搜索"]').first();
  62 |     await searchInput.fill('Beijing');
  63 |     await page.waitForTimeout(2000);
  64 | 
  65 |     // 如果出现结果链接，点击进入详情
  66 |     const resultLink = page.locator('a[href*="/en/tours/"]').first();
  67 |     if (await resultLink.isVisible({ timeout: 5000 }).catch(() => false)) {
  68 |       await resultLink.click();
  69 |       await page.waitForURL('**/tours/**');
  70 |       await expect(page.locator('body')).toBeVisible();
  71 |     }
  72 |   });
  73 | 
  74 |   test('搜索后清除输入恢复到初始状态', async ({ page }) => {
  75 |     await page.goto('/zh/search');
  76 |     await page.waitForLoadState('networkidle');
  77 | 
  78 |     const searchInput = page.locator('input[type="text"], input[placeholder*="搜索"], input[placeholder*="Search"]').first();
  79 |     await expect(searchInput).toBeVisible();
  80 | 
  81 |     // 输入后清除
  82 |     await searchInput.fill('故宫');
  83 |     await page.waitForTimeout(500);
  84 |     await searchInput.clear();
  85 |     await page.waitForTimeout(500);
  86 | 
  87 |     // 页面应正常显示
  88 |     await expect(page.locator('body')).toBeVisible();
  89 |   });
  90 | });
  91 | 
```