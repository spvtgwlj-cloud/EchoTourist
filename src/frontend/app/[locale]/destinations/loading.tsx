import { Skeleton } from '@/components/ui/skeleton';

export default function DestinationsLoading() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-10 space-y-2">
        <Skeleton className="h-9 w-48" />
        <Skeleton className="h-4 w-72" />
      </div>
      <div className="space-y-16">
        {Array.from({ length: 3 }).map((_, i) => (
          <section key={i}>
            <div className="mb-6">
              <Skeleton className="h-7 w-40" />
              <Skeleton className="h-4 w-64 mt-1" />
              <Skeleton className="h-3 w-32 mt-1" />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
              {Array.from({ length: 5 }).map((_, j) => (
                <Skeleton key={j} className="aspect-[4/3] rounded-lg" />
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
