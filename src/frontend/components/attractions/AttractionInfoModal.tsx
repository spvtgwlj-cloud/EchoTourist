'use client';

import { useEffect, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X, ChevronLeft, ChevronRight, MapPin, Play } from 'lucide-react';
import { ImageWithFallback } from '@/components/ui/ImageWithFallback';

/* ──────────────────────────────────────────────────────────────────
   Types
   ────────────────────────────────────────────────────────────────── */

interface AttractionMediaItem {
  id: string;
  url: string;
  media_type: string; // "image" | "video"
  alt_text?: string;
  sort_order: number;
}

interface Attraction {
  id: string;
  slug: string;
  name: string;
  description?: string;
  image_url?: string;
  rating: number;
  media: AttractionMediaItem[];
}

interface AttractionInfoModalProps {
  attraction: Attraction;
  locale: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/* ──────────────────────────────────────────────────────────────────
   Component
   ────────────────────────────────────────────────────────────────── */

export default function AttractionInfoModal({
  attraction,
  open,
  onOpenChange,
}: AttractionInfoModalProps) {
  const [currentMediaIndex, setCurrentMediaIndex] = useState(0);
  const mediaItems = (attraction?.media || []).slice(0, 8); // max 8
  const hasMultiple = mediaItems.length > 1;

  // 重置索引当打开新景点时
  useEffect(() => {
    if (open) setCurrentMediaIndex(0);
  }, [open, attraction?.id]);

  // 防御性保护：attraction 为空时静默不渲染（必须在 hooks 之后）
  if (!attraction) return null;

  const goPrev = () => {
    setCurrentMediaIndex((prev) =>
      prev <= 0 ? mediaItems.length - 1 : prev - 1,
    );
  };
  const goNext = () => {
    setCurrentMediaIndex((prev) =>
      prev >= mediaItems.length - 1 ? 0 : prev + 1,
    );
  };

  const currentMedia = mediaItems[currentMediaIndex];

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-black/60 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <Dialog.Content
          className="fixed left-1/2 top-1/2 z-50 w-full max-w-3xl -translate-x-1/2 -translate-y-1/2
            rounded-2xl bg-white shadow-2xl
            data-[state=open]:animate-in data-[state=closed]:animate-out
            data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0
            data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95
            data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%]
            data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%]
            max-h-[90vh] overflow-y-auto"
        >
          {/* Close button */}
          <Dialog.Close className="absolute right-4 top-4 z-30 rounded-full bg-black/40 p-1.5 text-white hover:bg-black/60 transition-colors">
            <X className="h-5 w-5" />
          </Dialog.Close>

          {/* ── Media carousel ── */}
          <div className="relative aspect-[16/9] bg-gray-100 overflow-hidden rounded-t-2xl">
            {mediaItems.length > 0 && currentMedia && (
              <>
                {currentMedia.media_type === 'video' ? (
                  <div className="relative flex h-full items-center justify-center bg-black">
                    <video
                      src={currentMedia.url}
                      controls
                      className="h-full w-full object-contain"
                      poster={attraction.image_url || undefined}
                    />
                  </div>
                ) : (
                  <ImageWithFallback
                    src={currentMedia.url}
                    alt={currentMedia.alt_text || attraction.name}
                    className="h-full w-full object-cover"
                  />
                )}

                {/* Navigation arrows */}
                {hasMultiple && (
                  <>
                    <button
                      onClick={goPrev}
                      className="absolute left-3 top-1/2 -translate-y-1/2 rounded-full bg-black/40 p-1.5 text-white hover:bg-black/60 transition-colors"
                      aria-label="Previous"
                    >
                      <ChevronLeft className="h-5 w-5" />
                    </button>
                    <button
                      onClick={goNext}
                      className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-black/40 p-1.5 text-white hover:bg-black/60 transition-colors"
                      aria-label="Next"
                    >
                      <ChevronRight className="h-5 w-5" />
                    </button>
                  </>
                )}

                {/* Media type badge */}
                {currentMedia.media_type === 'video' && (
                  <div className="absolute bottom-3 left-3 flex items-center gap-1 rounded-full bg-black/50 px-2 py-0.5 text-xs text-white">
                    <Play className="h-3 w-3 fill-white" />
                    Video
                  </div>
                )}

                {/* Dot indicators */}
                {hasMultiple && (
                  <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-1.5">
                    {mediaItems.map((_, idx) => (
                      <button
                        key={idx}
                        onClick={() => setCurrentMediaIndex(idx)}
                        className={`h-2 w-2 rounded-full transition-colors ${
                          idx === currentMediaIndex
                            ? 'bg-white'
                            : 'bg-white/40 hover:bg-white/70'
                        }`}
                      />
                    ))}
                  </div>
                )}
              </>
            )}

            {/* Fallback when no media */}
            {mediaItems.length === 0 && (
              <div className="flex h-full items-center justify-center text-muted-foreground">
                <MapPin className="h-16 w-16 opacity-30" />
              </div>
            )}

            {/* Rating badge */}
            {attraction.rating > 0 && (
              <div className="absolute top-4 left-4 flex items-center gap-1 rounded-full bg-black/40 px-2.5 py-1 text-sm text-white">
                {'⭐'.repeat(attraction.rating)}
              </div>
            )}
          </div>

          {/* ── Content ── */}
          <div className="px-6 pb-6 pt-5">
            <Dialog.Title className="text-xl font-bold">
              {attraction.name}
            </Dialog.Title>

            {/* Description */}
            {attraction.description && (
              <p className="mt-3 text-sm leading-relaxed text-gray-600">
                {attraction.description}
              </p>
            )}

            {/* Thumbnail strip */}
            {mediaItems.length > 1 && (
              <div className="mt-4 flex items-center gap-2 overflow-x-auto pb-1">
                {mediaItems.map((item, idx) => (
                  <button
                    key={item.id}
                    onClick={() => setCurrentMediaIndex(idx)}
                    className={`relative shrink-0 overflow-hidden rounded-lg border-2 transition-all ${
                      idx === currentMediaIndex
                        ? 'border-blue-500 ring-2 ring-blue-300'
                        : 'border-transparent opacity-70 hover:opacity-100'
                    }`}
                  >
                    {item.media_type === 'video' ? (
                      <div className="relative flex h-14 w-20 items-center justify-center bg-gray-200">
                        <Play className="h-5 w-5 fill-gray-500 text-gray-500" />
                      </div>
                    ) : (
                      <ImageWithFallback
                        src={item.url}
                        alt={item.alt_text || `View ${idx + 1}`}
                        className="h-14 w-20 object-cover"
                      />
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
