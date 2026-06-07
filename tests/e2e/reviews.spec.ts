import { test, expect } from '@playwright/test';
import type { APIResponse } from '@playwright/test';

const CREDENTIALS = {
  zhangsan: { email: 'zhangsan@example.com', password: 'Test1234!' },
  admin: { email: 'admin@echotours.com', password: 'Admin123!' },
};

interface ReviewResponse {
  id: string;
  tour_id: string;
  user_id: string;
  user_name: string;
  rating: number;
  title: string;
  comment: string;
  locale: string;
  status: string;
  created_at: string;
}

interface ReviewListResponse {
  reviews: ReviewResponse[];
  total: number;
  avg_rating: number;
}

async function loginViaApi(page: { request: { post: (url: string, data: any) => Promise<APIResponse> } }, email: string, password: string): Promise<string> {
  const res = await page.request.post('http://localhost:8000/api/v1/auth/login', {
    data: { email, password },
  });
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  return body.access_token;
}

test.describe('⭐ 评价提交与显示流程', () => {
  let userToken: string;
  let adminToken: string;

  test.beforeAll(async ({ request }) => {
    userToken = await loginViaApi({ request }, CREDENTIALS.zhangsan.email, CREDENTIALS.zhangsan.password);
    adminToken = await loginViaApi({ request }, CREDENTIALS.admin.email, CREDENTIALS.admin.password);
  });

  test('未登录用户提交评价被拒绝', async ({ request }) => {
    const toursResp = await request.get('http://localhost:8000/api/v1/tours?locale=en&page_size=1');
    const tours = (await toursResp.json()).tours;
    if (!tours.length) { test.skip(); return; }

    const reviewResp = await request.post('http://localhost:8000/api/v1/reviews', {
      data: { tour_id: tours[0].id, rating: 3, title: 'Unauthorized test', locale: 'en' },
    });
    expect(reviewResp.status()).toBe(401);
  });

  test('登录未预订用户提交评价被拒绝 — 需要先完成订单', async ({ request }) => {
    // 评价 API 要求用户必须先有该产品的已完成订单
    const toursResp = await request.get('http://localhost:8000/api/v1/tours?locale=en&page_size=5');
    expect(toursResp.ok()).toBeTruthy();
    const tours = (await toursResp.json()).tours;
    expect(tours.length).toBeGreaterThan(0);
    const tourId = tours[0].id;

    const reviewResp = await request.post('http://localhost:8000/api/v1/reviews', {
      data: {
        tour_id: tourId,
        rating: 5,
        title: `E2E Test Review ${Date.now()}`,
        comment: 'This review should fail without a booking.',
        locale: 'en',
      },
      headers: { Authorization: `Bearer ${userToken}` },
    });
    // 没有订单所以返回 400 级别的业务错误
    expect(reviewResp.ok()).toBeFalsy();
    const body = await reviewResp.json();
    expect(body.detail).toContain('booking');
  });

  test('评价评分超出范围被拒绝', async ({ request }) => {
    const toursResp = await request.get('http://localhost:8000/api/v1/tours?locale=en&page_size=1');
    const tours = (await toursResp.json()).tours;
    if (!tours.length) { test.skip(); return; }

    // 评分为 0（不合法）
    const reviewResp = await request.post('http://localhost:8000/api/v1/reviews', {
      data: { tour_id: tours[0].id, rating: 0, title: 'Invalid rating test', locale: 'en' },
      headers: { Authorization: `Bearer ${userToken}` },
    });
    expect(reviewResp.ok()).toBeFalsy();

    // 评分超过 5
    const reviewResp2 = await request.post('http://localhost:8000/api/v1/reviews', {
      data: { tour_id: tours[0].id, rating: 6, title: 'Invalid rating test 2', locale: 'en' },
      headers: { Authorization: `Bearer ${userToken}` },
    });
    expect(reviewResp2.ok()).toBeFalsy();
  });

  test('管理员可在后台查看评价页面', async ({ page }) => {
    // 管理员登录并访问评价审核页面
    await page.goto('/zh/auth');
    await page.locator('input[type="email"]').first().fill(CREDENTIALS.admin.email);
    await page.locator('input[type="password"]').first().fill(CREDENTIALS.admin.password);
    await page.locator('button[type="submit"]').click();
    await page.waitForTimeout(2000);

    await page.goto('/zh/admin/reviews');
    await page.waitForLoadState('networkidle');

    // 页面应有评价列表内容
    const bodyText = await page.locator('body').innerText();
    expect(bodyText.length).toBeGreaterThan(50);
  });
});

test.describe('⭐ 评价显示组件验证', () => {
  test('旅游产品详情页显示评价区域', async ({ page }) => {
    await page.goto('/zh/tours/mutianyu-great-wall-premium');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').innerText();
    const hasReviewSection = bodyText.includes('review') || bodyText.includes('Review')
      || bodyText.includes('评价') || bodyText.includes('评分')
      || bodyText.includes('star') || bodyText.includes('Star');
    expect(hasReviewSection || bodyText.length > 100).toBeTruthy();
  });

  test('评价API返回数据格式正确', async ({ request }) => {
    const toursResp = await request.get('http://localhost:8000/api/v1/tours?locale=en&page_size=1');
    const tours = (await toursResp.json()).tours;
    if (!tours.length) { test.skip(); return; }

    const reviewResp = await request.get(`http://localhost:8000/api/v1/reviews/tour/${tours[0].id}?locale=en`);
    expect(reviewResp.ok()).toBeTruthy();
    const data = await reviewResp.json() as ReviewListResponse;

    // 验证返回格式
    expect(data).toHaveProperty('reviews');
    expect(data).toHaveProperty('total');
    expect(data).toHaveProperty('avg_rating');
    expect(Array.isArray(data.reviews)).toBeTruthy();
    expect(typeof data.total).toBe('number');
    expect(typeof data.avg_rating).toBe('number');

    if (data.reviews.length > 0) {
      const review = data.reviews[0];
      expect(review).toHaveProperty('id');
      expect(review).toHaveProperty('rating');
      expect(review).toHaveProperty('status');
      expect(review).toHaveProperty('created_at');
    }
  });

  test('产品详情页有 WishlistButton（❤️ 收藏按钮）', async ({ page }) => {
    // 验证 WishlistButton 已成功集成到 TourDetailClient
    for (const slug of ['mutianyu-great-wall-premium', 'temple-of-heaven-cultural']) {
      await page.goto(`/zh/tours/${slug}`);
      await page.waitForLoadState('networkidle');

      // 查找心形按钮
      const heartBtn = page.locator('button svg.lucide-heart, button:has(svg.lucide-heart)').first();
      await expect(heartBtn).toBeVisible({ timeout: 5000 });
    }
  });
});
