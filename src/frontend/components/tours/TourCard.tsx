'use client';

import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Star, Clock, Users, MapPin } from 'lucide-react';
import { formatPrice } from '@/lib/utils';
import { ImageWithFallback } from '@/components/ui/ImageWithFallback';
import { WishlistButton } from '@/components/user/WishlistButton';
import type { Tour } from '@/lib/types';

interface TourCardProps {
  tour: Tour;
}

/** 主题 → 颜色映射，覆盖主流分类并兼顾年轻人审美 */
const THEME_COLORS: Record<string, string> = {
  citywalk: 'bg-rose-500 hover:bg-rose-600',
  culture_history: 'bg-amber-600 hover:bg-amber-700',
  nature: 'bg-emerald-600 hover:bg-emerald-700',
  food: 'bg-orange-500 hover:bg-orange-600',
  honeymoon: 'bg-pink-500 hover:bg-pink-600',
  family: 'bg-sky-500 hover:bg-sky-600',
  luxury: 'bg-purple-600 hover:bg-purple-700',
  adventure: 'bg-red-600 hover:bg-red-700',
  photography: 'bg-indigo-500 hover:bg-indigo-600',
  wellness: 'bg-teal-500 hover:bg-teal-600',
  hidden_gems: 'bg-violet-500 hover:bg-violet-600',
  festival: 'bg-fuchsia-500 hover:bg-fuchsia-600',
};

export function TourCard({ tour }: TourCardProps) {
  const t = useTranslations('tour');
  const locale = useLocale();
  const themeLabel = t(`themes.${tour.theme}` as any);
  const themeColor = THEME_COLORS[tour.theme] || 'bg-gray-500';

  return (
    <Link href={`/${locale}/tours/${tour.slug}`}>
      <Card className="group overflow-hidden transition-all hover:shadow-lg">
        <div className="relative aspect-[16/9] overflow-hidden bg-gray-100">
          {tour.images?.[0] ? (
            <ImageWithFallback
              src={tour.images[0]?.url}
              alt={tour.name}
              className="h-full w-full object-cover transition-transform group-hover:scale-105"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              <MapPin className="h-12 w-12" />
            </div>
          )}
          {/* 主题标签 — 最佳位置：图片左上角，与评分同排 */}
          <div className="absolute top-3 left-3 flex items-center gap-2">
            <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold text-white shadow-sm ${themeColor}`}>
              {themeLabel || tour.theme}
            </span>
            {tour.avg_rating > 0 && (
              <span className="inline-flex items-center gap-1 rounded-full bg-white/90 px-2.5 py-1 text-xs font-medium shadow-sm">
                <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                {tour.avg_rating.toFixed(1)}
              </span>
            )}
          </div>
          <div className="absolute top-3 right-3">
            <WishlistButton tourId={tour.id} />
          </div>
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
                {formatPrice(tour.start_price, tour.currency, locale)}
              </p>
              <span className="text-xs text-muted-foreground">{t('perPerson')}</span>
            </div>
            <Badge variant="secondary" className="text-xs">
              {tour.difficulty === 'easy' ? t('difficultyEasy') : tour.difficulty === 'moderate' ? t('difficultyModerate') : t('difficultyChallenging')}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
