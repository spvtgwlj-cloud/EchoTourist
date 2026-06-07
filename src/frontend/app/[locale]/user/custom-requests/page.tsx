'use client';

import { useTranslations } from 'next-intl';
import { useLocale } from 'next-intl';
import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Eye, ClipboardList, ChevronDown, ChevronUp, MapPin, Wrench } from 'lucide-react';
import Link from 'next/link';
import type { CustomTourRequest } from '@/lib/types';

const STATUS_MAP: Record<string, string> = {
  pending: 'statusPending',
  quoted: 'statusQuoted',
  confirmed: 'statusConfirmed',
  rejected: 'statusRejected',
  paid: 'statusPaid',
};

export default function CustomRequestsPage() {
  const t = useTranslations('customTour');
  const locale = useLocale();
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [requests, setRequests] = useState<CustomTourRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) { setLoading(false); return; }
    api
      .get<{ requests: CustomTourRequest[] }>('/custom-tours/requests')
      .then((res) => setRequests(res.requests || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [isAuthenticated]);

  const getStatusBadge = (status: string) => {
    const variantMap: Record<string, 'default' | 'success' | 'destructive' | 'warning' | 'secondary'> = {
      pending: 'warning',
      quoted: 'secondary',
      confirmed: 'success',
      rejected: 'destructive',
      paid: 'success',
    };
    return (
      <Badge variant={variantMap[status] || 'default'}>
        {t(STATUS_MAP[status] || status)}
      </Badge>
    );
  };

  const formatPrice = (price: number | undefined | null, currency: string) => {
    if (price == null) return '—';
    return `${currency === 'USD' ? '$' : currency}${price.toFixed(2)}`;
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(locale === 'zh' ? 'zh-CN' : locale === 'es' ? 'es-ES' : 'en-US', {
        year: 'numeric', month: 'short', day: 'numeric',
      });
    } catch { return dateStr; }
  };

  // Not logged in
  if (!isAuthenticated) {
    return (
      <div className="container mx-auto px-4 py-20 text-center">
        <ClipboardList className="mx-auto h-12 w-12 text-muted-foreground/50" />
        <p className="mt-4 text-muted-foreground">{t('noRequests')}</p>
        <Link href={`/${locale}/auth`}>
          <Button className="mt-4">{t('backToHome')}</Button>
        </Link>
      </div>
    );
  }

  // Loading
  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Skeleton className="h-8 w-56 mb-8" />
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
      <h1 className="text-3xl font-bold mb-8 flex items-center gap-2">
        <ClipboardList className="h-7 w-7" />
        {t('myRequests')}
      </h1>

      {requests.length === 0 ? (
        <div className="text-center py-20">
          <ClipboardList className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-muted-foreground">{t('noRequests')}</p>
          <Link href={`/${locale}/custom-tour`}>
            <Button className="mt-4">{t('title')}</Button>
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {requests.map((req) => (
            <Card key={req.id}>
              <CardContent className="p-6">
                {/* Header row */}
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-mono text-muted-foreground">{req.request_no}</p>
                      {getStatusBadge(req.status)}
                    </div>
                    <div className="flex flex-wrap gap-x-6 gap-y-1 mt-2 text-sm">
                      <span className="text-muted-foreground">
                        {req.segments?.length || 0} segment{(req.segments?.length || 0) > 1 ? 's' : ''}
                        {' · '}
                        {req.pax_count} pax
                      </span>
                      <span className="text-muted-foreground">
                        {formatDate(req.created_at)}
                      </span>
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-sm text-muted-foreground">{t('subtotal')}</p>
                    <p className="text-lg font-bold">
                      {formatPrice(req.subtotal, req.currency)}
                    </p>
                    {req.confirmed_price != null && (
                      <p className="text-xs text-green-600 font-medium">
                        {t('confirmedPrice')}: {formatPrice(req.confirmed_price, req.currency)}
                      </p>
                    )}
                  </div>
                </div>

                {/* Expand/collapse toggle */}
                <button
                  onClick={() => setExpandedId(expandedId === req.id ? null : req.id)}
                  className="flex items-center gap-1 text-xs text-muted-foreground hover:text-primary mt-3 transition-colors"
                >
                  {expandedId === req.id ? (
                    <><ChevronUp className="h-3 w-3" /> Hide details</>
                  ) : (
                    <><ChevronDown className="h-3 w-3" /> Show details</>
                  )}
                </button>

                {/* Expanded detail */}
                {expandedId === req.id && (
                  <div className="mt-4 pt-4 border-t space-y-4">
                    {/* Segments */}
                    {req.segments && req.segments.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
                          <MapPin className="h-3 w-3" /> Itinerary Segments
                        </p>
                        <div className="space-y-2">
                          {req.segments.map((seg) => (
                            <div key={seg.id} className="text-xs bg-gray-50 dark:bg-gray-800/50 rounded p-3">
                              <p className="font-medium text-primary">
                                {t('segmentLabel')} {seg.segment_order}: {seg.destination_name || seg.custom_destination || '-'}
                              </p>
                              <p className="text-muted-foreground mt-0.5">
                                {seg.start_date} → {seg.end_date}
                              </p>
                              {seg.attractions && seg.attractions.length > 0 && (
                                <p className="text-muted-foreground mt-1">
                                  🏛 {seg.attractions.map(a => a.attraction_name).join(', ')}
                                </p>
                              )}
                              {seg.selected_tours && seg.selected_tours.length > 0 && (
                                <p className="text-muted-foreground mt-0.5">
                                  📋 {seg.selected_tours.map(t => t.tour_name).join(', ')}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Services */}
                    {req.services && req.services.length > 0 && (
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
                          <Wrench className="h-3 w-3" /> Base Services
                        </p>
                        <div className="space-y-1 text-xs">
                          {req.services.map((svc) => (
                            <div key={svc.id} className="flex justify-between text-muted-foreground">
                              <span>{svc.service_name} × {svc.quantity}</span>
                              <span>{formatPrice(svc.subtotal, req.currency)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Guide language & special requests */}
                    {req.guide_language && (
                      <p className="text-xs text-muted-foreground">🗣 {t('guideLanguage')}: {req.guide_language}</p>
                    )}
                    {req.special_requests && (
                      <div className="text-xs">
                        <p className="text-muted-foreground font-medium">{t('specialRequests')}:</p>
                        <p className="text-muted-foreground/70 mt-0.5 whitespace-pre-wrap bg-gray-50 dark:bg-gray-800/50 p-2 rounded">
                          {req.special_requests}
                        </p>
                      </div>
                    )}

                    {/* Admin notes */}
                    {req.admin_notes && (
                      <div className="text-xs">
                        <p className="text-muted-foreground font-medium">Admin Notes:</p>
                        <p className="text-muted-foreground/70 mt-0.5 whitespace-pre-wrap bg-blue-50 dark:bg-blue-900/20 p-2 rounded">
                          {req.admin_notes}
                        </p>
                      </div>
                    )}

                    {/* Contact info */}
                    <div className="text-xs text-muted-foreground border-t pt-2">
                      <p>{t('contactName')}: {req.contact_name} · {t('contactEmail')}: {req.contact_email}</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
