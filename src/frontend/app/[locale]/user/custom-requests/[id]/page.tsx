'use client';

import { useTranslations } from 'next-intl';
import { useLocale } from 'next-intl';
import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useRouter, useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, MapPin, Wrench, Loader2, ClipboardList } from 'lucide-react';
import Link from 'next/link';
import type { CustomTourRequest } from '@/lib/types';

const STATUS_MAP: Record<string, string> = {
  pending: 'statusPending',
  quoted: 'statusQuoted',
  confirmed: 'statusConfirmed',
  rejected: 'statusRejected',
  paid: 'statusPaid',
};

export default function CustomRequestDetailPage() {
  const t = useTranslations('customTour');
  const locale = useLocale();
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const { isAuthenticated } = useAuthStore();
  const [data, setData] = useState<CustomTourRequest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push(`/${locale}/auth`);
      return;
    }
    if (!params.id) return;

    api
      .get<CustomTourRequest>(`/custom-tours/requests/${params.id}`)
      .then((res) => setData(res))
      .catch(() => setError('Failed to load request details'))
      .finally(() => setLoading(false));
  }, [isAuthenticated, params.id, router, locale]);

  const formatPrice = (price: number | undefined | null, currency: string) => {
    if (price == null) return '—';
    return `${currency === 'USD' ? '$' : currency}${price.toFixed(2)}`;
  };

  // Loading
  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Skeleton className="h-6 w-48 mb-6" />
        <Skeleton className="h-10 w-72 mb-4" />
        <Skeleton className="h-6 w-48 mb-8" />
        <div className="space-y-4">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-24 w-full" />)}
        </div>
      </div>
    );
  }

  // Error
  if (error || !data) {
    return (
      <div className="container mx-auto px-4 py-20 text-center">
        <ClipboardList className="mx-auto h-12 w-12 text-muted-foreground/50" />
        <p className="mt-4 text-muted-foreground">{error || 'Request not found'}</p>
        <Link href={`/${locale}/user/custom-requests`}>
          <Button className="mt-4" variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" /> {t('myRequests')}
          </Button>
        </Link>
      </div>
    );
  }

  const statusBadgeVariant: Record<string, 'default' | 'success' | 'destructive' | 'warning' | 'secondary'> = {
    pending: 'warning',
    quoted: 'secondary',
    confirmed: 'success',
    rejected: 'destructive',
    paid: 'success',
  };

  const totalDays = data.segments?.reduce((sum, seg) => {
    try {
      const days = Math.max(1, (new Date(seg.end_date).getTime() - new Date(seg.start_date).getTime()) / (1000 * 60 * 60 * 24));
      return sum + days;
    } catch { return sum; }
  }, 0) || 0;

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Back link */}
      <Link
        href={`/${locale}/user/custom-requests`}
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary mb-6 transition-colors"
      >
        <ArrowLeft className="h-3 w-3" /> {t('myRequests')}
      </Link>

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="text-2xl font-bold font-mono">{data.request_no}</h1>
          <Badge variant={statusBadgeVariant[data.status] || 'default'}>
            {t(STATUS_MAP[data.status] || data.status)}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground mt-1">
          {data.segments?.length || 0} segment{(data.segments?.length || 0) > 1 ? 's' : ''} · {data.pax_count} pax · {totalDays} days
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Contact & Travel Info */}
        <div className="bg-white dark:bg-gray-900 rounded-lg border p-6">
          <h2 className="font-bold mb-4">{t('contactInfo')}</h2>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">{t('contactName')}</dt>
              <dd className="font-medium">{data.contact_name}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">{t('contactEmail')}</dt>
              <dd>{data.contact_email}</dd>
            </div>
            {data.contact_phone && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">{t('contactPhone')}</dt>
                <dd>{data.contact_phone}</dd>
              </div>
            )}
            <div className="flex justify-between">
              <dt className="text-muted-foreground">{t('paxCount')}</dt>
              <dd>{data.pax_count}</dd>
            </div>
            {data.guide_language && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">{t('guideLanguage')}</dt>
                <dd className="font-medium">{data.guide_language}</dd>
              </div>
            )}
            {data.special_requests && (
              <div className="pt-2 border-t col-span-2">
                <dt className="text-muted-foreground mb-1">{t('specialRequests')}</dt>
                <dd className="text-sm whitespace-pre-wrap bg-gray-50 dark:bg-gray-800/50 p-3 rounded">{data.special_requests}</dd>
              </div>
            )}
          </dl>
        </div>

        {/* Price Info */}
        <div className="bg-white dark:bg-gray-900 rounded-lg border p-6">
          <h2 className="font-bold mb-4">{t('subtotal')}</h2>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between items-end">
              <dt className="text-muted-foreground">{t('subtotal')}</dt>
              <dd className="text-lg font-bold">{formatPrice(data.subtotal, data.currency)}</dd>
            </div>
            <div className="flex justify-between items-end">
              <dt className="text-muted-foreground">{t('confirmedPrice')}</dt>
              <dd className={`text-lg font-bold ${data.confirmed_price != null ? 'text-green-600' : ''}`}>
                {formatPrice(data.confirmed_price, data.currency)}
              </dd>
            </div>
            <p className="text-xs text-muted-foreground pt-2 border-t">{t('priceNote')}</p>
            {data.admin_notes && (
              <div className="pt-2 border-t">
                <dt className="text-muted-foreground mb-1 text-xs font-medium">Admin Notes</dt>
                <dd className="text-sm whitespace-pre-wrap bg-blue-50 dark:bg-blue-900/20 p-3 rounded">{data.admin_notes}</dd>
              </div>
            )}
          </dl>
        </div>

        {/* Itinerary Segments */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-900 rounded-lg border p-6">
          <h2 className="font-bold mb-4 flex items-center gap-2">
            <MapPin className="h-5 w-5 text-primary" />
            {t('itinerarySegments')} ({data.segments?.length || 0})
          </h2>
          <div className="space-y-4">
            {data.segments?.map((seg) => (
              <div key={seg.id} className="border rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                      {seg.segment_order}
                    </span>
                    <span className="font-medium text-sm">
                      {seg.destination_name || seg.custom_destination || '—'}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {seg.start_date} → {seg.end_date}
                  </span>
                </div>

                {/* Attractions */}
                {seg.attractions && seg.attractions.length > 0 && (
                  <div className="ml-8 mb-2">
                    <p className="text-xs text-muted-foreground mb-1">{t('chooseAttractions')}:</p>
                    <div className="flex flex-wrap gap-1">
                      {seg.attractions.map((a) => (
                        <span key={a.id} className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-50 text-blue-700 dark:bg-blue-900/30">
                          🏛 {a.attraction_name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Tours */}
                {seg.selected_tours && seg.selected_tours.length > 0 && (
                  <div className="ml-8">
                    <p className="text-xs text-muted-foreground mb-1">{t('baseTour')}:</p>
                    <div className="flex flex-wrap gap-1">
                      {seg.selected_tours.map((t) => (
                        <span key={t.id} className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-green-50 text-green-700 dark:bg-green-900/30">
                          📋 {t.tour_name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {(!seg.attractions || seg.attractions.length === 0) && (!seg.selected_tours || seg.selected_tours.length === 0) && (
                  <p className="ml-8 text-xs text-muted-foreground">{t('chooseAttractions')}</p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Services */}
        {data.services && data.services.length > 0 && (
          <div className="lg:col-span-2 bg-white dark:bg-gray-900 rounded-lg border p-6">
            <h2 className="font-bold mb-4 flex items-center gap-2">
              <Wrench className="h-5 w-5 text-primary" />
              {t('selectServices')} ({data.services.length})
            </h2>
            <div className="space-y-2">
              {data.services.map((svc) => (
                <div key={svc.id} className="flex items-center justify-between py-2 border-b last:border-0 text-sm">
                  <div>
                    <span className="font-medium">{svc.service_name}</span>
                    <span className="text-muted-foreground ml-2">× {svc.quantity}</span>
                  </div>
                  <span className="font-medium">{formatPrice(svc.subtotal, data.currency)}</span>
                </div>
              ))}
              <div className="flex justify-between pt-2 font-bold text-sm">
                <span>{t('subtotal')}</span>
                <span>{formatPrice(data.subtotal, data.currency)}</span>
              </div>
            </div>
          </div>
        )}

        {/* Metadata */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-900 rounded-lg border p-6">
          <h2 className="font-bold mb-4">{t('requestNo')}</h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">{t('requestNo')}</dt>
              <dd className="font-mono">{data.request_no}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">{t('status')}</dt>
              <dd>{t(STATUS_MAP[data.status] || data.status)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Created</dt>
              <dd>{data.created_at}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Updated</dt>
              <dd>{data.updated_at}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}
