'use client';

import { useTranslations } from 'next-intl';
import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatPrice, formatDate } from '@/lib/utils';
import { api } from '@/lib/api';
import { useLocale } from 'next-intl';
import type { Order } from '@/lib/types';
import { Skeleton } from '@/components/ui/skeleton';

const statusMap: Record<string, string> = {
  pending: 'pending',
  confirmed: 'confirmed',
  in_progress: 'inProgress',
  completed: 'completed',
  cancelled: 'cancelled',
  refunded: 'refunded',
};

export default function OrdersPage() {
  const t = useTranslations('user');
  const locale = useLocale();
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<{ orders: Order[] }>('/orders')
      .then((res) => setOrders(res.orders || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Skeleton className="h-8 w-48 mb-8" />
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="border rounded-lg p-6 space-y-3">
              <Skeleton className="h-5 w-1/3" />
              <Skeleton className="h-4 w-1/2" />
              <div className="flex gap-4">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-4 w-16" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">{t('myOrders')}</h1>

      {orders.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-muted-foreground text-lg">{t('noOrders')}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((order) => (
            <Card key={order.id}>
              <CardContent className="p-6">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">{order.order_no}</p>
                    <p className="font-semibold mt-1">{order.tour_name || 'Tour'}</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      {formatDate(order.tour_date, locale)} · {order.pax_count} pax
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold">{formatPrice(order.total, order.currency)}</p>
                    <Badge
                      variant={
                        order.status === 'confirmed' || order.status === 'completed'
                          ? 'success'
                          : order.status === 'cancelled'
                            ? 'destructive'
                            : 'warning'
                      }
                      className="mt-1"
                    >
                      {t(`orderStatus.${statusMap[order.status] || order.status}`)}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
