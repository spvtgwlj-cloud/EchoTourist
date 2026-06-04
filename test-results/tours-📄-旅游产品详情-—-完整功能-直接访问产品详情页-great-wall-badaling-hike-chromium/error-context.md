# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tours.spec.ts >> 📄 旅游产品详情 — 完整功能 >> 直接访问产品详情页: great-wall-badaling-hike
- Location: tests/e2e/tours.spec.ts:51:9

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/zh/tours/great-wall-badaling-hike
Call log:
  - navigating to "http://localhost:3000/zh/tours/great-wall-badaling-hike", waiting until "load"

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | test.describe('🏛️ 旅游产品列表', () => {
  4   |   test('产品列表页 SSR 渲染显示产品卡片', async ({ page }) => {
  5   |     await page.goto('/zh/tours');
  6   |     await page.waitForLoadState('domcontentloaded');
  7   | 
  8   |     const tourLinks = page.locator('a[href*="/zh/tours/"]:not([href$="/zh/tours"])');
  9   |     await expect(tourLinks.first()).toBeVisible({ timeout: 10000 });
  10  |     const count = await tourLinks.count();
  11  |     expect(count).toBeGreaterThanOrEqual(1);
  12  |   });
  13  | 
  14  |   test('产品卡片显示价格信息', async ({ page }) => {
  15  |     await page.goto('/zh/tours');
  16  |     await page.waitForLoadState('domcontentloaded');
  17  | 
  18  |     const bodyText = await page.locator('body').innerText();
  19  |     const hasPrice = bodyText.includes('¥') || bodyText.includes('$') || bodyText.includes('price');
  20  |     expect(hasPrice).toBeTruthy();
  21  |   });
  22  | 
  23  |   test('点击产品卡片进入详情页', async ({ page }) => {
  24  |     await page.goto('/zh/tours');
  25  | 
  26  |     const tourLink = page.locator('a[href*="/zh/tours/"]:not([href$="/zh/tours"])').first();
  27  |     await expect(tourLink).toBeVisible({ timeout: 10000 });
  28  |     await tourLink.click();
  29  |     await page.waitForURL('**/tours/**');
  30  |     await expect(page.locator('body')).toBeVisible();
  31  |   });
  32  | 
  33  |   test('英文环境产品列表正常显示', async ({ page }) => {
  34  |     await page.goto('/en/tours');
  35  |     await page.waitForLoadState('domcontentloaded');
  36  | 
  37  |     const tourLinks = page.locator('a[href*="/en/tours/"]:not([href$="/en/tours"])');
  38  |     await expect(tourLinks.first()).toBeVisible({ timeout: 10000 });
  39  |   });
  40  | });
  41  | 
  42  | test.describe('📄 旅游产品详情 — 完整功能', () => {
  43  |   const KNOWN_TOURS = [
  44  |     'forbidden-city-royal-walk',
  45  |     'great-wall-badaling-hike',
  46  |     'beijing-essence-3-day',
  47  |     'xian-terracotta-warriors-2day',
  48  |   ];
  49  | 
  50  |   for (const slug of KNOWN_TOURS) {
  51  |     test(`直接访问产品详情页: ${slug}`, async ({ page }) => {
> 52  |       await page.goto(`/zh/tours/${slug}`);
      |                  ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/zh/tours/great-wall-badaling-hike
  53  |       await page.waitForLoadState('networkidle');
  54  |       await expect(page.locator('body')).toBeVisible();
  55  | 
  56  |       // 验证不是 404 页面
  57  |       const bodyText = await page.locator('body').innerText();
  58  |       expect(bodyText.length).toBeGreaterThan(50);
  59  |     });
  60  |   }
  61  | 
  62  |   test('产品详情页显示核心信息', async ({ page }) => {
  63  |     await page.goto('/zh/tours/forbidden-city-royal-walk');
  64  |     await page.waitForLoadState('networkidle');
  65  | 
  66  |     const bodyText = await page.locator('body').innerText();
  67  | 
  68  |     // 应包含价格信息
  69  |     expect(bodyText).toContain('¥');
  70  | 
  71  |     // 应包含预订/购买按钮
  72  |     const hasBookingButton = bodyText.includes('Book') || bodyText.includes('预订')
  73  |       || bodyText.includes('立即');
  74  |     expect(hasBookingButton).toBeTruthy();
  75  |   });
  76  | 
  77  |   test('产品详情页有选择日期选项', async ({ page }) => {
  78  |     await page.goto('/zh/tours/beijing-essence-3-day');
  79  |     await page.waitForLoadState('networkidle');
  80  | 
  81  |     const bodyText = await page.locator('body').innerText();
  82  |     const hasDateOptions = bodyText.includes('Date') || bodyText.includes('日期')
  83  |       || bodyText.includes('出发') || bodyText.includes('团期');
  84  |     expect(hasDateOptions).toBeTruthy();
  85  |   });
  86  | 
  87  |   test('从列表页导航到详情页 URL 格式正确', async ({ page }) => {
  88  |     await page.goto('/zh/tours');
  89  |     await page.waitForLoadState('domcontentloaded');
  90  | 
  91  |     const tourLink = page.locator('a[href*="/zh/tours/"]:not([href$="/zh/tours"])').first();
  92  |     const href = await tourLink.getAttribute('href');
  93  | 
  94  |     expect(href).toMatch(/^\/zh\/tours\//);
  95  |     expect(href?.split('/').pop()).toBeTruthy();
  96  |   });
  97  | 
  98  |   test('英文产品详情页正常工作', async ({ page }) => {
  99  |     await page.goto('/en/tours/forbidden-city-royal-walk');
  100 |     await page.waitForLoadState('networkidle');
  101 |     await expect(page.locator('body')).toBeVisible();
  102 | 
  103 |     const bodyText = await page.locator('body').innerText();
  104 |     const hasPrice = bodyText.includes('$') || bodyText.includes('price') || bodyText.includes('Book');
  105 |     expect(hasPrice).toBeTruthy();
  106 |   });
  107 | });
  108 | 
```