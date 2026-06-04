'use client';

import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Star, Clock, Users } from 'lucide-react';
import { formatPrice } from '@/lib/utils';
import { ImageWithFallback } from '@/components/ui/ImageWithFallback';
import type { Tour } from '@/lib/types';

interface TourCardProps {
  tour: Tour;
}

export function TourCard({ tour }: TourCardProps) {
  const t = useTranslations('tour');
  const locale = useLocale();

  return (
    <Link href={`/${locale}/tours/${tour.slug}`}>
      <Card className="group overflow-hidden transition-all hover:shadow-lg">
        <div className="relative aspect-[16/9] overflow-hidden bg-gray-100">
          {tour.images?.[0] ? (
            <ImageWithFallback
              src={tour.images[0]}
              alt={tour.name}
              className="h-full w-full object-cover transition-transform group-hover:scale-105"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              <Clock className="h-12 w-12" />
            </div>
          )}
          {tour.avg_rating > 0 && (
            <div className="absolute top-3 left-3 flex items-center gap-1 rounded-full bg-white/90 px-2.5 py-1 text-sm font-medium">
              <Star className="h-3.5 w-3.5 fill-yellow-400 text-yellow-400" />
              {tour.avg_rating.toFixed(1)}
            </div>
          )}
        </div>
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold truncate">{tour.name}</h3>
              {tour.subtitle && (
                <p className="mt-1 text-sm text-muted-foreground line-clamp-1">
                  {tour.subtitle}
                </p>
              )}
            </div>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              {t('duration', { days: tour.duration_days, nights: tour.duration_nights })}
            </span>
            {tour.max_pax && (
              <span className="flex items-center gap-1">
                <Users className="h-3.5 w-3.5" />
                {tour.max_pax} pax
              </span>
            )}
          </div>

          <div className="mt-4 flex items-center justify-between">
            <div>
              <span className="text-xs text-muted-foreground">{t('from')}</span>
              <p className="text-lg font-bold text-primary">
                {formatPrice(tour.start_price, tour.currency)}
              </p>
              <span className="text-xs text-muted-foreground">{t('perPerson')}</span>
            </div>
            <Badge variant="secondary" className="text-xs">
              {tour.difficulty === 'easy' ? 'Easy' : tour.difficulty === 'moderate' ? 'Moderate' : 'Challenging'}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
