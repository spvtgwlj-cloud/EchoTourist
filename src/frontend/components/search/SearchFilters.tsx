'use client';

import { useTranslations } from 'next-intl';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';

interface SearchFiltersProps {
  difficulty: string;
  theme: string;
  sortBy: string;
  onDifficultyChange: (d: string) => void;
  onThemeChange: (t: string) => void;
  onSortByChange: (s: string) => void;
  onClear: () => void;
}

const difficulties = ['easy', 'moderate', 'challenging'];
const themeOptions = [
  { value: 'citywalk', labelKey: 'themes.citywalk' },
  { value: 'culture_history', labelKey: 'themes.culture_history' },
  { value: 'nature', labelKey: 'themes.nature' },
  { value: 'food', labelKey: 'themes.food' },
  { value: 'honeymoon', labelKey: 'themes.honeymoon' },
  { value: 'family', labelKey: 'themes.family' },
  { value: 'adventure', labelKey: 'themes.adventure' },
  { value: 'photography', labelKey: 'themes.photography' },
  { value: 'luxury', labelKey: 'themes.luxury' },
  { value: 'wellness', labelKey: 'themes.wellness' },
  { value: 'hidden_gems', labelKey: 'themes.hidden_gems' },
  { value: 'festival', labelKey: 'themes.festival' },
];
const sortOptions = [
  { value: 'rating', key: 'rating' },
  { value: 'price_asc', key: 'priceLowToHigh' },
  { value: 'price_desc', key: 'priceHighToLow' },
  { value: 'duration', key: 'duration' },
];

export function SearchFilters({
  difficulty, theme, sortBy,
  onDifficultyChange, onThemeChange, onSortByChange, onClear,
}: SearchFiltersProps) {
  const t = useTranslations('search');
  const tt = useTranslations('tour');
  const hasFilters = difficulty || theme || sortBy !== 'rating';

  const difficultyLabels: Record<string, string> = {
    easy: tt('difficultyEasy'),
    moderate: tt('difficultyModerate'),
    challenging: tt('difficultyChallenging'),
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Sort */}
      <select
        value={sortBy}
        onChange={(e) => onSortByChange(e.target.value)}
        className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
      >
        {sortOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {t(opt.key as any)}
          </option>
        ))}
      </select>

      {/* Difficulty */}
      <div className="flex gap-1 flex-wrap">
        {difficulties.map((d) => (
          <button
            key={d}
            onClick={() => onDifficultyChange(difficulty === d ? '' : d)}
            className={`rounded-md px-3 py-1.5 text-sm border transition-colors ${
              difficulty === d
                ? 'border-primary bg-primary/10 text-primary'
                : 'border-input text-muted-foreground hover:border-primary/50'
            }`}
          >
            {difficultyLabels[d] || d.charAt(0).toUpperCase() + d.slice(1)}
          </button>
        ))}
      </div>

      {/* Theme */}
      <select
        value={theme}
        onChange={(e) => onThemeChange(e.target.value)}
        className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
      >
        <option value="">{tt('theme')}</option>
        {themeOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {tt(opt.labelKey as any)}
          </option>
        ))}
      </select>

      {hasFilters && (
        <Button variant="ghost" size="sm" onClick={onClear}>
          <X className="h-3 w-3 mr-1" /> {t('clearAll')}
        </Button>
      )}
    </div>
  );
}
