'use client';

import { useTranslations } from 'next-intl';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Star, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

interface ReviewFormProps {
  tourId: string;
  token: string;
  onSuccess: () => void;
  onCancel?: () => void;
}

export function ReviewForm({ tourId, token, onSuccess, onCancel }: ReviewFormProps) {
  const t = useTranslations('tour');
  const [rating, setRating] = useState(5);
  const [title, setTitle] = useState('');
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      await api.post('/reviews', { tour_id: tourId, rating, title, comment: comment || undefined, locale: 'en' },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to submit review');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 border rounded-lg p-4">
      <h3 className="font-semibold">{t('writeReview')}</h3>

      <div className="flex items-center gap-1">
        {Array.from({ length: 5 }, (_, i) => (
          <button key={i} type="button" onClick={() => setRating(i + 1)}>
            <Star className={`h-6 w-6 ${i < rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-200'}`} />
          </button>
        ))}
      </div>

      <input
        type="text" value={title} placeholder={t('reviewTitle') || 'Review title'}
        onChange={(e) => setTitle(e.target.value)}
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
      />

      <textarea
        value={comment} placeholder={t('reviewComment') || 'Share your experience'}
        onChange={(e) => setComment(e.target.value)}
        rows={3}
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
      />

      {error && <p className="text-sm text-red-500">{error}</p>}

      <div className="flex gap-2">
        <Button type="submit" disabled={submitting}>
          {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
          {t('submitReview')}
        </Button>
        {onCancel && <Button type="button" variant="outline" onClick={onCancel}>{t('cancel')}</Button>}
      </div>
    </form>
  );
}
