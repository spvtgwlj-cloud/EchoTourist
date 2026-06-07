import { getTranslations } from 'next-intl/server';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { TourCard } from '@/components/tours/TourCard';
import AttractionsGridClient from '@/components/attractions/AttractionsGridClient';
import type { Tour } from '@/lib/types';
import { ChevronLeft } from 'lucide-react';

type Props = { params: Promise<{ locale: string; slug: string }> };

interface DestinationDetail {
  id: string; slug: string; name: string; description?: string;
  image_url?: string; tour_count: number;
}

interface AttractionMediaItem {
  id: string; url: string; media_type: string;
  alt_text?: string; sort_order: number;
}

interface AttractionTicket {
  id: string; ticket_type: string; price: number;
  currency: string; availability: number; status: string;
}

interface Attraction {
  id: string; slug: string; name: string; description?: string;
  image_url?: string; sort_order: number; rating: number;
  ticket_price: number;
  ticket_currency: string;
  tickets: AttractionTicket[];
  media: AttractionMediaItem[];
}

async function getDestination(locale: string, slug: string): Promise<DestinationDetail | null> {
  try {
    return await api.get<DestinationDetail>(`/destinations/${slug}?locale=${locale}`);
  } catch { return null; }
}

async function getAttractions(locale: string, slug: string): Promise<Attraction[]> {
  try {
    const res = await api.get<{ attractions: Attraction[] }>(
      `/destinations/${slug}/attractions?locale=${locale}`,
      { next: { revalidate: 3600 } },
    );
    return res.attractions || [];
  } catch { return []; }
}

async function getTours(locale: string, slug: string): Promise<Tour[]> {
  try {
    const res = await api.get<{ tours: Tour[]; total: number }>(
      `/destinations/${slug}/tours?locale=${locale}&page_size=12`,
      { next: { revalidate: 120 } },
    );
    return res.tours || [];
  } catch { return []; }
}

export default async function DestinationDetailPage({ params }: Props) {
  const { locale, slug } = await params;
  const t = await getTranslations({ locale, namespace: 'destinations' });
  const ct = await getTranslations({ locale, namespace: 'common' });
  const dest = await getDestination(locale, slug);
  if (!dest) notFound();

  const attractions = await getAttractions(locale, slug);
  const tours = await getTours(locale, slug);

  return (
    <div className="container mx-auto px-4 py-8">
      <Link href={`/${locale}/destinations`} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary mb-6">
        <ChevronLeft className="h-4 w-4" /> {t('back')}
      </Link>

      {/* Destination Hero */}
      <div className="mb-10">
        <h1 className="text-3xl font-bold">{dest.name}</h1>
        {dest.description && <p className="mt-2 text-muted-foreground max-w-2xl">{dest.description}</p>}
        <p className="mt-1 text-sm text-muted-foreground">{dest.tour_count} {t('tours')}</p>
      </div>

      {/* Attractions Grid — now uses client component with More Information modal */}
      {attractions.length > 0 && (
        <section className="mb-12">
          <h2 className="text-2xl font-bold mb-6">{t('attractions')}</h2>
          <AttractionsGridClient
            attractions={attractions}
            locale={locale}
            moreInfoLabel={ct('moreInformation')}
          />
        </section>
      )}

      {/* Tours Section */}
      {tours.length === 0 ? (
        <div className="text-center py-20 text-muted-foreground">{t('noTours')}</div>
      ) : (
        <section>
          <h2 className="text-2xl font-bold mb-6">{ct('viewAll')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {tours.map((tour) => <TourCard key={tour.id} tour={tour} />)}
          </div>
        </section>
      )}
    </div>
  );
}
