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
import { Loader2, AlertCircle, User, Mail, Phone } from 'lucide-react';
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

  // Form fields
  const [contactName, setContactName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [contactPhone, setContactPhone] = useState('');

  const tourId = searchParams.get('tour');
  const dateId = searchParams.get('date');
  const pax = parseInt(searchParams.get('pax') || '1');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push(`/${locale}/auth`);
      return;
    }
    if (tourId && dateId) {
      Promise.all([
        api.get<Tour>(`/tours/${tourId}`),
        api.get<{ dates: TourDate[] }>(`/tours/${tourId}/dates`),
      ]).then(([tourData, datesData]) => {
        setTour(tourData);
        const d = datesData.dates.find((d) => d.id === dateId);
        if (d) setDateInfo(d);
      }).catch(() => setError('Failed to load booking details'));
    }
  }, [tourId, dateId, isAuthenticated, locale, router]);

  const handlePayment = async () => {
    if (!tourId || !dateId || !token) return;
    setLoading(true);
    setError('');

    try {
      // Step 1: Create order
      const orderReq: BookingRequest = {
        tour_id: tourId,
        tour_date_id: dateId,
        pax_count: pax,
        contact_name: contactName,
        contact_email: contactEmail,
        contact_phone: contactPhone || undefined,
        locale,
      };

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
        // Mock mode — skip to success
        router.push(`/${locale}/checkout/success?order_no=${order.order_no}`);
      } else if (intent.session_id) {
        // Check if Stripe public key is configured
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

  const totalPrice = dateInfo ? dateInfo.price_per_pax * pax : 0;

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
              <span className="text-muted-foreground">Tour</span>
              <span className="font-medium">{tour?.name || ct('loading')}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Date</span>
              <span className="font-medium">
                {dateInfo ? new Date(dateInfo.start_date).toLocaleDateString() : ct('loading')}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Guests</span>
              <span className="font-medium">{pax}</span>
            </div>
            <div className="border-t pt-4">
              <div className="flex justify-between text-lg font-bold">
                <span>Total</span>
                <span>{formatPrice(totalPrice, dateInfo?.currency || 'USD')}</span>
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
          disabled={loading || !dateInfo || !contactName || !contactEmail}
        >
          {loading ? <Loader2 className="h-5 w-5 animate-spin mr-2" /> : null}
          {t('payNow')} — {formatPrice(totalPrice, dateInfo?.currency || 'USD')}
        </Button>

        <p className="mt-4 text-xs text-muted-foreground text-center">
          {t('refundPolicy')}
        </p>
      </div>
    </div>
  );
}
