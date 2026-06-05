'use client';

import { useTranslations } from 'next-intl';
import { useSearchParams } from 'next/navigation';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useLocale } from 'next-intl';
import { useRouter } from 'next/navigation';
import { formatPrice } from '@/lib/utils';
import { Loader2, AlertCircle, User, Mail, Phone, MapPin } from 'lucide-react';
import type { Tour, TourDate, PaymentIntent, BookingRequest } from '@/lib/types';

export default function CheckoutPage() {
  const t = useTranslations('booking');
  const ct = useTranslations('common');
  const locale = useLocale();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { token, isAuthenticated } = useAuthStore();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [tour, setTour] = useState<Tour | null>(null);
  const [dateInfo, setDateInfo] = useState<TourDate | null>(null);
  const [orderId, setOrderId] = useState<string | null>(null);
  const [authReady, setAuthReady] = useState(false);

  // Form fields
  const [contactName, setContactName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [contactPhone, setContactPhone] = useState('');

  // Tour booking params
  const tourId = searchParams.get('tour');
  const dateId = searchParams.get('date');

  // Attraction booking params
  const attractionId = searchParams.get('attraction_id');
  const ticketId = searchParams.get('ticket_id');
  const attractionName = searchParams.get('name');
  const ticketPrice = parseFloat(searchParams.get('price') || '0');
  const ticketCurrency = searchParams.get('currency') || 'USD';
  const ticketType = searchParams.get('ticket_type') || 'standard';

  const pax = parseInt(searchParams.get('pax') || '1');

  const isAttractionBooking = !!(attractionId && ticketId);

  // 等待 auth store 从 localStorage 初始化完成
  useEffect(() => {
    const hasToken = typeof window !== 'undefined' && !!localStorage.getItem('auth_token');
    if (!hasToken || isAuthenticated) {
      setAuthReady(true);
      return;
    }
    const timer = setTimeout(() => setAuthReady(true), 500);
    return () => clearTimeout(timer);
  }, [isAuthenticated]);

  useEffect(() => {
    if (!authReady) return;
    if (!isAuthenticated) {
      router.push(`/${locale}/auth`);
      return;
    }
    if (tourId && dateId && !isAttractionBooking) {
      Promise.all([
        api.get<Tour>(`/tours/${tourId}`),
        api.get<{ dates: TourDate[] }>(`/tours/${tourId}/dates`),
      ]).then(([tourData, datesData]) => {
        setTour(tourData);
        const d = datesData.dates.find((d) => d.id === dateId);
        if (d) setDateInfo(d);
      }).catch(() => setError('Failed to load booking details'));
    }
  }, [tourId, dateId, isAttractionBooking, isAuthenticated, locale, router, authReady]);

  const handlePayment = async () => {
    if (!token) return;
    setLoading(true);
    setError('');

    try {
      let orderReq: BookingRequest;

      if (isAttractionBooking) {
        orderReq = {
          attraction_id: attractionId!,
          attraction_ticket_id: ticketId!,
          pax_count: pax,
          contact_name: contactName,
          contact_email: contactEmail,
          contact_phone: contactPhone || undefined,
          locale,
        };
      } else {
        if (!tourId || !dateId) return;
        orderReq = {
          tour_id: tourId,
          tour_date_id: dateId,
          pax_count: pax,
          contact_name: contactName,
          contact_email: contactEmail,
          contact_phone: contactPhone || undefined,
          locale,
        };
      }

      const order = await api.post<{ id: string; order_no: string }>('/orders', orderReq, {
        headers: { Authorization: `Bearer ${token}` },
      });

      setOrderId(order.id);

      // Step 2: Create payment intent
      const intent = await api.post<PaymentIntent>('/payments/create-intent', {
        order_id: order.id,
      });

      // Step 3: Redirect to Stripe Checkout
      if (intent.session_id && intent.session_id.startsWith('mock_')) {
        router.push(`/${locale}/checkout/success?order_no=${order.order_no}`);
      } else if (intent.session_id) {
        const stripeKey = process.env.NEXT_PUBLIC_STRIPE_PUBLIC_KEY;
        if (!stripeKey) {
          setError('Stripe payment is not configured. Please set NEXT_PUBLIC_STRIPE_PUBLIC_KEY.');
          return;
        }
        try {
          const stripeModule = await import('@stripe/stripe-js');
          const stripe = await stripeModule.loadStripe(stripeKey);
          if (!stripe) {
            setError('Failed to load Stripe. Please try again.');
            return;
          }
          const { error: redirectError } = await stripe.redirectToCheckout({
            sessionId: intent.session_id,
          });
          if (redirectError) {
            setError(redirectError.message || 'Stripe redirect failed');
          }
        } catch {
          setError('Failed to initialize payment. Please try again.');
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Payment failed');
    } finally {
      setLoading(false);
    }
  };

  const totalPrice = isAttractionBooking
    ? ticketPrice * pax
    : (dateInfo ? dateInfo.price_per_pax * pax : 0);

  const canSubmit = isAttractionBooking
    ? !!(attractionId && ticketId && contactName && contactEmail)
    : !!(dateInfo && contactName && contactEmail);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">{t('checkout')}</h1>

        {error && (
          <div className="mb-6 flex items-center gap-2 rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-600">
            <AlertCircle className="h-4 w-4 shrink-0" /> {error}
          </div>
        )}

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>{t('bookingSummary')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex justify-between">
              <span className="text-muted-foreground">
                {isAttractionBooking ? 'Attraction' : t('tourLabel')}
              </span>
              <span className="font-medium">
                {isAttractionBooking
                  ? (attractionName || ct('loading'))
                  : (tour?.name || ct('loading'))}
              </span>
            </div>
            {!isAttractionBooking && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">{t('dateLabel')}</span>
                <span className="font-medium">
                  {dateInfo ? new Date(dateInfo.start_date).toLocaleDateString() : ct('loading')}
                </span>
              </div>
            )}
            {isAttractionBooking && ticketType && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Ticket Type</span>
                <span className="font-medium capitalize">{ticketType}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-muted-foreground">{t('guestsLabel')}</span>
              <span className="font-medium">{pax}</span>
            </div>
            <div className="border-t pt-4">
              <div className="flex justify-between text-lg font-bold">
                <span>{t('totalLabel')}</span>
                <span>{formatPrice(totalPrice, ticketCurrency || 'USD', locale)}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Contact Information */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>{t('contactInfo') || 'Contact Information'}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="relative">
              <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text" value={contactName}
                onChange={(e) => setContactName(e.target.value)}
                placeholder={t('fullName') || 'Full Name'}
                className="w-full rounded-md border border-input bg-background py-2.5 pl-10 pr-4 text-sm"
              />
            </div>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="email" value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                placeholder={t('email') || 'Email'}
                className="w-full rounded-md border border-input bg-background py-2.5 pl-10 pr-4 text-sm"
              />
            </div>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="tel" value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
                placeholder={t('phone') || 'Phone'}
                className="w-full rounded-md border border-input bg-background py-2.5 pl-10 pr-4 text-sm"
              />
            </div>
          </CardContent>
        </Card>

        <Button
          className="w-full"
          size="xl"
          onClick={handlePayment}
          disabled={loading || !canSubmit}
        >
          {loading ? <Loader2 className="h-5 w-5 animate-spin mr-2" /> : null}
          {t('payNow')} — {formatPrice(totalPrice, ticketCurrency || 'USD', locale)}
        </Button>

        <p className="mt-4 text-xs text-muted-foreground text-center">
          {t('refundPolicy')}
        </p>
      </div>
    </div>
  );
}
