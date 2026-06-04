# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: destinations.spec.ts >> 🌍 目的地列表 >> 所有种子数据目的地都可见
- Location: tests/e2e/destinations.spec.ts:14:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/en/destinations
Call log:
  - navigating to "http://localhost:3000/en/destinations", waiting until "load"

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | test.describe('🌍 目的地列表', () => {
  4   |   test('目的地页面 SSR 渲染显示目的地卡片', async ({ page }) => {
  5   |     await page.goto('/zh/destinations');
  6   |     await page.waitForLoadState('networkidle');
  7   | 
  8   |     const destLinks = page.locator('a[href*="/zh/destinations/"]');
  9   |     await expect(destLinks.first()).toBeVisible({ timeout: 10000 });
  10  |     const count = await destLinks.count();
  11  |     expect(count).toBeGreaterThanOrEqual(1);
  12  |   });
  13  | 
  14  |   test('所有种子数据目的地都可见', async ({ page }) => {
> 15  |     await page.goto('/en/destinations');
      |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/en/destinations
  16  |     await page.waitForLoadState('networkidle');
  17  | 
  18  |     // 种子数据有北京、南京、西安 3 个目的地
  19  |     const beijingLink = page.locator('a[href*="/en/destinations/beijing"]');
  20  |     const nanjingLink = page.locator('a[href*="/en/destinations/nanjing"]');
  21  |     const xianLink = page.locator('a[href*="/en/destinations/xian"]');
  22  | 
  23  |     const beijingVisible = await beijingLink.isVisible({ timeout: 5000 }).catch(() => false);
  24  |     const nanjingVisible = await nanjingLink.isVisible({ timeout: 5000 }).catch(() => false);
  25  |     const xianVisible = await xianLink.isVisible({ timeout: 5000 }).catch(() => false);
  26  | 
  27  |     // 至少 2 个目的地可见
  28  |     const visibleCount = [beijingVisible, nanjingVisible, xianVisible].filter(Boolean).length;
  29  |     expect(visibleCount).toBeGreaterThanOrEqual(2);
  30  |   });
  31  | 
  32  |   test('目的地卡片可点击进入详情', async ({ page }) => {
  33  |     await page.goto('/zh/destinations');
  34  |     await page.waitForLoadState('networkidle');
  35  | 
  36  |     const destLink = page.locator('a[href*="/zh/destinations/"]').first();
  37  |     await expect(destLink).toBeVisible({ timeout: 10000 });
  38  |     await destLink.click();
  39  |     await page.waitForURL('**/destinations/**');
  40  |     await expect(page.locator('body')).toBeVisible();
  41  |   });
  42  | 
  43  |   test('英文环境目的地列表正常', async ({ page }) => {
  44  |     await page.goto('/en/destinations');
  45  |     await page.waitForLoadState('domcontentloaded');
  46  | 
  47  |     const destLinks = page.locator('a[href*="/en/destinations/"]');
  48  |     await expect(destLinks.first()).toBeVisible({ timeout: 10000 });
  49  |   });
  50  | });
  51  | 
  52  | test.describe('🏙️ 目的地详情', () => {
  53  |   const KNOWN_DESTINATIONS = ['beijing', 'nanjing', 'xian'];
  54  | 
  55  |   for (const slug of KNOWN_DESTINATIONS) {
  56  |     test(`目的地详情页可访问: ${slug}`, async ({ page }) => {
  57  |       await page.goto(`/zh/destinations/${slug}`);
  58  |       await page.waitForLoadState('networkidle');
  59  |       await expect(page.locator('body')).toBeVisible();
  60  | 
  61  |       // 验证不是 404
  62  |       const bodyText = await page.locator('body').innerText();
  63  |       expect(bodyText.length).toBeGreaterThan(50);
  64  |     });
  65  |   }
  66  | 
  67  |   test('目的地详情页显示景点网格', async ({ page }) => {
  68  |     await page.goto('/zh/destinations/beijing');
  69  |     await page.waitForLoadState('networkidle');
  70  | 
  71  |     const bodyText = await page.locator('body').innerText();
  72  |     // 北京应有景点信息
  73  |     const hasAttractions = bodyText.includes('景点') || bodyText.includes('Attraction')
  74  |       || bodyText.includes('attraction');
  75  |     expect(hasAttractions).toBeTruthy();
  76  |   });
  77  | 
  78  |   test('目的地详情页关联的旅游产品可见', async ({ page }) => {
  79  |     await page.goto('/en/destinations/beijing');
  80  |     await page.waitForLoadState('networkidle');
  81  | 
  82  |     // 应该显示关联的旅游产品链接
  83  |     const tourLinks = page.locator('a[href*="/en/tours/"]').first();
  84  |     if (await tourLinks.isVisible({ timeout: 5000 }).catch(() => false)) {
  85  |       await expect(tourLinks).toBeVisible();
  86  |     }
  87  |   });
  88  | 
  89  |   test('从目的地详情点击旅游产品进入产品详情', async ({ page }) => {
  90  |     await page.goto('/en/destinations/beijing');
  91  |     await page.waitForLoadState('networkidle');
  92  | 
  93  |     const tourLink = page.locator('a[href*="/en/tours/"]').first();
  94  |     if (await tourLink.isVisible({ timeout: 5000 }).catch(() => false)) {
  95  |       const href = await tourLink.getAttribute('href');
  96  |       await tourLink.click();
  97  |       await page.waitForURL('**/tours/**');
  98  |       await expect(page.locator('body')).toBeVisible();
  99  |     }
  100 |   });
  101 | 
  102 |   test('景点按 sort_order 排序显示', async ({ page }) => {
  103 |     await page.goto('/zh/destinations/beijing');
  104 |     await page.waitForLoadState('networkidle');
  105 | 
  106 |     const bodyText = await page.locator('body').innerText();
  107 |     // 景点应有名称和描述
  108 |     const hasAttractionContent = bodyText.includes('故宫') || bodyText.includes('天安门')
  109 |       || bodyText.includes('天坛') || bodyText.includes('颐和园')
  110 |       || bodyText.includes('景点');
  111 |     expect(hasAttractionContent).toBeTruthy();
  112 |   });
  113 | });
  114 | 
  115 | test.describe('🧭 目的地导航', () => {
```