# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: i18n.spec.ts >> 🌐 国际化 — 3 语言完整验证 >> 从中文切换到西班牙语
- Location: tests/e2e/i18n.spec.ts:64:7

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
  3   | test.describe('🌐 国际化 — 3 语言完整验证', () => {
  4   |   const LOCALES = [
  5   |     { code: 'en', label: 'English', title: 'Echo Tours' },
  6   |     { code: 'zh', label: '中文', title: 'Echo 旅行' },
  7   |     { code: 'es', label: 'Español', title: 'Echo Tours' }, // Spanish title defaults to "Echo Tours"
  8   |   ];
  9   | 
  10  |   for (const locale of LOCALES) {
  11  |     test(`首页使用 ${locale.label} (${locale.code}) 渲染`, async ({ page }) => {
  12  |       await page.goto(`/${locale.code}`);
  13  |       await page.waitForLoadState('domcontentloaded');
  14  | 
  15  |       // 验证页面标题
  16  |       const title = await page.title();
  17  |       expect(title).toContain(locale.title || 'Echo');
  18  | 
  19  |       // 验证 HTML lang 属性
  20  |       const htmlLang = await page.locator('html').getAttribute('lang');
  21  |       expect(htmlLang).toBe(locale.code);
  22  | 
  23  |       // 验证页面内容（body 不为空且正确渲染）
  24  |       const bodyText = await page.locator('body').innerText();
  25  |       expect(bodyText.length).toBeGreaterThan(50);
  26  |     });
  27  |   }
  28  | 
  29  |   test('从中文切换到英文', async ({ page }) => {
  30  |     await page.goto('/zh');
  31  |     await page.waitForLoadState('networkidle');
  32  | 
  33  |     // 点击语言切换按钮
  34  |     const langButton = page.locator('header button:has(svg.lucide-globe)').first();
  35  |     await expect(langButton).toBeVisible();
  36  |     await langButton.click();
  37  | 
  38  |     // 选择英文
  39  |     const englishLink = page.getByRole('link', { name: 'English' }).first();
  40  |     await expect(englishLink).toBeVisible();
  41  |     await englishLink.click();
  42  |     await page.waitForTimeout(1000);
  43  | 
  44  |     // 验证切换到了英文
  45  |     expect(page.url()).toContain('/en');
  46  |   });
  47  | 
  48  |   test('从英文切换到中文', async ({ page }) => {
  49  |     await page.goto('/en');
  50  |     await page.waitForLoadState('networkidle');
  51  | 
  52  |     const langButton = page.locator('header button:has(svg.lucide-globe)').first();
  53  |     await expect(langButton).toBeVisible();
  54  |     await langButton.click();
  55  | 
  56  |     const chineseLink = page.getByRole('link', { name: '中文' }).first();
  57  |     await expect(chineseLink).toBeVisible();
  58  |     await chineseLink.click();
  59  |     await page.waitForTimeout(1000);
  60  | 
  61  |     expect(page.url()).toContain('/zh');
  62  |   });
  63  | 
  64  |   test('从中文切换到西班牙语', async ({ page }) => {
> 65  |     await page.goto('/zh');
      |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/zh
  66  |     await page.waitForLoadState('networkidle');
  67  | 
  68  |     const langButton = page.locator('header button:has(svg.lucide-globe)').first();
  69  |     await expect(langButton).toBeVisible();
  70  |     await langButton.click();
  71  | 
  72  |     const spanishLink = page.getByRole('link', { name: 'Español' }).first();
  73  |     if (await spanishLink.isVisible({ timeout: 3000 }).catch(() => false)) {
  74  |       await spanishLink.click();
  75  |       await page.waitForTimeout(1000);
  76  |       expect(page.url()).toContain('/es');
  77  |     }
  78  |   });
  79  | 
  80  |   test('语言设置在页面间切换后保持', async ({ page }) => {
  81  |     // 切换到英文
  82  |     await page.goto('/zh');
  83  |     const langButton = page.locator('header button:has(svg.lucide-globe)').first();
  84  |     await langButton.click();
  85  |     const englishLink = page.getByRole('link', { name: 'English' }).first();
  86  |     await englishLink.click();
  87  |     await page.waitForTimeout(1000);
  88  | 
  89  |     // 导航到其他页面
  90  |     await page.goto('/en/tours');
  91  |     await page.waitForLoadState('domcontentloaded');
  92  |     expect(page.url()).toContain('/en');
  93  | 
  94  |     await page.goto('/en/destinations');
  95  |     await page.waitForLoadState('domcontentloaded');
  96  |     expect(page.url()).toContain('/en');
  97  |   });
  98  | 
  99  |   test('所有语言的旅游产品列表页可访问', async ({ page }) => {
  100 |     for (const locale of ['en', 'zh', 'es']) {
  101 |       await page.goto(`/${locale}/tours`);
  102 |       await page.waitForLoadState('domcontentloaded');
  103 | 
  104 |       const tourLinks = page.locator(`a[href*="/${locale}/tours/"]:not([href$="/${locale}/tours"])`);
  105 |       const count = await tourLinks.count();
  106 |       // 至少有一个产品链接
  107 |       expect(count).toBeGreaterThanOrEqual(1);
  108 |     }
  109 |   });
  110 | 
  111 |   test('所有语言的目的地页面可访问', async ({ page }) => {
  112 |     for (const locale of ['en', 'zh', 'es']) {
  113 |       await page.goto(`/${locale}/destinations`);
  114 |       await page.waitForLoadState('networkidle');
  115 |       await expect(page.locator('body')).toBeVisible();
  116 |     }
  117 |   });
  118 | 
  119 |   test('所有语言的搜索页面可访问', async ({ page }) => {
  120 |     for (const locale of ['en', 'zh', 'es']) {
  121 |       await page.goto(`/${locale}/search`);
  122 |       await page.waitForLoadState('networkidle');
  123 |       await expect(page.locator('body')).toBeVisible();
  124 |     }
  125 |   });
  126 | });
  127 | 
```