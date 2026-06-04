import { Skeleton } from '@/components/ui/skeleton';

export function TourCardSkeleton() {
  return (
    <div className="rounded-lg border bg-white overflow-hidden">
      {/* Image skeleton */}
      <Skeleton className="h-48 w-full rounded-none" />
      <div className="p-4 space-y-3">
        {/* Title */}
        <Skeleton className="h-5 w-3/4" />
        {/* Subtitle */}
        <Skeleton className="h-4 w-full" />
        {/* Price row */}
        <div className="flex items-center justify-between pt-2">
          <Skeleton className="h-6 w-24" />
          <Skeleton className="h-4 w-20" />
        </div>
        {/* Badge row */}
        <div className="flex gap-2 pt-1">
          <Skeleton className="h-5 w-16 rounded-full" />
          <Skeleton className="h-5 w-20 rounded-full" />
        </div>
      </div>
    </div>
  );
}

export function DestinationCardSkeleton() {
  return (
    <div className="relative h-64 rounded-xl overflow-hidden">
      <Skeleton className="h-full w-full rounded-xl" />
      <div className="absolute bottom-0 left-0 right-0 p-4 space-y-2">
        <Skeleton className="h-6 w-1/2 bg-white/30" />
        <Skeleton className="h-4 w-1/3 bg-white/20" />
      </div>
    </div>
  );
}

export function TourDetailSkeleton() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Gallery */}
      <Skeleton className="h-96 w-full rounded-xl mb-8" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <Skeleton className="h-8 w-2/3" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-40 w-full rounded-lg" />
        </div>
        <div className="space-y-4">
          <Skeleton className="h-48 w-full rounded-lg" />
          <Skeleton className="h-12 w-full rounded-lg" />
        </div>
      </div>
    </div>
  );
}

export function TourGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <TourCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function DestinationGridSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <DestinationCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 5, cols = 5 }: { rows?: number; cols?: number }) {
  return (
    <div className="rounded-lg border bg-white p-4 space-y-3">
      {/* Header */}
      <div className="flex gap-4 pb-2 border-b">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 py-2">
          {Array.from({ length: cols }).map((_, j) => (
            <Skeleton key={j} className="h-4 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

/** ── 首页专用 ── */

export function HomeHeroSkeleton() {
  return (
    <section className="bg-gradient-to-br from-primary/5 via-primary/10 to-accent/5">
      <div className="container mx-auto px-4 py-20 md:py-32">
        <div className="max-w-3xl space-y-6">
          <Skeleton className="h-12 w-3/4 md:h-16" />
          <Skeleton className="h-6 w-2/3" />
          <div className="flex flex-wrap gap-4 pt-4">
            <Skeleton className="h-12 w-36 rounded-lg" />
            <Skeleton className="h-12 w-36 rounded-lg" />
          </div>
        </div>
      </div>
    </section>
  );
}

export function HomeFeaturedSkeleton() {
  return (
    <section className="container mx-auto px-4 py-16">
      <div className="flex items-center justify-between mb-8">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-9 w-24" />
      </div>
      <TourGridSkeleton count={6} />
    </section>
  );
}

export function HomeFeaturesSkeleton() {
  return (
    <section className="bg-gray-50 py-16">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12 space-y-2">
          <Skeleton className="h-8 w-48 mx-auto" />
          <Skeleton className="h-4 w-72 mx-auto" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="text-center space-y-3">
              <Skeleton className="h-14 w-14 rounded-full mx-auto" />
              <Skeleton className="h-5 w-24 mx-auto" />
              <Skeleton className="h-4 w-40 mx-auto" />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function HomeDestinationsPreviewSkeleton() {
  return (
    <section className="container mx-auto px-4 py-16">
      <div className="text-center mb-12 space-y-2">
        <Skeleton className="h-8 w-48 mx-auto" />
        <Skeleton className="h-4 w-72 mx-auto" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="aspect-[4/3] rounded-xl" />
        ))}
      </div>
    </section>
  );
}

/** ── 目的地详情专用 ── */

export function DestinationDetailSkeleton() {
  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Back button */}
      <Skeleton className="h-4 w-20" />
      {/* Hero */}
      <div className="space-y-3">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-4 w-96" />
        <Skeleton className="h-4 w-32" />
      </div>
      {/* Attractions grid */}
      <div className="space-y-4">
        <Skeleton className="h-7 w-40" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="aspect-[4/3] rounded-xl" />
          ))}
        </div>
      </div>
      {/* Tours section */}
      <div className="space-y-4">
        <Skeleton className="h-7 w-40" />
        <TourGridSkeleton count={3} />
      </div>
    </div>
  );
}

/** ── 搜索页面专用 ── */

export function SearchPageSkeleton() {
  return (
    <div className="container mx-auto px-4 py-8 space-y-6">
      {/* Search bar */}
      <Skeleton className="h-12 w-full rounded-lg" />
      {/* Filters */}
      <div className="flex gap-3">
        <Skeleton className="h-9 w-24 rounded-full" />
        <Skeleton className="h-9 w-32 rounded-full" />
        <Skeleton className="h-9 w-28 rounded-full" />
      </div>
      {/* Results */}
      <TourGridSkeleton count={6} />
    </div>
  );
}

/** ── 管理后台仪表盘专用 ── */

export function AdminDashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-lg border bg-white p-5 space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-3 w-32" />
          </div>
        ))}
      </div>
      {/* Charts area */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-lg border bg-white p-5 space-y-3">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-48 w-full rounded" />
        </div>
        <div className="rounded-lg border bg-white p-5 space-y-3">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-48 w-full rounded" />
        </div>
      </div>
    </div>
  );
}
