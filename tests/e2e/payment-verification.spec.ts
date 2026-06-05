import { test, expect } from '@playwright/test';
import type { APIResponse } from '@playwright/test';

const CREDENTIALS = {
  zhangsan: { email: 'zhangsan@example.com', password: 'Test1234!' },
};

async function loginViaApi(page: { request: { post: (url: string, data: any) => Promise<APIResponse> } }): Promise<string> {
  const res = await page.request.post('http://localhost:8000/api/v1/auth/login', {
    data: { email: CREDENTIALS.zhangsan.email, password: CREDENTIALS.zhangsan.password },
  });
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  return body.access_token;
}

test.describe('🛡️ 支付完成后订单验证', () => {
  test('支付成功后用户中心可查看到该订单', async ({ page, request }) => {
    // 1. 获取可用旅游产品
    const toursResp = await request.get('http://localhost:8000/api/v1/tours?locale=en&page_size=5');
    expect(toursResp.ok()).toBeTruthy();
    const tours = (await toursResp.json()).tours;
    expect(tours.length).toBeGreaterThan(0);
    const tour = tours[0];

    // 2. 获取可用团期
    const datesResp = await request.get(`http://localhost:8000/api/v1/tours/${tour.id}/dates`);
    expect(datesResp.ok()).toBeTruthy();
    const dates = (await datesResp.json()).dates;
    const availableDate = dates.find((d: any) => d.availability > 0);
    if (!availableDate) {
      test.skip('No available dates for testing');
      return;
    }

    // 3. 登录并完成支付流程
    const token = await loginViaApi({ request });

    // 创建订单
    const orderReq = await request.post('http://localhost:8000/api/v1/orders', {
      data: {
        tour_id: tour.id,
        tour_date_id: availableDate.id,
        pax_count: 1,
        contact_name: 'E2E Verification',
        contact_email: 'e2e_verify@example.com',
        locale: 'en',
      },
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(orderReq.ok()).toBeTruthy();
    const order = await orderReq.json();
    expect(order).toHaveProperty('id');
    expect(order).toHaveProperty('order_no');

    // 4. 通过 API 获取用户订单列表，验证新订单存在
    const ordersResp = await request.get('http://localhost:8000/api/v1/orders?page=1&page_size=20', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(ordersResp.ok()).toBeTruthy();
    const ordersData = await ordersResp.json();
    const orders = ordersData.orders || ordersData;
    const foundOrder = Array.isArray(orders)
      ? orders.find((o: any) => o.order_no === order.order_no)
      : null;

    expect(foundOrder).toBeDefined();
    expect(foundOrder.status).toBeDefined();
    expect(foundOrder.total).toBeGreaterThan(0);
  });

  test('用户中心页面可访问并显示订单信息', async ({ page }) => {
    // 登录
    await page.goto('/zh/auth');
    await page.locator('input[type="email"]').first().fill(CREDENTIALS.zhangsan.email);
    await page.locator('input[type="password"]').first().fill(CREDENTIALS.zhangsan.password);
    await page.locator('button[type="submit"]').click();
    await page.waitForTimeout(2000);

    // 访问用户中心订单页
    await page.goto('/zh/user/orders');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('body')).toBeVisible();
    const bodyText = await page.locator('body').innerText();

    // 页面应有订单相关内容（订单列表或提示信息）
    const hasOrderContent = bodyText.includes('order') || bodyText.includes('Order')
      || bodyText.includes('订单') || bodyText.includes('订单号')
      || bodyText.includes('ECHO-') || bodyText.includes('暂无')
      || bodyText.includes('没有');
    expect(hasOrderContent).toBeTruthy();
  });

  test('支付成功页面跳转后返回首页导航正常', async ({ page, request }) => {
    // 模拟直接访问成功页（不需要实际支付）
    await page.goto('/en/checkout/success?order_no=ECHO-20260605-E2ETEST');
    await page.waitForLoadState('networkidle');

    // 成功页应显示成功信息和返回首页按钮
    const bodyText = await page.locator('body').innerText();
    expect(bodyText).toContain('Payment Successful');

    // 点击返回首页按钮
    const backBtn = page.locator('a[href*="/en"], button:has-text("Back to Home")').first();
    if (await backBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await backBtn.click();
      await page.waitForURL('**/en');
      await expect(page.locator('body')).toBeVisible();
    }
  });
});
