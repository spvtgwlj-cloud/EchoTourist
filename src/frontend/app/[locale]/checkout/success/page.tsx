'use client';

import { useTranslations } from 'next-intl';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle } from 'lucide-react';
import { useLocale } from 'next-intl';

export default function PaymentSuccessPage() {
  const t = useTranslations('booking');
  const ct = useTranslations('common');
  const locale = useLocale();
  const searchParams = useSearchParams();
  const orderNo = searchParams.get('order_no');

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4 py-12">
      <Card className="w-full max-w-md text-center">
        <CardHeader>
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
          <CardTitle>{t('paymentSuccess')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">{t('paymentSuccessDesc')}</p>
          {orderNo && (
            <div className="rounded-lg bg-muted p-4">
              <p className="text-sm text-muted-foreground">{t('bookingReference')}</p>
              <p className="text-lg font-bold">{orderNo}</p>
            </div>
          )}
          <div className="flex gap-4 justify-center pt-2">
            <Link href={`/${locale}/user/orders`}>
              <Button variant="outline">{t('viewOrder')}</Button>
            </Link>
            <Link href={`/${locale}`}>
              <Button>{ct('backToHome')}</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
