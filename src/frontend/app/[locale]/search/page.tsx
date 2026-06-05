'use client';

import { useTranslations, useLocale } from 'next-intl';
import { useSearchParams, useRouter } from 'next/navigation';
import { useState, useEffect, useCallback } from 'react';
import { TourCard } from '@/components/tours/TourCard';
import { SearchInput } from '@/components/search/SearchInput';
import { SearchFilters } from '@/components/search/SearchFilters';
import { api } from '@/lib/api';
import { Search as SearchIcon, Loader2 } from 'lucide-react';
import type { Tour } from '@/lib/types';
import { TourGridSkeleton } from '@/components/ui/skeletons';

interface SearchResult {
  tours: Tour[];
  total: number;
  page: number;
  page_size: number;
}

export default function SearchPage() {
  const t = useTranslations('search');
  const locale = useLocale();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [difficulty, setDifficulty] = useState(searchParams.get('difficulty') || '');
  const [sortBy, setSortBy] = useState(searchParams.get('sort_by') || 'rating');
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const doSearch = useCallback(async (q: string, diff: string, sort: string) => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams({
        locale, sort_by: sort, page: '1', page_size: '12',
      });
      if (q) params.set('q', q);
      if (diff) params.set('difficulty', diff);
      const res = await api.get<SearchResult>(`/search?${params}`);
      setResults(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  }, [locale]);

  useEffect(() => {
    const timer = setTimeout(() => doSearch(query, difficulty, sortBy), 300);
    return () => clearTimeout(timer);
  }, [query, difficulty, sortBy, doSearch]);

  const handleClear = () => { setQuery(''); setDifficulty(''); setSortBy('rating'); };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-4">{t('title')}</h1>
        <SearchInput value={query} onChange={setQuery} />
      </div>

      <div className="mb-6">
        <SearchFilters
          difficulty={difficulty}
          sortBy={sortBy}
          onDifficultyChange={setDifficulty}
          onSortByChange={setSortBy}
          onClear={handleClear}
        />
      </div>

      {loading && (
        <div>
          <div className="flex items-center gap-2 mb-6">
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            <span className="text-sm text-muted-foreground">{t('searching')}</span>
          </div>
          <TourGridSkeleton count={6} />
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-600">
          {error}
        </div>
      )}

      {!loading && !error && results && (
        <>
          <p className="mb-6 text-sm text-muted-foreground">
            {t('results', { count: results.total })}
          </p>

          {results.tours.length === 0 ? (
            <div className="text-center py-20">
              <SearchIcon className="mx-auto h-12 w-12 text-muted-foreground/50" />
              <p className="mt-4 text-muted-foreground">{t('noResults')}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {results.tours.map((tour: any) => (
                <TourCard key={tour.id} tour={tour} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
