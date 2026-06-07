'use client';

import { useTranslations, useLocale } from 'next-intl';
import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import {
  Star, Clock, Users, MapPin, CheckCircle, XCircle,
} from 'lucide-react';
import { formatPrice, formatDate } from '@/lib/utils';
import { ImageWithFallback } from '@/components/ui/ImageWithFallback';
import { WishlistButton } from '@/components/user/WishlistButton';
import type { Tour, TourDate } from '@/lib/types';

interface TourDetailClientProps {
  tour: Tour;
  dates: TourDate[];
  locale: string;
}

export function TourDetailClient({ tour, dates, locale }: TourDetailClientProps) {
  const t = useTranslations('tour');
  const ct = useTranslations('common');
  const bt = useTranslations('booking');
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [pax, setPax] = useState(1);
  const [currentImage, setCurrentImage] = useState(0);

  const availableDates = dates.filter((d) => d.status === 'available' && d.availability > 0);
  const selectedDateData = dates.find((d) => d.id === selectedDate);
  const totalPrice = selectedDateData ? selectedDateData.price_per_pax * pax : tour.start_price * pax;

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm text-muted-foreground">
        <Link href={`/${locale}/tours`} className="hover:text-primary">{ct('viewAll')}</Link>
        <span className="mx-2">/</span>
        <span className="text-foreground">{tour.name}</span>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-8">
          {/* Image Gallery */}
          <div className="relative aspect-[16/9] overflow-hidden rounded-xl bg-gray-100">
            {tour.images?.length ? (
              <ImageWithFallback
                src={tour.images[currentImage]?.url || tour.images[currentImage] as unknown as string}
                alt={tour.name}
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <Clock className="h-16 w-16" />
              </div>
            )}
            {tour.images?.length > 1 && (
              <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
                {tour.images.map((_, i) => (
                  <button
                    key={i}
                    className={`h-2 w-2 rounded-full ${i === currentImage ? 'bg-white' : 'bg-white/50'}`}
                    onClick={() => setCurrentImage(i)}
                  />
                ))}
              </div>
            )}
            {tour.avg_rating > 0 && (
              <div className="absolute top-4 right-4 flex items-center gap-1 rounded-full bg-white/90 px-3 py-1.5 text-sm font-medium">
                <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                {tour.avg_rating.toFixed(1)} ({tour.review_count})
              </div>
            )}
          </div>

          {/* Tour Info */}
          <div>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap gap-2 mb-3">
                  <Badge variant="secondary">
                    {tour.difficulty === 'easy' ? t('difficultyEasy') : tour.difficulty === 'moderate' ? t('difficultyModerate') : t('difficultyChallenging')}
                  </Badge>
                  {tour.theme && (
                    <Badge variant="default" className="bg-amber-600 hover:bg-amber-700">
                      {t(`themes.${tour.theme}` as any)}
                    </Badge>
                  )}
                  <Badge variant="outline">{tour.category_name}</Badge>
                </div>
                <h1 className="text-3xl font-bold">{tour.name}</h1>
                {tour.subtitle && (
                  <p className="mt-2 text-lg text-muted-foreground">{tour.subtitle}</p>
                )}
              </div>
              <WishlistButton tourId={tour.id} className="mt-1 shrink-0" />
            </div>

            <div className="mt-4 flex flex-wrap gap-4 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {t('duration', { days: tour.duration_days, nights: tour.duration_nights })}
              </span>
              {tour.max_pax && (
                <span className="flex items-center gap-1">
                  <Users className="h-4 w-4" />
                  {t('maxPax', { count: tour.max_pax })}
                </span>
              )}
              <span className="flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                {tour.destination_name}
              </span>
            </div>
          </div>

          {/* Overview */}
          {tour.description && (
            <section>
              <h2 className="text-xl font-semibold mb-3">{t('overview')}</h2>
              <p className="text-muted-foreground leading-relaxed">{tour.description}</p>
            </section>
          )}

          {/* Highlights */}
          {tour.highlights?.length > 0 && (
            <section>
              <h2 className="text-xl font-semibold mb-3">{t('highlights')}</h2>
              <ul className="space-y-2">
                {tour.highlights.map((h, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 shrink-0" />
                    <span>{h}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Itinerary */}
          {tour.itinerary?.length && (
            <section>
              <h2 className="text-xl font-semibold mb-4">{t('itinerary')}</h2>
              <div className="space-y-3">
                {tour.itinerary.map((day) => (
                  <Card key={day.day}>
                    <CardContent className="p-4">
                      <div className="flex gap-4">
                        <div className="flex flex-col items-center">
                          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary">
                            {String(day.day).padStart(2, '0')}
                          </div>
                          {day.day < (tour.itinerary?.length || 1) && (
                            <div className="mt-1 w-0.5 flex-1 bg-border" />
                          )}
                        </div>
                        <div className="flex-1 pb-4">
                          <h3 className="font-semibold">{day.title}</h3>
                          <p className="mt-1 text-sm text-muted-foreground">{day.description}</p>
                          {day.meals?.length && (
                            <div className="mt-2 flex gap-2">
                              {day.meals.map((meal) => (
                                <Badge key={meal} variant="outline" className="text-xs">
                                  {meal}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>
          )}

          {/* Includes / Excludes */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {tour.includes?.length > 0 && (
              <section>
                <h2 className="text-xl font-semibold mb-3">{t('includes')}</h2>
                <ul className="space-y-2">
                  {tour.includes.map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </section>
            )}
            {tour.excludes?.length > 0 && (
              <section>
                <h2 className="text-xl font-semibold mb-3">{t('excludes')}</h2>
                <ul className="space-y-2">
                  {tour.excludes.map((item, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <XCircle className="h-4 w-4 text-red-400 mt-0.5 shrink-0" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </div>
        </div>

        {/* Booking Sidebar */}
        <div className="lg:col-span-1">
          <div className="sticky top-24 space-y-4">
            <Card>
              <CardContent className="p-6 space-y-4">
                <div>
                  <span className="text-sm text-muted-foreground">{t('from')}</span>
                  <p className="text-3xl font-bold text-primary">
                    {formatPrice(selectedDateData?.price_per_pax || tour.start_price, tour.currency, locale)}
                  </p>
                  <span className="text-sm text-muted-foreground">{t('perPerson')}</span>
                </div>

                <div className="border-t pt-4">
                  <label className="text-sm font-medium">{t('selectDate')}</label>
                  <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">
                    {availableDates.length === 0 ? (
                      <p className="text-sm text-muted-foreground">{t('noDates')}</p>
                    ) : (
                      availableDates.map((d) => (
                        <button
                          key={d.id}
                          onClick={() => setSelectedDate(d.id)}
                          className={`w-full text-left px-3 py-2 rounded-md text-sm border transition-colors ${
                            selectedDate === d.id
                              ? 'border-primary bg-primary/5 text-primary'
                              : 'hover:border-primary/50'
                          }`}
                        >
                          <div className="flex justify-between">
                            <span>{formatDate(d.start_date, locale)}</span>
                            <span className="font-medium">{formatPrice(d.price_per_pax, d.currency, locale)}</span>
                          </div>
                          {d.availability <= 3 && d.availability > 0 && (
                            <span className="text-xs text-amber-600">
                              {t('limitedSpots', { count: d.availability })}
                            </span>
                          )}
                        </button>
                      ))
                    )}
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium">{t('guests')}</label>
                  <div className="mt-2 flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => setPax(Math.max(1, pax - 1))}
                    >
                      -
                    </Button>
                    <span className="w-12 text-center font-medium">{pax}</span>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => setPax(Math.min(tour.max_pax || 20, pax + 1))}
                    >
                      +
                    </Button>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <div className="flex justify-between text-lg font-bold">
                    <span>{t('totalPrice')}</span>
                    <span className="text-primary">{formatPrice(totalPrice, tour.currency, locale)}</span>
                  </div>
                </div>

                <Link
                  href={
                    selectedDate
                      ? `/${locale}/checkout?tour=${tour.id}&date=${selectedDate}&pax=${pax}`
                      : '#'
                  }
                  className="block"
                >
                  <Button className="w-full" size="lg" disabled={!selectedDate}>
                    {t('bookNow')}
                  </Button>
                </Link>

                <div className="text-xs text-muted-foreground text-center space-y-1">
                  <p>{t('freeCancellation')} • {t('instantConfirmation')}</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
