'use client';

import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';

export function Footer() {
  const t = useTranslations('footer');
  const locale = useLocale();

  return (
    <footer className="border-t bg-gray-50">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <span className="text-xl font-bold text-primary">Echo</span>
              <span className="text-xl font-light">Tours</span>
            </div>
            <p className="text-sm text-muted-foreground">
              {t.raw('aboutUs')} — Handcrafted tours and authentic travel experiences.
            </p>
          </div>

          <div>
            <h4 className="font-semibold mb-4">{t('aboutUs')}</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link href={`/${locale}`}>{t('aboutUs')}</Link></li>
              <li><Link href={`/${locale}`}>{t('contactUs')}</Link></li>
              <li><Link href={`/${locale}`}>{t('faq')}</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4">{t('followUs')}</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>Instagram</li>
              <li>Facebook</li>
              <li>Twitter / X</li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4">{t('newsletter')}</h4>
            <p className="text-sm text-muted-foreground mb-2">
              Get travel inspiration and exclusive offers.
            </p>
            <div className="flex">
              <input
                type="email"
                placeholder={t('newsletterPlaceholder')}
                className="flex-1 rounded-l-md border border-r-0 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <button className="rounded-r-md bg-primary px-4 py-2 text-sm text-white hover:bg-primary/90">
                {t('subscribe')}
              </button>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t text-center text-sm text-muted-foreground">
          <p>{t('copyright')}</p>
        </div>
      </div>
    </footer>
  );
}
