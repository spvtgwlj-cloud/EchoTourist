'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';
import { useRouter } from 'next/navigation';
import { useLocale } from 'next-intl';
import { api } from '@/lib/api';
import { AdminLayout } from '@/components/admin/AdminLayout';
import { Button } from '@/components/ui/button';
import { Star } from 'lucide-react';
import { TableSkeleton } from '@/components/ui/skeletons';

interface ReviewItem {
  id: string; tour_id: string; user_id: string;
  rating: number; title?: string; comment?: string;
  status: string; created_at: string;
}

export default function AdminReviews() {
  const locale = useLocale();
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('pending');

  const fetchReviews = (status: string) => {
    setLoading(true);
    api.get<{ reviews: ReviewItem[]; total: number }>(`/admin/reviews?status=${status}`, { cache: 'no-store' })
      .then((res) => { setReviews(res.reviews || []); setTotal(res.total); })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!isAuthenticated || !user?.is_admin) { router.push(`/${locale}/auth`); return; }
    fetchReviews(filter);
  }, [isAuthenticated, user, locale, router, filter]);

  const moderateReview = async (id: string, status: string) => {
    await api.patch(`/admin/reviews/${id}`, { status });
    fetchReviews(filter);
  };

  if (loading) return <AdminLayout>
    <div className="flex items-center justify-between mb-6">
      <div><div className="h-7 w-40 bg-gray-200 animate-pulse rounded" /><div className="h-4 w-32 bg-gray-200 animate-pulse rounded mt-2" /></div>
    </div>
    <TableSkeleton rows={4} cols={6} />
  </AdminLayout>;

  return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Reviews ({total})</h1>
        <div className="flex gap-2">
          {['pending', 'approved', 'rejected'].map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1.5 rounded-md text-sm border ${filter === s ? 'border-primary bg-primary/10 text-primary' : 'border-input text-muted-foreground'}`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        {reviews.length === 0 ? (
          <div className="text-center py-20 text-muted-foreground">No reviews found</div>
        ) : reviews.map((review) => (
          <div key={review.id} className="rounded-lg border bg-white p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className="flex gap-0.5">
                  {Array.from({ length: 5 }, (_, i) => (
                    <Star key={i} className={`h-4 w-4 ${i < review.rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-200'}`} />
                  ))}
                </div>
              </div>
              <span className="text-xs text-muted-foreground">
                {review.created_at ? new Date(review.created_at).toLocaleDateString() : ''}
              </span>
            </div>
            {review.title && <p className="font-medium text-sm">{review.title}</p>}
            {review.comment && <p className="text-sm text-muted-foreground mt-1">{review.comment}</p>}
            {review.status === 'pending' && (
              <div className="flex gap-2 mt-3">
                <Button size="sm" onClick={() => moderateReview(review.id, 'approved')}>Approve</Button>
                <Button size="sm" variant="outline" onClick={() => moderateReview(review.id, 'rejected')}>Reject</Button>
              </div>
            )}
          </div>
        ))}
      </div>
    </AdminLayout>
  );
}
