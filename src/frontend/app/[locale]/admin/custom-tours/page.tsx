'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useRouter } from 'next/navigation';
import { useLocale } from 'next-intl';
import { api } from '@/lib/api';
import { AdminLayout } from '@/components/admin/AdminLayout';
import { Button } from '@/components/ui/button';
import { Eye, Loader2, Search } from 'lucide-react';
import Link from 'next/link';
import { TableSkeleton } from '@/components/ui/skeletons';

interface CustomTourRequestItem {
  id: string;
  request_no: string;
  destination_name: string;
  destination_id: string;
  start_date: string;
  end_date: string;
  pax_count: number;
  contact_name: string;
  contact_email: string;
  subtotal: number;
  confirmed_price: number | null;
  currency: string;
  status: string;
  created_at: string;
  guide_language: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700',
  quoted: 'bg-blue-100 text-blue-700',
  confirmed: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
  paid: 'bg-purple-100 text-purple-700',
};

export default function AdminCustomTours() {
  const locale = useLocale();
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const [requests, setRequests] = useState<CustomTourRequestItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    if (!isAuthenticated || !user?.is_admin) { router.push(`/${locale}/auth`); return; }
    loadRequests();
  }, [isAuthenticated, user, locale, router, statusFilter]);

  const loadRequests = () => {
    setLoading(true);
    const endpoint = '/admin/custom-tours' + (statusFilter ? `?status=${statusFilter}` : '');
    api.get<{ requests: CustomTourRequestItem[]; total: number }>(endpoint)
      .then((res) => { setRequests(res.requests || []); setTotal(res.total); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  if (loading) return <AdminLayout>
    <div className="flex items-center justify-between mb-6">
      <div><div className="h-7 w-40 bg-gray-200 animate-pulse rounded" /><div className="h-4 w-24 bg-gray-200 animate-pulse rounded mt-2" /></div>
      <div className="h-10 w-32 bg-gray-200 animate-pulse rounded" />
    </div>
    <TableSkeleton rows={5} cols={7} />
  </AdminLayout>;

  return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Custom Tour Requests</h1>
          <p className="text-sm text-muted-foreground">{total} requests total</p>
        </div>
      </div>

      {/* Status Filter */}
      <div className="flex gap-2 mb-4">
        {['', 'pending', 'quoted', 'confirmed', 'rejected', 'paid'].map(s => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${
              statusFilter === s
                ? 'bg-primary text-white border-primary'
                : 'bg-white text-muted-foreground border-gray-200 hover:border-gray-300'
            }`}
          >
            {s ? s.charAt(0).toUpperCase() + s.slice(1) : 'All'}
          </button>
        ))}
      </div>

      <div className="rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="text-left p-3 font-medium">Request No.</th>
              <th className="text-left p-3 font-medium">Destination</th>
              <th className="text-left p-3 font-medium">Dates</th>
              <th className="text-left p-3 font-medium">Pax</th>
              <th className="text-left p-3 font-medium">Contact</th>
              <th className="text-left p-3 font-medium">Est. Price</th>
              <th className="text-left p-3 font-medium">Status</th>
              <th className="text-left p-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {requests.length === 0 ? (
              <tr><td colSpan={8} className="p-6 text-center text-muted-foreground">No requests found</td></tr>
            ) : requests.map((r) => (
              <tr key={r.id} className="border-b hover:bg-gray-50/50">
                <td className="p-3 font-mono text-xs">{r.request_no}</td>
                <td className="p-3 font-medium">{r.destination_name}</td>
                <td className="p-3 text-xs">{r.start_date} → {r.end_date}</td>
                <td className="p-3">{r.pax_count}</td>
                <td className="p-3">
                  <div className="text-xs">
                    <div>{r.contact_name}</div>
                    <div className="text-muted-foreground">{r.contact_email}</div>
                  </div>
                </td>
                <td className="p-3">
                  {r.confirmed_price != null ? (
                    <span className="font-bold">${r.confirmed_price}</span>
                  ) : (
                    <span className="text-muted-foreground">${r.subtotal} (est.)</span>
                  )}
                </td>
                <td className="p-3">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[r.status] || 'bg-gray-100'}`}>
                    {r.status}
                  </span>
                </td>
                <td className="p-3">
                  <Link href={`/${locale}/admin/custom-tours/${r.id}`}>
                    <Button variant="ghost" size="sm">
                      <Eye className="h-3 w-3 mr-1" /> Review
                    </Button>
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
