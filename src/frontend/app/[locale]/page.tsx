import { useTranslations } from 'next-intl';
import { getTranslations } from 'next-intl/server';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { TourCard } from '@/components/tours/TourCard';
import { api } from '@/lib/api';
import type { Tour } from '@/lib/types';
import { Search, Shield, MapPin, HeadphonesIcon } from 'lucide-react';

type Props = {
  params: Promise<{ locale: string }>;
};

async function getFeaturedTours(locale: string): Promise<Tour[]> {
  try {
    const res = await api.get<{ tours: Tour[]; total: number }>(
      `/tours?locale=${locale}&page_size=6&sort=rating`,
      { next: { revalidate: 300 } },
    );
    return res.tours || [];
  } catch {
    return [];
  }
}

export default async function HomePage({ params }: Props) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'home' });
  const commonT = await getTranslations({ locale, namespace: 'common' });
  const destT = await getTranslations({ locale, namespace: 'destinations' });
  const tours = await getFeaturedTours(locale);

  const features = [
    {
      icon: MapPin,
      title: t('expertGuides'),
      desc: t('expertGuidesDesc'),
    },
    {
      icon: Search,
      title: t('customized'),
      desc: t('customizedDesc'),
    },
    {
      icon: Shield,
      title: t('bestPrice'),
      desc: t('bestPriceDesc'),
    },
    {
      icon: HeadphonesIcon,
      title: t('support247'),
      desc: t('support247Desc'),
    },
  ];

  return (
    <div>
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-primary/5 via-primary/10 to-accent/5">
        <div className="container mx-auto px-4 py-20 md:py-32">
          <div className="max-w-3xl">
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
              {t('heroTitle')}
            </h1>
            <p className="mt-6 text-lg md:text-xl text-muted-foreground max-w-2xl">
              {t('heroSubtitle')}
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Link href={`/${locale}/tours`}>
                <Button size="xl">{t('cta')}</Button>
              </Link>
              <Link href={`/${locale}/tours`}>
                <Button size="xl" variant="outline">
                  {commonT('viewAll')}
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Tours */}
      {tours.length > 0 && (
        <section className="container mx-auto px-4 py-16">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold">{t('featuredTours')}</h2>
              <p className="mt-2 text-muted-foreground">{t('whyChooseUsDesc')}</p>
            </div>
            <Link href={`/${locale}/tours`}>
              <Button variant="ghost">{commonT('viewAll')} →</Button>
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {tours.map((tour) => (
              <TourCard key={tour.id} tour={tour} />
            ))}
          </div>
        </section>
      )}

      {/* Why Choose Us */}
      <section className="bg-gray-50 py-16">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold">{t('whyChooseUs')}</h2>
            <p className="mt-2 text-muted-foreground">{t('whyChooseUsDesc')}</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <div key={feature.title} className="text-center">
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
                    <Icon className="h-7 w-7 text-primary" />
                  </div>
                  <h3 className="mt-4 font-semibold">{feature.title}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">{feature.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Destinations Preview */}
      <section className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold">{t('popularDestinations')}</h2>
          <p className="mt-2 text-muted-foreground">{t('whyChooseUsDesc')}</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { key: 'beijing', slug: 'beijing' },
            { key: 'nanjing', slug: 'nanjing' },
            { key: 'xian', slug: 'xian' },
          ].map((dest) => (
            <Link
              key={dest.key}
              href={`/${locale}/destinations/${dest.slug}`}
              className="group relative aspect-[4/3] overflow-hidden rounded-xl bg-gray-100"
            >
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
              <div className="absolute bottom-0 left-0 right-0 p-6">
                <h3 className="text-xl font-bold text-white">{destT(dest.key)}</h3>
                <p className="text-sm text-white/80">{commonT('viewAll')} →</p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-primary py-16">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-primary-foreground">
            {t.raw('heroTitle')}
          </h2>
          <p className="mt-4 text-lg text-primary-foreground/80 max-w-2xl mx-auto">
            {t('heroSubtitle')}
          </p>
          <Link href={`/${locale}/tours`}>
            <Button size="xl" variant="secondary" className="mt-8">
              {t('cta')}
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
}
