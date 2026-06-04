'use client';

import { useTranslations } from 'next-intl';
import { useLocale } from 'next-intl';
import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';
import { api } from '@/lib/api';
import { TourCard } from '@/components/tours/TourCard';
import { Button } from '@/components/ui/button';
import { Heart } from 'lucide-react';
import { TourGridSkeleton } from '@/components/ui/skeletons';
import Link from 'next/link';

interface WishlistItem {
  id: string; tour_id: string; tour_name?: string; tour_slug?: string;
  tour_image?: string; start_price: number; currency: string;
  avg_rating: number;
}

export default function WishlistPage() {
  const t = useTranslations('user');
  const locale = useLocale();
  const { token, isAuthenticated } = useAuthStore();
  const [items, setItems] = useState<WishlistItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) { setLoading(false); return; }
    api.get<{ items: WishlistItem[] }>('/wishlist')
      .then((res) => setItems(res.items || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [isAuthenticated]);

  if (loading) return (
    <div className="container mx-auto px-4 py-8">
      <div className="h-8 w-48 bg-gray-200 animate-pulse rounded mb-8" />
      <TourGridSkeleton count={3} />
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8 flex items-center gap-2">
        <Heart className="h-7 w-7" /> {t('wishlist')}
      </h1>

      {items.length === 0 ? (
        <div className="text-center py-20">
          <Heart className="mx-auto h-12 w-12 text-muted-foreground/50" />
          <p className="mt-4 text-muted-foreground">{t('noWishlist')}</p>
          <Link href={`/${locale}/tours`}>
            <Button className="mt-4">{t('browseTours')}</Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {items.map((item) => (
            <div key={item.id}>
              {/* We map wishlist items to tour-like objects for TourCard */}
              <TourCard tour={{
                id: item.tour_id,
                slug: item.tour_slug || '',
                name: item.tour_name || '',
                start_price: item.start_price,
                currency: item.currency,
                avg_rating: item.avg_rating,
                review_count: 0,
                duration_days: 0,
                duration_nights: 0,
                difficulty: 'easy',
                images: item.tour_image ? [item.tour_image] : [],
                min_pax: 1,
                highlights: [],
                includes: [],
                excludes: [],
                status: 'published',
                locale,
              }} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
