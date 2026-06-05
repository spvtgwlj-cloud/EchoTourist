import { useTranslations } from 'next-intl';
import { getTranslations } from 'next-intl/server';
import Link from 'next/link';
import { api } from '@/lib/api';
import { MapPin, Star, ChevronRight } from 'lucide-react';
import { WishlistButton } from '@/components/user/WishlistButton';

type Props = { params: Promise<{ locale: string }> };

interface Destination {
  id: string;
  slug: string;
  name: string;
  description?: string;
  image_url?: string;
  tour_count: number;
}

interface Attraction {
  id: string;
  name: string;
  image_url?: string;
  rating: number;
  slug: string;
  ticket_price: number;
  ticket_currency: string;
}

async function getDestinations(locale: string): Promise<Destination[]> {
  try {
    const res = await api.get<{ destinations: Destination[] }>(
      `/destinations?locale=${locale}`,
      { next: { revalidate: 3600 } },
    );
    return res.destinations || [];
  } catch { return []; }
}

async function getTopAttractions(locale: string, slug: string, limit = 5): Promise<Attraction[]> {
  try {
    const res = await api.get<{ attractions: Attraction[] }>(
      `/destinations/${slug}/attractions?locale=${locale}`,
      { next: { revalidate: 3600 } },
    );
    return (res.attractions || []).slice(0, limit);
  } catch { return []; }
}

export default async function DestinationsPage({ params }: Props) {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: 'destinations' });
  const ct = await getTranslations({ locale, namespace: 'common' });
  const destinations = await getDestinations(locale);

  // Fetch top attractions for each destination in parallel
  const destinationsWithAttractions = await Promise.all(
    destinations.map(async (dest) => ({
      ...dest,
      attractions: await getTopAttractions(locale, dest.slug),
    })),
  );

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Page Header */}
      <div className="mb-10">
        <h1 className="text-3xl font-bold">{t('title')}</h1>
        <p className="mt-2 text-muted-foreground">{t('subtitle')}</p>
      </div>

      {destinationsWithAttractions.length === 0 ? (
        <div className="text-center py-20">
          <MapPin className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-muted-foreground">{t('empty')}</p>
        </div>
      ) : (
        <div className="space-y-16">
          {destinationsWithAttractions.map((dest) => (
            <section key={dest.id}>
              {/* Destination Header */}
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <Link href={`/${locale}/destinations/${dest.slug}`} className="inline-block group">
                    <h2 className="text-2xl font-bold group-hover:text-primary transition-colors">
                      {dest.name}
                    </h2>
                  </Link>
                  {dest.description && (
                    <p className="mt-1 text-sm text-muted-foreground max-w-2xl">{dest.description}</p>
                  )}
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {dest.tour_count} {t('tours')} &middot; {dest.attractions.length} {t('attractions')}
                  </p>
                </div>
                <Link
                  href={`/${locale}/destinations/${dest.slug}`}
                  className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline shrink-0"
                >
                  {ct('viewAll')} <ChevronRight className="h-4 w-4" />
                </Link>
              </div>

              {/* Attractions Grid */}
              {dest.attractions.length > 0 ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                  {dest.attractions.map((attr) => (
                    <Link
                      key={attr.id}
                      href={`/${locale}/destinations/${dest.slug}`}
                      className="group relative aspect-[4/3] overflow-hidden rounded-lg bg-gray-100 border border-gray-200 hover:shadow-md transition-shadow block"
                    >
                      {/* Image Area */}
                      {attr.image_url ? (
                        <img
                          src={attr.image_url}
                          alt={attr.name}
                          className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                          loading="lazy"
                        />
                      ) : (
                        <div className="flex h-full items-center justify-center text-muted-foreground/40">
                          <MapPin className="h-8 w-8" />
                        </div>
                      )}
                      {/* Gradient Overlay */}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                      {/* Wishlist Button */}
                      <div className="absolute top-1.5 right-1.5 z-10">
                        <WishlistButton
                          itemId={attr.id}
                          itemType="attraction"
                          className="text-white/80 hover:text-red-400"
                        />
                      </div>
                      {/* Content */}
                      <div className="absolute bottom-0 left-0 right-0 p-2.5">
                        <h3 className="text-xs font-semibold text-white leading-tight truncate">
                          {attr.name}
                        </h3>
                        <div className="mt-0.5 flex items-center gap-1.5">
                          {attr.rating > 0 && (
                            <div className="flex items-center gap-0.5">
                              <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                              <span className="text-[10px] text-white/90">{attr.rating}</span>
                            </div>
                          )}
                          {attr.ticket_price > 0 && (
                            <span className="text-[10px] font-medium text-yellow-300 ml-auto">
                              ${attr.ticket_price}
                            </span>
                          )}
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground py-8 text-center bg-gray-50 rounded-lg">
                  {t('noAttractions')}
                </p>
              )}
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
