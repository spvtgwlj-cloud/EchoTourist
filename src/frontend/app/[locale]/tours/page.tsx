import { useTranslations } from 'next-intl';
import { getTranslations } from 'next-intl/server';
import { TourCard } from '@/components/tours/TourCard';
import { api } from '@/lib/api';
import type { Tour } from '@/lib/types';

type Props = {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ destination?: string; page?: string }>;
};

async function getTours(locale: string, destination?: string): Promise<{ tours: Tour[]; total: number }> {
  try {
    const params = new URLSearchParams({ locale, page_size: '12' });
    if (destination) params.set('destination', destination);
    const res = await api.get<{ tours: Tour[]; total: number }>(
      `/tours?${params}`,
      { next: { revalidate: 120 } },
    );
    return res;
  } catch {
    return { tours: [], total: 0 };
  }
}

export default async function ToursPage({ params, searchParams }: Props) {
  const { locale } = await params;
  const { destination } = await searchParams;
  const t = await getTranslations({ locale, namespace: 'search' });
  const dt = await getTranslations({ locale, namespace: 'destinations' });
  const { tours, total } = await getTours(locale, destination);

  const destinationTitle = destination
    ? `${dt(destination as any) || destination.charAt(0).toUpperCase() + destination.slice(1)} Tours`
    : t('allTours');

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">{destinationTitle}</h1>
          <p className="mt-1 text-muted-foreground">
            {t('results', { count: total })}
          </p>
        </div>
      </div>

      {tours.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-muted-foreground text-lg">{t('noResults')}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tours.map((tour) => (
            <TourCard key={tour.id} tour={tour} />
          ))}
        </div>
      )}
    </div>
  );
}
