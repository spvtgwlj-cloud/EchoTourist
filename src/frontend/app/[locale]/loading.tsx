import { Skeleton } from '@/components/ui/skeleton';
import {
  HomeHeroSkeleton,
  HomeFeaturedSkeleton,
  HomeFeaturesSkeleton,
  HomeDestinationsPreviewSkeleton,
} from '@/components/ui/skeletons';

export default function HomeLoading() {
  return (
    <div>
      <HomeHeroSkeleton />
      <HomeFeaturedSkeleton />
      <HomeFeaturesSkeleton />
      <HomeDestinationsPreviewSkeleton />
      {/* CTA Section */}
      <section className="bg-primary py-16">
        <div className="container mx-auto px-4 text-center space-y-4">
          <Skeleton className="mx-auto h-8 w-64 bg-primary-foreground/20" />
          <Skeleton className="mx-auto h-5 w-96 bg-primary-foreground/20" />
          <Skeleton className="mx-auto h-12 w-36 rounded-lg bg-primary-foreground/20" />
        </div>
      </section>
    </div>
  );
}
