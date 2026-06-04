'use client';

import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { useLocale } from 'next-intl';

export default function NotFound() {
  const t = useTranslations('common');
  const locale = useLocale();

  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center px-4 text-center">
      <h1 className="text-6xl font-bold text-primary">404</h1>
      <h2 className="mt-4 text-2xl font-semibold">{t('pageNotFound')}</h2>
      <p className="mt-2 text-muted-foreground">{t('pageNotFoundDesc')}</p>
      <Link href={`/${locale}`} className="mt-8">
        <Button>{t('backToHome')}</Button>
      </Link>
    </div>
  );
}
