'use client';

import { useState } from 'react';
import { MapPin } from 'lucide-react';
import { ImageWithFallback } from '@/components/ui/ImageWithFallback';
import { WishlistButton } from '@/components/user/WishlistButton';
import AttractionInfoModal from './AttractionInfoModal';

/* ──────────────────────────────────────────────────────────────────
   Types (mirrored from parent page for isolation)
   ────────────────────────────────────────────────────────────────── */

interface AttractionMediaItem {
  id: string;
  url: string;
  media_type: string;
  alt_text?: string;
  sort_order: number;
}

interface AttractionTicket {
  id: string;
  ticket_type: string;
  price: number;
  currency: string;
  availability: number;
  status: string;
}

interface Attraction {
  id: string;
  slug: string;
  name: string;
  description?: string;
  image_url?: string;
  sort_order: number;
  rating: number;
  ticket_price: number;
  ticket_currency: string;
  tickets: AttractionTicket[];
  media: AttractionMediaItem[];
}

interface AttractionsGridClientProps {
  attractions: Attraction[];
  locale: string;
  /** Hover button label: "More Information" (i18n) */
  moreInfoLabel?: string;
}

/* ──────────────────────────────────────────────────────────────────
   Component
   ────────────────────────────────────────────────────────────────── */

export default function AttractionsGridClient({
  attractions,
  locale,
  moreInfoLabel,
}: AttractionsGridClientProps) {
  const [selectedAttraction, setSelectedAttraction] = useState<Attraction | null>(null);

  if (attractions.length === 0) return null;

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {attractions.map((attr) => {
          const firstTicket =
            attr.ticket_price > 0 && attr.tickets && attr.tickets.length > 0
              ? attr.tickets[0]
              : null;

          return (
            <div
              key={attr.id}
              className="group relative aspect-[4/3] overflow-hidden rounded-xl bg-gray-100"
            >
              {attr.image_url ? (
                <ImageWithFallback
                  src={attr.image_url}
                  alt={attr.name}
                  className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                />
              ) : (
                <div className="flex h-full items-center justify-center text-muted-foreground">
                  <MapPin className="h-10 w-10" />
                </div>
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

              {/* Wishlist Button */}
              <div className="absolute top-2 right-2 z-10">
                <WishlistButton
                  itemId={attr.id}
                  itemType="attraction"
                  className="text-white/80 hover:text-red-400"
                />
              </div>

              <div className="absolute bottom-0 left-0 right-0 p-3 z-10">
                <h3 className="text-sm font-semibold text-white leading-tight">
                  {attr.name}
                </h3>
                <div className="mt-1 flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    {attr.rating > 0 && (
                      <span className="text-yellow-400 text-xs">
                        {'⭐'.repeat(attr.rating)}
                      </span>
                    )}
                  </div>
                  {attr.ticket_price > 0 && (
                    <span className="text-xs font-semibold text-yellow-300">
                      From ${attr.ticket_price}
                    </span>
                  )}
                </div>
              </div>

              {/* More Information Button (opens modal instead of direct checkout) */}
              {firstTicket && (
                <button
                  onClick={() => setSelectedAttraction(attr)}
                  className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20
                    px-4 py-2 rounded-lg bg-white/90 text-sm font-semibold text-gray-900
                    opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white shadow-lg
                    whitespace-nowrap"
                >
                  {moreInfoLabel || 'More Information'}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Modal */}
      {selectedAttraction && (
        <AttractionInfoModal
          key={selectedAttraction.id}
          attraction={selectedAttraction}
          locale={locale}
          open={!!selectedAttraction}
          onOpenChange={(open) => {
            if (!open) setSelectedAttraction(null);
          }}
        />
      )}
    </>
  );
}
