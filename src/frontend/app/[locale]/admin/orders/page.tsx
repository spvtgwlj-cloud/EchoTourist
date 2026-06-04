'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useRouter } from 'next/navigation';
import { useLocale } from 'next-intl';
import { api } from '@/lib/api';
import { AdminLayout } from '@/components/admin/AdminLayout';
import { Button } from '@/components/ui/button';
import { TableSkeleton } from '@/components/ui/skeletons';

interface OrderItem {
  id: string; order_no: string; status: string; payment_status: string;
  total: number; currency: string; contact_name: string;
  contact_email: string; pax_count: number; created_at: string;
}

export default function AdminOrders() {
  const locale = useLocale();
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated || !user?.is_admin) { router.push(`/${locale}/auth`); return; }
    api.get<{ orders: OrderItem[]; total: number }>('/admin/orders')
      .then((res) => { setOrders(res.orders || []); setTotal(res.total); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [isAuthenticated, user, locale, router]);

  const statusColor = (s: string) => {
    const map: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-700',
      confirmed: 'bg-green-100 text-green-700',
      completed: 'bg-blue-100 text-blue-700',
      cancelled: 'bg-red-100 text-red-700',
    };
    return map[s] || 'bg-gray-100 text-gray-700';
  };

  if (loading) return <AdminLayout>
    <div className="flex items-center justify-between mb-6">
      <div><div className="h-7 w-24 bg-gray-200 animate-pulse rounded" /><div className="h-4 w-32 bg-gray-200 animate-pulse rounded mt-2" /></div>
    </div>
    <TableSkeleton rows={5} cols={7} />
  </AdminLayout>;

  return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Orders</h1>
          <p className="text-sm text-muted-foreground">{total} orders total</p>
        </div>
      </div>

      <div className="rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-gray-50">
              <th className="text-left p-3 font-medium">Order No</th>
              <th className="text-left p-3 font-medium">Customer</th>
              <th className="text-left p-3 font-medium">Status</th>
              <th className="text-left p-3 font-medium">Payment</th>
              <th className="text-left p-3 font-medium">Total</th>
              <th className="text-left p-3 font-medium">PAX</th>
              <th className="text-left p-3 font-medium">Date</th>
            </tr>
          </thead>
          <tbody>
            {orders.length === 0 ? (
              <tr><td colSpan={7} className="p-6 text-center text-muted-foreground">No orders found</td></tr>
            ) : orders.map((order) => (
              <tr key={order.id} className="border-b hover:bg-gray-50/50">
                <td className="p-3 font-mono text-xs">{order.order_no}</td>
                <td className="p-3">
                  <p className="font-medium">{order.contact_name || 'N/A'}</p>
                  <p className="text-xs text-muted-foreground">{order.contact_email}</p>
                </td>
                <td className="p-3">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${statusColor(order.status)}`}>
                    {order.status}
                  </span>
                </td>
                <td className="p-3">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                    order.payment_status === 'paid' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                  }`}>{order.payment_status}</span>
                </td>
                <td className="p-3 font-medium">{order.currency} {order.total.toFixed(2)}</td>
                <td className="p-3">{order.pax_count}</td>
                <td className="p-3 text-xs text-muted-foreground">
                  {order.created_at ? new Date(order.created_at).toLocaleDateString() : ''}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AdminLayout>
  );
}
