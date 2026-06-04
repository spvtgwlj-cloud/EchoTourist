# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: user-center.spec.ts >> 🔒 用户中心权限控制 >> 未登录访问订单页导航栏显示登录按钮
- Location: tests/e2e/user-center.spec.ts:141:7

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/zh
Call log:
  - navigating to "http://localhost:3000/zh", waiting until "load"

```

# Test source

```ts
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
  112 | 
  113 |   test('心愿单页面有内容或空状态提示', async ({ page }) => {
  114 |     await page.goto('/zh/user/wishlist');
  115 |     await page.waitForLoadState('networkidle');
  116 | 
  117 |     const bodyText = await page.locator('body').innerText();
  118 |     const hasContent = bodyText.includes('心愿') || bodyText.includes('wishlist')
  119 |       || bodyText.includes('Wishlist') || bodyText.includes('收藏')
  120 |       || bodyText.includes('暂无') || bodyText.includes('empty')
  121 |       || bodyText.includes('没有任何');
  122 |     expect(hasContent).toBeTruthy();
  123 |   });
  124 | 
  125 |   test('英文心愿单页面正常', async ({ page }) => {
  126 |     await page.goto('/en/user/wishlist');
  127 |     await page.waitForLoadState('networkidle');
  128 |     await expect(page.locator('body')).toBeVisible();
  129 |   });
  130 | 
  131 |   test('不同用户心愿单页面均可访问', async ({ page }) => {
  132 |     await login(page, CREDENTIALS.lisi.email, CREDENTIALS.lisi.password, true);
  133 | 
  134 |     await page.goto('/zh/user/wishlist');
  135 |     await page.waitForLoadState('networkidle');
  136 |     await expect(page.locator('body')).toBeVisible();
  137 |   });
  138 | });
  139 | 
  140 | test.describe('🔒 用户中心权限控制', () => {
  141 |   test('未登录访问订单页导航栏显示登录按钮', async ({ page }) => {
  142 |     await page.context().clearCookies();
> 143 |     await page.goto('/zh');
      |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/zh
  144 |     await page.waitForLoadState('networkidle');
  145 |     await page.evaluate(() => localStorage.clear()).catch(() => {});
  146 | 
  147 |     await page.goto('/zh/user/orders');
  148 |     await page.waitForLoadState('networkidle');
  149 |     // 导航栏应显示"登录"按钮（未登录状态）
  150 |     const headerLogin = page.locator('header a[href*="auth"]').first();
  151 |     await expect(headerLogin).toBeVisible();
  152 |   });
  153 | 
  154 |   test('未登录访问个人资料页导航栏显示登录按钮', async ({ page }) => {
  155 |     await page.context().clearCookies();
  156 |     await page.goto('/zh');
  157 |     await page.waitForLoadState('networkidle');
  158 |     await page.evaluate(() => localStorage.clear()).catch(() => {});
  159 | 
  160 |     await page.goto('/zh/user/profile');
  161 |     await page.waitForLoadState('networkidle');
  162 |     const headerLogin = page.locator('header a[href*="auth"]').first();
  163 |     await expect(headerLogin).toBeVisible();
  164 |   });
  165 | });
  166 | 
```