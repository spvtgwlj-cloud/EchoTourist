/**
 * E2E 测试后数据清理
 *
 * 作为测试序列的最后一项（字母排序 zz-），在所有 E2E 测试通过后执行，
 * 清除测试过程中产生的中间数据：
 * - test-*, dup-*, upd-*, del-*, detail-* 前缀的 destinations 和 tours
 * - Elasticsearch 索引中的 test- 文档
 * - Redis 缓存
 *
 * 确保数据库 + ES + Redis 保持干净状态供下一轮测试。
 */
import { test, expect } from '@playwright/test';
import { execSync } from 'child_process';
import * as path from 'path';

// 项目根目录（该文件位于 tests/e2e/）
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');
const EXEC_OPTS: { cwd: string; encoding: BufferEncoding; timeout: number } = {
  cwd: PROJECT_ROOT,
  encoding: 'utf-8',
  timeout: 30_000,
};

test.describe('Post-test data cleanup', () => {
  test('cleanup test data from database, ES cache, and Redis', () => {
    // ── 1. 执行清理脚本（数据库 + ES） ──────────────────────────
    const output = execSync(
      'docker compose exec backend python /app/scripts/cleanup_test_data.py',
      EXEC_OPTS
    );
    console.log('🧹 Cleanup output:\n', output);

    // ── 2. 清空 Redis 缓存 ─────────────────────────────────────
    const redisClear = execSync(
      `docker compose exec redis redis-cli -n 0 FLUSHDB`,
      EXEC_OPTS
    );
    console.log('🗑️  Redis cache flushed:', redisClear.trim());

    // ── 3. 验证 PostgreSQL 仅保留 3 个正式目的地 ──────────────
    const destCheck = execSync(
      `docker compose exec postgres psql -U postgres -d echo_tours -t -A -c "SELECT slug FROM destinations ORDER BY slug;"`,
      EXEC_OPTS
    );
    const destinations = destCheck.trim().split('\n').filter(Boolean);
    console.log('📍 Remaining destinations:', destinations);

    expect(destinations).toEqual(['beijing', 'nanjing', 'xian']);
    expect(destinations.length).toBe(3);

    // ── 4. 验证 PG 无 test-/dup-/detail- 前缀的残留 ──────────
    const pgResidual = execSync(
      `docker compose exec postgres psql -U postgres -d echo_tours -t -A -c "SELECT COUNT(*) FROM destinations WHERE slug ~ '^(test|dup|detail|upd|del)-';"`,
      EXEC_OPTS
    );
    expect(parseInt(pgResidual.trim(), 10)).toBe(0);

    // ── 5. 验证 PG 无 test- 前缀的 tour 残留 ────────────────
    const tourResidual = execSync(
      `docker compose exec postgres psql -U postgres -d echo_tours -t -A -c "SELECT COUNT(*) FROM tours WHERE slug ILIKE 'test-%';"`,
      EXEC_OPTS
    );
    expect(parseInt(tourResidual.trim(), 10)).toBe(0);

    // ── 6. 验证 ES 索引中无 test- 文档 ────────────────────────
    const esCheck = execSync(
      `docker compose exec backend python -c "
import requests
r = requests.post('http://elasticsearch:9200/tours/_search',
    json={'query': {'prefix': {'slug': 'test-'}}, 'size': 0}, timeout=5)
print(r.json()['hits']['total']['value'])
"`,
      EXEC_OPTS
    );
    const esTestCount = parseInt(esCheck.trim(), 10);
    expect(esTestCount).toBe(0);
    console.log('🔍 ES test documents:', esTestCount);

    // ── 7. 验证 ES 仅保留正式产品（30×3=90 文档） ─────────────
    const esTotal = execSync(
      `docker compose exec backend python -c "
import requests
r = requests.get('http://elasticsearch:9200/tours/_count',
    json={'query': {'match_all': {}}}, timeout=5)
print(r.json()['count'])
"`,
      EXEC_OPTS
    );
    const esTotalCount = parseInt(esTotal.trim(), 10);
    console.log('📊 ES total documents:', esTotalCount);
    expect(esTotalCount).toBeGreaterThanOrEqual(90);

    console.log('✅ Full cleanup verified: DB clean | ES clean | Redis flushed');
  });
});
