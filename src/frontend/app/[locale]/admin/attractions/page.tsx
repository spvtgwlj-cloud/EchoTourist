'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useRouter } from 'next/navigation';
import { useLocale } from 'next-intl';
import { api } from '@/lib/api';
import { AdminLayout } from '@/components/admin/AdminLayout';
import { Edit3, Eye } from 'lucide-react';
import Link from 'next/link';
import { TableSkeleton } from '@/components/ui/skeletons';

interface AttractionItem {
  id: string; slug: string; image_url?: string;
  sort_order: number; rating: number; status: string;
  destination_id: string; destination_name: string;
  media_count: number;
}

export default function AdminAttractions() {
  const locale = useLocale();
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const [attractions, setAttractions] = useState<AttractionItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated || !user?.is_admin) { router.push(`/${locale}/auth`); return; }
    api.get<{ attractions: AttractionItem[]; total: number }>('/admin/attractions')
      .then((res) => { setAttractions(res.attractions || []); setTotal(res.total); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [isAuthenticated, user, locale, router]);

  if (loading) return <AdminLayout>
    <div className="flex items-center justify-between mb-6">
      <div><div className="h-7 w-24 bg-gray-200 animate-pulse rounded" /><div className="h-4 w-32 bg-gray-200 animate-pulse rounded mt-2" /></div>
    </div>
    <TableSkeleton rows={5} cols={6} />
  </AdminLayout>;

  // Group by destination
  const grouped: Record<string, AttractionItem[]> = {};
  for (const a of attractions) {
    const key = a.destination_name || 'Other';
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(a);
  }

  return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Attractions</h1>
          <p className="text-sm text-muted-foreground">{total} attractions total</p>
        </div>
      </div>

      {Object.entries(grouped).map(([destName, items]) => (
        <div key={destName} className="mb-8">
          <h2 className="text-lg font-semibold mb-3 text-gray-700">{destName}</h2>
          <div className="rounded-lg border bg-white overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50">
                  <th className="text-left p-3 font-medium">Slug</th>
                  <th className="text-left p-3 font-medium">Rating</th>
                  <th className="text-left p-3 font-medium">Sort</th>
                  <th className="text-left p-3 font-medium">Media</th>
                  <th className="text-left p-3 font-medium">Status</th>
                  <th className="text-left p-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((a) => (
                  <tr key={a.id} className="border-b hover:bg-gray-50/50">
                    <td className="p-3 font-medium">{a.slug}</td>
                    <td className="p-3">
                      {a.rating > 0 ? '⭐'.repeat(a.rating) : '-'}
                    </td>
                    <td className="p-3 text-muted-foreground">{a.sort_order}</td>
                    <td className="p-3">
                      <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                        {a.media_count} items
                      </span>
                    </td>
                    <td className="p-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        a.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                      }`}>{a.status}</span>
                    </td>
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/${locale}/admin/attractions/${a.id}/edit`}
                          className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
                        >
                          <Edit3 className="h-3.5 w-3.5" /> Edit
                        </Link>
                        <Link
                          href={`/${locale}/destinations/${destName.toLowerCase()}/#${a.slug}`}
                          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-gray-700"
                          target="_blank"
                        >
                          <Eye className="h-3.5 w-3.5" /> View
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </AdminLayout>
  );
}
