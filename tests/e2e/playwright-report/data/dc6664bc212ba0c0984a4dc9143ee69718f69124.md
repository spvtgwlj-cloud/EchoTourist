# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin.spec.ts >> ⭐ 管理员 — 评论审核 >> 评论审核页面显示评论列表
- Location: tests/e2e/admin.spec.ts:129:7

# Error details

```
TimeoutError: page.waitForURL: Timeout 10000ms exceeded.
=========================== logs ===========================
waiting for navigation to "http://localhost:3000/zh" until "load"
============================================================
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - banner [ref=e2]:
    - generic [ref=e3]:
      - link "Echo Tours" [ref=e4] [cursor=pointer]:
        - /url: /zh
        - generic [ref=e5]: Echo
        - generic [ref=e6]: Tours
      - navigation [ref=e7]:
        - link "首页" [ref=e8] [cursor=pointer]:
          - /url: /zh
        - link "旅游产品" [ref=e9] [cursor=pointer]:
          - /url: /zh/tours
        - link "目的地" [ref=e10] [cursor=pointer]:
          - /url: /zh/destinations
        - link "搜索" [ref=e11] [cursor=pointer]:
          - /url: /zh/search
      - generic [ref=e12]:
        - button "中文" [ref=e14]:
          - img [ref=e15]
          - generic [ref=e18]: 中文
          - img [ref=e19]
        - button "系" [ref=e22]:
          - generic [ref=e23]: 系
          - img [ref=e24]
  - main [ref=e26]:
    - generic [ref=e28]:
      - generic [ref=e29]:
        - heading "欢迎回来" [level=3] [ref=e30]
        - paragraph [ref=e31]: 欢迎回来
      - generic [ref=e32]:
        - generic [ref=e33]:
          - generic [ref=e34]:
            - img [ref=e35]
            - textbox "邮箱" [ref=e38]: admin@echotours.com
          - generic [ref=e39]:
            - img [ref=e40]
            - textbox "密码" [ref=e43]: Admin123!
          - button "欢迎回来" [ref=e44]
        - generic [ref=e49]: or
        - generic [ref=e50]:
          - generic [ref=e52]:
            - button "使用 Google 账号登录。在新标签页中打开" [ref=e54] [cursor=pointer]:
              - generic [ref=e56]:
                - img [ref=e58]
                - generic [ref=e65]: 使用 Google 账号登录
            - iframe
          - generic [ref=e66]:
            - generic [ref=e68]: 🛠️ Dev Mode
            - button "🛠️ Dev Google 登录" [ref=e69]:
              - img [ref=e70]
              - text: 🛠️ Dev Google 登录
        - paragraph [ref=e75]:
          - text: 还没有账户？
          - button "创建账户" [ref=e76]
  - contentinfo [ref=e77]:
    - generic [ref=e78]:
      - generic [ref=e79]:
        - generic [ref=e80]:
          - generic [ref=e81]:
            - generic [ref=e82]: Echo
            - generic [ref=e83]: Tours
          - paragraph [ref=e84]: 关于我们 — Handcrafted tours and authentic travel experiences.
        - generic [ref=e85]:
          - heading "关于我们" [level=4] [ref=e86]
          - list [ref=e87]:
            - listitem [ref=e88]:
              - link "关于我们" [ref=e89] [cursor=pointer]:
                - /url: /zh
            - listitem [ref=e90]:
              - link "联系我们" [ref=e91] [cursor=pointer]:
                - /url: /zh
            - listitem [ref=e92]:
              - link "常见问题" [ref=e93] [cursor=pointer]:
                - /url: /zh
        - generic [ref=e94]:
          - heading "关注我们" [level=4] [ref=e95]
          - list [ref=e96]:
            - listitem [ref=e97]: Instagram
            - listitem [ref=e98]: Facebook
            - listitem [ref=e99]: Twitter / X
        - generic [ref=e100]:
          - heading "订阅我们的通讯" [level=4] [ref=e101]
          - paragraph [ref=e102]: Get travel inspiration and exclusive offers.
          - generic [ref=e103]:
            - textbox "您的邮箱地址" [ref=e104]
            - button "订阅" [ref=e105]
      - paragraph [ref=e107]: © 2026 Echo 旅行。保留所有权利。
  - region "Notifications alt+T"
  - button "Open Next.js Dev Tools" [ref=e113] [cursor=pointer]:
    - img [ref=e114]
  - alert [ref=e117]
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | const ADMIN_CREDENTIALS = {
  4   |   email: 'admin@echotours.com',
  5   |   password: 'Admin123!',
  6   | };
  7   | 
  8   | async function adminLogin(page) {
  9   |   await page.goto('/zh/auth');
  10  |   await page.waitForLoadState('networkidle');
  11  | 
  12  |   await page.locator('input[type="email"], input[name="email"]').first().fill(ADMIN_CREDENTIALS.email);
  13  |   await page.locator('input[type="password"]').first().fill(ADMIN_CREDENTIALS.password);
  14  |   await page.locator('button[type="submit"]').click();
> 15  |   await page.waitForURL('http://localhost:3000/zh', { timeout: 10000 });
      |              ^ TimeoutError: page.waitForURL: Timeout 10000ms exceeded.
  16  | }
  17  | 
  18  | test.describe('🔧 管理后台 — 完整功能', () => {
  19  |   test.beforeEach(async ({ page }) => {
  20  |     await adminLogin(page);
  21  |   });
  22  | 
  23  |   test('管理仪表盘页面可访问', async ({ page }) => {
  24  |     await page.goto('/zh/admin');
  25  |     await page.waitForLoadState('networkidle');
  26  |     // CSR 页面加载骨架屏后应渲染页面内容
  27  |     await expect(page.locator('body')).toBeVisible();
  28  |   });
  29  | 
  30  |   test('英文管理后台可访问', async ({ page }) => {
  31  |     await page.goto('/en/admin');
  32  |     await page.waitForLoadState('networkidle');
  33  |     await expect(page.locator('body')).toBeVisible();
  34  |   });
  35  | 
  36  |   test('管理后台侧边栏导航存在', async ({ page }) => {
  37  |     await page.goto('/zh/admin');
  38  |     await page.waitForLoadState('networkidle');
  39  | 
  40  |     // 检查是否有导航链接
  41  |     const navLinks = page.locator('a[href*="/zh/admin/"], nav a').all();
  42  |     const count = (await navLinks).length;
  43  |     // 至少有一个导航链接
  44  |     expect(count).toBeGreaterThanOrEqual(1);
  45  |   });
  46  | });
  47  | 
  48  | test.describe('📊 管理员仪表盘', () => {
  49  |   test.beforeEach(async ({ page }) => {
  50  |     await adminLogin(page);
  51  |   });
  52  | 
  53  |   test('仪表盘显示统计卡片', async ({ page }) => {
  54  |     await page.goto('/zh/admin');
  55  |     await page.waitForLoadState('networkidle');
  56  | 
  57  |     const bodyText = await page.locator('body').innerText();
  58  |     // 统计信息可能包括数字、百分比等
  59  |     const hasNumbers = /\d+/.test(bodyText);
  60  |     expect(hasNumbers).toBeTruthy();
  61  |   });
  62  | });
  63  | 
  64  | test.describe('🏛️ 管理员 — 产品管理', () => {
  65  |   test.beforeEach(async ({ page }) => {
  66  |     await adminLogin(page);
  67  |   });
  68  | 
  69  |   test('产品管理页面可访问', async ({ page }) => {
  70  |     await page.goto('/zh/admin/tours');
  71  |     await page.waitForLoadState('networkidle');
  72  |     await expect(page.locator('body')).toBeVisible();
  73  |   });
  74  | 
  75  |   test('产品管理页面显示产品列表', async ({ page }) => {
  76  |     await page.goto('/zh/admin/tours');
  77  |     await page.waitForLoadState('networkidle');
  78  | 
  79  |     const bodyText = await page.locator('body').innerText();
  80  |     const hasContent = bodyText.includes('tour') || bodyText.includes('Tour')
  81  |       || bodyText.includes('产品') || bodyText.includes('产品管理')
  82  |       || bodyText.includes('旅游');
  83  |     expect(hasContent).toBeTruthy();
  84  |   });
  85  | 
  86  |   test('英文产品管理页正常', async ({ page }) => {
  87  |     await page.goto('/en/admin/tours');
  88  |     await page.waitForLoadState('networkidle');
  89  |     await expect(page.locator('body')).toBeVisible();
  90  |   });
  91  | });
  92  | 
  93  | test.describe('📋 管理员 — 订单管理', () => {
  94  |   test.beforeEach(async ({ page }) => {
  95  |     await adminLogin(page);
  96  |   });
  97  | 
  98  |   test('订单管理页面可访问', async ({ page }) => {
  99  |     await page.goto('/zh/admin/orders');
  100 |     await page.waitForLoadState('networkidle');
  101 |     await expect(page.locator('body')).toBeVisible();
  102 |   });
  103 | 
  104 |   test('订单管理页面显示订单列表', async ({ page }) => {
  105 |     await page.goto('/zh/admin/orders');
  106 |     await page.waitForLoadState('networkidle');
  107 |     // CSR 页面，骨架屏加载后页面正常渲染
  108 |     await expect(page.locator('body')).toBeVisible();
  109 |   });
  110 | 
  111 |   test('英文订单管理页正常', async ({ page }) => {
  112 |     await page.goto('/en/admin/orders');
  113 |     await page.waitForLoadState('networkidle');
  114 |     await expect(page.locator('body')).toBeVisible();
  115 |   });
```