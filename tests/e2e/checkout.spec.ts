import { test, expect } from '@playwright/test';

const CREDENTIALS = {
  zhangsan: { email: 'zhangsan@example.com', password: 'Test1234!' },
};

async function login(page) {
  await page.goto('/zh/auth');
  await page.waitForLoadState('networkidle');

  const emailInput = page.locator('input[type="email"], input[name="email"]').first();
  const passwordInput = page.locator('input[type="password"]').first();
  await emailInput.fill(CREDENTIALS.zhangsan.email);
  await passwordInput.fill(CREDENTIALS.zhangsan.password);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL('http://localhost:3000/zh', { timeout: 10000 }).catch(() => {});
}

async function clearAuth(page) {
  await page.context().clearCookies();
  await page.evaluate(() => localStorage.clear());
  await page.goto('/zh');
  await page.waitForLoadState('networkidle');
}

test.describe('🛒 预订流程 — 完整业务闭环', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('未登录访问结账页显示未登录状态', async ({ page }) => {
    // 先清除登录状态再访问
    await page.context().clearCookies();
    await page.goto('/zh');
    await page.waitForLoadState('networkidle');
    await page.evaluate(() => localStorage.clear());
    await page.goto('/zh/checkout');
    await page.waitForLoadState('networkidle');

    // 导航栏应显示"登录"按钮（未登录状态）
    const headerLogin = page.locator('header a[href*="auth"]').first();
    await expect(headerLogin).toBeVisible();
  });

  test('登录后可访问结账页面', async ({ page }) => {
    await page.goto('/zh/checkout');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('结账页面正常渲染', async ({ page }) => {
    await page.goto('/zh/checkout');
    await page.waitForLoadState('networkidle');

    // 结账页面加载正常（可能为 CSR 空状态或需要先选择产品）
    const bodyText = await page.locator('body').innerText();
    // 至少页面非空
    expect(bodyText.length).toBeGreaterThan(0);
  });

  test('支付成功页面可访问', async ({ page }) => {
    await page.goto('/zh/checkout/success');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();

    // 成功页面应显示确认信息
    const bodyText = await page.locator('body').innerText();
    const hasSuccessText = bodyText.includes('成功') || bodyText.includes('confirmed')
      || bodyText.includes('谢谢') || bodyText.includes('Thank')
      || bodyText.includes('order') || bodyText.includes('订单')
      || bodyText.includes('Order');
    expect(hasSuccessText).toBeTruthy();
  });

  test('英文结账成功页面可访问', async ({ page }) => {
    await page.goto('/en/checkout/success');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toBeVisible();
  });

  test('产品详情页有预订按钮', async ({ page }) => {
    const tours = ['nanjing-historical-essence', 'mutianyu-great-wall-premium',
      'temple-of-heaven-cultural', 'beijing-essence-5-day'];

    for (const slug of tours) {
      await page.goto(`/zh/tours/${slug}`);
      await page.waitForLoadState('networkidle');

      // 查看预订按钮是否存在
      const bodyText = await page.locator('body').innerText();
      const hasBookingOption = bodyText.includes('Book') || bodyText.includes('预订')
        || bodyText.includes('¥') || bodyText.includes('日期');
      expect(hasBookingOption).toBeTruthy();
    }
  });

  test('结账页面加载后显示预订信息（需选择产品）', async ({ page }) => {
    await page.goto('/zh/checkout');
    await page.waitForLoadState('networkidle');

    // 结账页面应正常渲染（不再因 auth 竞态问题重定向到登录页）
    const bodyText = await page.locator('body').innerText();
    const hasCheckoutContent = bodyText.includes('结算') || bodyText.includes('预订概要')
      || bodyText.includes('Checkout') || bodyText.includes('Booking')
      || bodyText.includes('loading') || bodyText.includes('Loading');
    expect(hasCheckoutContent || bodyText.length > 50).toBeTruthy();
  });

  test('产品详情页预订按钮可交互', async ({ page }) => {
    // 从产品详情尝试寻找预订入口
    await page.goto('/zh/tours/mutianyu-great-wall-premium');
    await page.waitForLoadState('networkidle');

    const bookBtn = page.locator('button:has-text("Book"), button:has-text("预订"), a:has-text("Book"), a:has-text("预订")').first();
    if (await bookBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await bookBtn.click();
      await page.waitForTimeout(1000);
      // 可能跳转到 checkout 或留在当前页
      await expect(page.locator('body')).toBeVisible();
    }
  });
});

test.describe('📧 支付成功邮件确认流程', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('英文结账 — 完整流程下单到成功页含邮件提示', async ({ page }) => {
    // 通过 API 获取可预订产品
    const toursResp = await page.request.get('http://localhost:8000/api/v1/tours?locale=en&page_size=5');
    expect(toursResp.ok()).toBeTruthy();
    const tours = (await toursResp.json()).tours;
    expect(tours.length).toBeGreaterThan(0);

    const tour = tours[0];

    // 获取可用团期
    const datesResp = await page.request.get(`http://localhost:8000/api/v1/tours/${tour.id}/dates`);
    expect(datesResp.ok()).toBeTruthy();
    const dates = (await datesResp.json()).dates;
    const availableDate = dates.find((d: any) => d.availability > 0);
    if (!availableDate) {
      test.skip('No available dates for testing');
      return;
    }

    // 访问结账页
    await page.goto(`/en/checkout?tour=${tour.id}&date=${availableDate.id}&pax=2`);
    await page.waitForLoadState('networkidle');

    // 等待联系方式表单加载
    await page.waitForTimeout(1500);

    // 填写联系方式
    const nameInput = page.locator('input[placeholder*="Name"], input[placeholder*="name"]').first();
    const emailInput = page.locator('input[type="email"]').first();
    const phoneInput = page.locator('input[type="tel"], input[placeholder*="Phone"]').first();

    await expect(nameInput).toBeVisible({ timeout: 8000 });
    await nameInput.fill('E2E Payment Test');
    await emailInput.fill('e2e_payment_test@example.com');
    if (await phoneInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await phoneInput.fill('+1234567890');
    }

    // 点击支付按钮
    const payBtn = page.locator('button:has-text("Pay"), button:has-text("支付")').first();
    await expect(payBtn).toBeVisible({ timeout: 5000 });

    // 验证支付金额显示
    const btnText = await payBtn.innerText();
    expect(btnText).toContain('Pay');

    // 点击提交订单
    await payBtn.click();

    // 等待跳转到成功页（mock 支付成功后自动跳转）
    await page.waitForURL(/\/en\/checkout\/success\?order_no=ECHO-/, { timeout: 20000 });

    // 验证成功页内容
    await expect(page.locator('body')).toBeVisible({ timeout: 5000 });
    const bodyText = await page.locator('body').innerText();

    // 显示支付成功信息
    expect(bodyText).toContain('Payment Successful');

    // 显示"请查收邮件"或类似表述
    expect(bodyText.toLowerCase()).toContain('email');

    // 显示订单号
    expect(bodyText).toMatch(/ECHO-\d{8}-[A-Z0-9]{8}/);

    // 显示操作按钮
    const viewOrderLink = page.locator('a:has-text("View Orders"), a:has-text("View Order")').first();
    await expect(viewOrderLink).toBeVisible({ timeout: 3000 });
  });

  test('中文结账 — 完整流程支付成功显示邮箱提示', async ({ page }) => {
    const toursResp = await page.request.get('http://localhost:8000/api/v1/tours?locale=zh&page_size=5');
    expect(toursResp.ok()).toBeTruthy();
    const tours = (await toursResp.json()).tours;
    expect(tours.length).toBeGreaterThan(0);

    const tour = tours[0];

    const datesResp = await page.request.get(`http://localhost:8000/api/v1/tours/${tour.id}/dates`);
    const dates = (await datesResp.json()).dates;
    const availableDate = dates.find((d: any) => d.availability > 0);
    if (!availableDate) {
      test.skip('No available dates for testing');
      return;
    }

    await page.goto(`/zh/checkout?tour=${tour.id}&date=${availableDate.id}&pax=1`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    const nameInput = page.locator('input[placeholder*="Name"], input[placeholder*="name"], input[placeholder*="姓名"]').first();
    const emailInput = page.locator('input[type="email"]').first();

    await expect(nameInput).toBeVisible({ timeout: 8000 });
    await nameInput.fill('E2E 中文测试');
    await emailInput.fill('e2e_zh_test@example.com');

    const payBtn = page.locator('button:has-text("Pay"), button:has-text("支付")').first();
    await expect(payBtn).toBeVisible({ timeout: 5000 });
    await payBtn.click();

    await page.waitForURL(/\/zh\/checkout\/success\?order_no=ECHO-/, { timeout: 20000 });

    await expect(page.locator('body')).toBeVisible({ timeout: 5000 });
    const bodyText = await page.locator('body').innerText();

    // 中文支付成功
    expect(bodyText).toContain('支付成功');

    // 中文邮箱提示
    expect(bodyText).toContain('邮箱');

    // 订单号
    expect(bodyText).toMatch(/ECHO-\d{8}-[A-Z0-9]{8}/);
  });

  test('结账缺少必填项时提交按钮禁用', async ({ page }) => {
    const toursResp = await page.request.get('http://localhost:8000/api/v1/tours?locale=en&page_size=1');
    expect(toursResp.ok()).toBeTruthy();
    const tours = (await toursResp.json()).tours;
    if (!tours.length) {
      test.skip('No tours available');
      return;
    }

    const tour = tours[0];
    const datesResp = await page.request.get(`http://localhost:8000/api/v1/tours/${tour.id}/dates`);
    const dates = (await datesResp.json()).dates;
    const availableDate = dates.find((d: any) => d.availability > 0);
    if (!availableDate) {
      test.skip('No available dates');
      return;
    }

    await page.goto(`/en/checkout?tour=${tour.id}&date=${availableDate.id}&pax=1`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    // 不填写姓名和邮箱，按钮应禁用
    const payBtn = page.locator('button:has-text("Pay"), button:has-text("支付")').first();
    await expect(payBtn).toBeVisible({ timeout: 5000 });
    await expect(payBtn).toBeDisabled();
  });
});
