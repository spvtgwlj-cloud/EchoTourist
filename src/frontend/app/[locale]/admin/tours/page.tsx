'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useRouter } from 'next/navigation';
import { useLocale } from 'next-intl';
import { api } from '@/lib/api';
import { AdminLayout } from '@/components/admin/AdminLayout';
import { Button } from '@/components/ui/button';
import { Plus, Eye } from 'lucide-react';
import Link from 'next/link';
import { TableSkeleton } from '@/components/ui/skeletons';

interface TourItem {
  id: string; slug: string; name: string; status: string;
  start_price: number; duration_days: number; difficulty: string;
}

export default function AdminTours() {
  const locale = useLocale();
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const [tours, setTours] = useState<TourItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated || !user?.is_admin) { router.push(`/${locale}/auth`); return; }
    api.get<{ tours: TourItem[]; total: number }>('/admin/tours')
      .then((res) => { setTours(res.tours || []); setTotal(res.total); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [isAuthenticated, user, locale, router]);

  if (loading) return <AdminLayout>
    <div className="flex items-center justify-between mb-6">
      <div><div className="h-7 w-24 bg-gray-200 animate-pulse rounded" /><div className="h-4 w-32 bg-gray-200 animate-pulse rounded mt-2" /></div>
      <div className="h-10 w-32 bg-gray-200 animate-pulse rounded" />
    </div>
    <TableSkeleton rows={5} cols={6} />
  </AdminLayout>;

  return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Tours</h1>
          <p className="text-sm text-muted-foreground">{total} tours total</p>
        </div>
        <Link href={`/${locale}/admin/tours/create`}>
          <Button><Plus className="h-4 w-4 mr-2" /> Add Tour</Button>
        </Link>
      </div>

      <div className="rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="text-left p-3 font-medium">Name</th>
              <th className="text-left p-3 font-medium">Status</th>
              <th className="text-left p-3 font-medium">Price</th>
              <th className="text-left p-3 font-medium">Days</th>
              <th className="text-left p-3 font-medium">Difficulty</th>
              <th className="text-left p-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {tours.length === 0 ? (
              <tr><td colSpan={6} className="p-6 text-center text-muted-foreground">No tours found</td></tr>
            ) : tours.map((tour) => (
              <tr key={tour.id} className="border-b hover:bg-gray-50/50">
                <td className="p-3 font-medium">{tour.name || tour.slug}</td>
                <td className="p-3">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                    tour.status === 'published' ? 'bg-green-100 text-green-700' :
                    tour.status === 'draft' ? 'bg-gray-100 text-gray-700' :
                    'bg-yellow-100 text-yellow-700'
                  }`}>{tour.status}</span>
                </td>
                <td className="p-3">${tour.start_price}</td>
                <td className="p-3">{tour.duration_days}</td>
                <td className="p-3">{tour.difficulty}</td>
                <td className="p-3">
                  <Link href={`/${locale}/tours/${tour.slug}`}>
                    <Button variant="ghost" size="sm"><Eye className="h-3 w-3 mr-1" /> View</Button>
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AdminLayout>
  );
}
