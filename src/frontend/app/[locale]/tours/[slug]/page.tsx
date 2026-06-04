import { getTranslations } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { TourDetailClient } from './TourDetailClient';
import { api } from '@/lib/api';
import type { Tour, TourDate } from '@/lib/types';

type Props = {
  params: Promise<{ locale: string; slug: string }>;
};

async function getTour(locale: string, slug: string): Promise<Tour | null> {
  try {
    return await api.get<Tour>(`/tours/${slug}?locale=${locale}`, {
      next: { revalidate: 60 },
    });
  } catch {
    return null;
  }
}

async function getTourDates(tourId: string): Promise<TourDate[]> {
  try {
    const res = await api.get<{ dates: TourDate[] }>(`/tours/${tourId}/dates`, {
      next: { revalidate: 30 },
    });
    return res.dates || [];
  } catch {
    return [];
  }
}

export default async function TourDetailPage({ params }: Props) {
  const { locale, slug } = await params;
  const t = await getTranslations({ locale, namespace: 'common' });
  const tour = await getTour(locale, slug);

  if (!tour) {
    notFound();
  }

  const dates = await getTourDates(tour.id);

  return <TourDetailClient tour={tour} dates={dates} locale={locale} />;
}
