'use client';

import { useTranslations } from 'next-intl';
import { useLocale } from 'next-intl';
import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { AdminLayout } from '@/components/admin/AdminLayout';
import { StatsCard } from '@/components/admin/StatsCard';
import { Loader2, Map, ShoppingCart, Users, Star, DollarSign } from 'lucide-react';

interface AdminStats {
  total_users: number;
  total_tours: number;
  published_tours: number;
  total_orders: number;
  total_revenue: number;
  pending_reviews: number;
}

export default function AdminDashboard() {
  const locale = useLocale();
  const router = useRouter();
  const { user, isAuthenticated, token } = useAuthStore();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated || !user?.is_admin) {
      router.push(`/${locale}/auth`);
      return;
    }
    api.get<AdminStats>('/admin/stats', { cache: 'no-store' })
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [isAuthenticated, user, locale, router]);

  if (loading) return <AdminLayout><div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin" /></div></AdminLayout>;

  return (
    <AdminLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Welcome back, {user?.name}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatsCard
          title="Total Tours"
          value={stats?.total_tours ?? 0}
          icon={<Map className="h-5 w-5" />}
          description={`${stats?.published_tours ?? 0} published`}
        />
        <StatsCard
          title="Total Orders"
          value={stats?.total_orders ?? 0}
          icon={<ShoppingCart className="h-5 w-5" />}
        />
        <StatsCard
          title="Total Users"
          value={stats?.total_users ?? 0}
          icon={<Users className="h-5 w-5" />}
        />
        <StatsCard
          title="Revenue"
          value={`$${stats?.total_revenue?.toFixed(2) ?? '0.00'}`}
          icon={<DollarSign className="h-5 w-5" />}
        />
        <StatsCard
          title="Pending Reviews"
          value={stats?.pending_reviews ?? 0}
          icon={<Star className="h-5 w-5" />}
        />
      </div>
    </AdminLayout>
  );
}
