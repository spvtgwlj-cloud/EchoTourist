'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useRouter } from 'next/navigation';
import { useLocale } from 'next-intl';
import { api } from '@/lib/api';
import { AdminLayout } from '@/components/admin/AdminLayout';
import { Button } from '@/components/ui/button';
import { Plus, Eye, Edit3, CalendarRange, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { TableSkeleton } from '@/components/ui/skeletons';

interface TourItem {
  id: string; slug: string; name: string; status: string;
  start_price: number; duration_days: number; difficulty: string;
  theme: string;
  sort_order?: number;
  serial_number?: string;
  area_code?: string;
}

export default function AdminTours() {
  const locale = useLocale();
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const [tours, setTours] = useState<TourItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchTours = useCallback(() => {
    setLoading(true);
    api.get<{ tours: TourItem[]; total: number }>('/admin/tours')
      .then((res) => { setTours(res.tours || []); setTotal(res.total); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!isAuthenticated || !user?.is_admin) { router.push(`/${locale}/auth`); return; }
    fetchTours();
  }, [isAuthenticated, user, locale, router, fetchTours]);

  const handleDelete = async (tour: TourItem) => {
    if (!confirm(`Are you sure you want to delete "${tour.name || tour.slug}"?`)) return;
    setDeletingId(tour.id);
    try {
      await api.delete(`/admin/tours/${tour.id}`);
      setTours((prev) => prev.filter((t) => t.id !== tour.id));
      setTotal((prev) => prev - 1);
    } catch {
      alert('Failed to delete tour. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) return <AdminLayout>
    <div className="flex items-center justify-between mb-6">
      <div><div className="h-7 w-24 bg-gray-200 animate-pulse rounded" /><div className="h-4 w-32 bg-gray-200 animate-pulse rounded mt-2" /></div>
      <div className="h-10 w-32 bg-gray-200 animate-pulse rounded" />
    </div>
    <TableSkeleton rows={5} cols={7} />
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
              <th className="text-left p-3 font-medium">Serial No.</th>
              <th className="text-left p-3 font-medium">Name</th>
              <th className="text-left p-3 font-medium">Sort</th>
              <th className="text-left p-3 font-medium">Status</th>
              <th className="text-left p-3 font-medium">Price</th>
              <th className="text-left p-3 font-medium">Days</th>
              <th className="text-left p-3 font-medium">Difficulty</th>
              <th className="text-left p-3 font-medium">Theme</th>
              <th className="text-left p-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {tours.length === 0 ? (
              <tr><td colSpan={9} className="p-6 text-center text-muted-foreground">No tours found</td></tr>
            ) : tours.map((tour) => (
              <tr key={tour.id} className="border-b hover:bg-gray-50/50">
                <td className="p-3 font-mono text-xs text-muted-foreground">
                  {tour.area_code && tour.serial_number
                    ? `${tour.area_code}-${tour.serial_number}`
                    : '-'}
                </td>
                <td className="p-3 font-medium">{tour.name || tour.slug}</td>
                <td className="p-3 text-muted-foreground">{tour.sort_order ?? 0}</td>
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
                <td className="p-3"><span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-50 text-blue-700">{tour.theme || 'citywalk'}</span></td>
                <td className="p-3">
                  <div className="flex items-center gap-1">
                    <Link href={`/${locale}/admin/tours/${tour.id}/edit`}>
                      <Button variant="ghost" size="sm"><Edit3 className="h-3 w-3 mr-1" /> Edit</Button>
                    </Link>
                    <Link href={`/${locale}/admin/tours/${tour.id}/dates`}>
                      <Button variant="ghost" size="sm"><CalendarRange className="h-3 w-3 mr-1" /> Dates</Button>
                    </Link>
                    <Link href={`/${locale}/tours/${tour.slug}`}>
                      <Button variant="ghost" size="sm"><Eye className="h-3 w-3" /></Button>
                    </Link>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-600 hover:text-red-800 hover:bg-red-50"
                      onClick={() => handleDelete(tour)}
                      disabled={deletingId === tour.id}
                    >
                      <Trash2 className="h-3 w-3 mr-1" />
                      {deletingId === tour.id ? '...' : 'Delete'}
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AdminLayout>
  );
}
