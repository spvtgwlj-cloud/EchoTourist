'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useLocale } from 'next-intl';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { Loader2, Plus, Trash2, Upload, X } from 'lucide-react';

interface TranslationInput {
  locale: string;
  name: string;
  subtitle: string;
  description: string;
  itinerary: string;
}

interface ImageInput {
  url: string;
  alt_text: string;
  sort_order: number;
}

interface DateInput {
  start_date: string;
  end_date: string;
  price_per_pax: number;
  availability: number;
}

const LOCALES = [
  { value: 'en', label: 'English' },
  { value: 'zh', label: '中文' },
  { value: 'es', label: 'Español' },
];

const EMPTY_TRANSLATION: TranslationInput = {
  locale: 'en', name: '', subtitle: '', description: '', itinerary: '',
};

export default function TourCreateForm() {
  const locale = useLocale();
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  // Basic fields
  const [slug, setSlug] = useState('');
  const [status, setStatus] = useState('draft');
  const [type, setType] = useState('group_tour');
  const [durationDays, setDurationDays] = useState(1);
  const [durationNights, setDurationNights] = useState(0);
  const [maxPax, setMaxPax] = useState(20);
  const [minPax, setMinPax] = useState(1);
  const [startPrice, setStartPrice] = useState(0);
  const [currency, setCurrency] = useState('USD');
  const [difficulty, setDifficulty] = useState('easy');

  // Arrays
  const [highlights, setHighlights] = useState<string[]>(['']);
  const [includes, setIncludes] = useState<string[]>(['']);
  const [excludes, setExcludes] = useState<string[]>(['']);

  // Translations
  const [translations, setTranslations] = useState<TranslationInput[]>([{ ...EMPTY_TRANSLATION }]);

  // Images
  const [images, setImages] = useState<ImageInput[]>([{ url: '', alt_text: '', sort_order: 1 }]);

  // Dates
  const [dates, setDates] = useState<DateInput[]>([
    { start_date: '', end_date: '', price_per_pax: 0, availability: 10 },
  ]);

  // Upload state
  const [uploading, setUploading] = useState(false);

  // ── Helper functions ──────────────────────────────────────────

  const handleArrayItem = (
    arr: string[],
    setter: (v: string[]) => void,
    index: number,
    value: string,
  ) => {
    const next = [...arr];
    next[index] = value;
    setter(next);
  };

  const addArrayItem = (arr: string[], setter: (v: string[]) => void) => {
    setter([...arr, '']);
  };

  const removeArrayItem = (arr: string[], setter: (v: string[]) => void, index: number) => {
    if (arr.length <= 1) return;
    setter(arr.filter((_, i) => i !== index));
  };

  // ── Image upload handler ──────────────────────────────────────

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>, index: number) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const token = localStorage.getItem('auth_token');
      const res = await fetch('/api/v1/admin/upload', {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();

      const next = [...images];
      next[index] = { ...next[index], url: data.url, alt_text: file.name.split('.')[0] };
      setImages(next);
    } catch (err) {
      setError('Image upload failed');
    } finally {
      setUploading(false);
    }
  };

  // ── Submit ────────────────────────────────────────────────────

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSaving(true);

    try {
      // Build itinerary from text areas
      const translationsPayload = translations
        .filter((t) => t.name)
        .map((t) => ({
          locale: t.locale,
          name: t.name,
          subtitle: t.subtitle || undefined,
          description: t.description || undefined,
          itinerary: t.itinerary
            ? t.itinerary.split('\n').filter(Boolean).map((line, i) => {
                const [title, ...descParts] = line.split('—');
                return { day: i + 1, title: title.trim(), description: descParts.join('—').trim() || title.trim() };
              })
            : undefined,
          meta_title: undefined,
          meta_description: undefined,
        }));

      const payload = {
        slug,
        status,
        type,
        duration_days: durationDays,
        duration_nights: durationNights,
        max_pax: maxPax || undefined,
        min_pax: minPax,
        start_price: startPrice,
        currency,
        difficulty,
        highlights: highlights.filter(Boolean),
        includes: includes.filter(Boolean),
        excludes: excludes.filter(Boolean),
        translations: translationsPayload,
        images: images.filter((img) => img.url).map((img, i) => ({
          url: img.url,
          alt_text: img.alt_text || undefined,
          sort_order: img.sort_order || i + 1,
        })),
        dates: dates
          .filter((d) => d.start_date && d.end_date)
          .map((d) => ({
            start_date: d.start_date,
            end_date: d.end_date,
            price_per_pax: d.price_per_pax,
            currency,
            availability: d.availability,
          })),
      };

      const result = await api.post<{ status: string; id: string }>('/admin/tours', payload);
      router.push(`/${locale}/admin/tours`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create tour');
    } finally {
      setSaving(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────

  return (
    <form onSubmit={handleSubmit} className="space-y-8 max-w-4xl">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* ── Basic Info ───────────────────────────────────────── */}
      <section className="bg-white rounded-lg border p-6 space-y-4">
        <h2 className="text-lg font-semibold">Basic Information</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Slug *</label>
            <input
              required
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
              className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
              placeholder="my-tour-slug"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value="draft">Draft</option>
              <option value="published">Published</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="w-full border rounded-md px-3 py-2 text-sm"
            >
              <option value="group_tour">Group Tour</option>
              <option value="private_tour">Private Tour</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Difficulty</label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
              className="w-full border rounded-md px-3 py-2 text-sm"
            >
              <option value="easy">Easy</option>
              <option value="moderate">Moderate</option>
              <option value="challenging">Challenging</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Duration (Days) *</label>
            <input
              type="number" min={1} required
              value={durationDays}
              onChange={(e) => setDurationDays(Number(e.target.value))}
              className="w-full border rounded-md px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Duration (Nights)</label>
            <input
              type="number" min={0}
              value={durationNights}
              onChange={(e) => setDurationNights(Number(e.target.value))}
              className="w-full border rounded-md px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Start Price *</label>
            <input
              type="number" min={0} step="0.01" required
              value={startPrice}
              onChange={(e) => setStartPrice(Number(e.target.value))}
              className="w-full border rounded-md px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Currency</label>
            <select
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className="w-full border rounded-md px-3 py-2 text-sm"
            >
              <option value="USD">USD</option>
              <option value="CNY">CNY</option>
              <option value="EUR">EUR</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Max Pax</label>
            <input
              type="number" min={1}
              value={maxPax}
              onChange={(e) => setMaxPax(Number(e.target.value))}
              className="w-full border rounded-md px-3 py-2 text-sm"
              placeholder="Max group size"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Min Pax</label>
            <input
              type="number" min={1}
              value={minPax}
              onChange={(e) => setMinPax(Number(e.target.value))}
              className="w-full border rounded-md px-3 py-2 text-sm"
            />
          </div>
        </div>
      </section>

      {/* ── Translations ─────────────────────────────────────── */}
      <section className="bg-white rounded-lg border p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Translations</h2>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              const usedLocales = translations.map((t) => t.locale);
              const next = LOCALES.find((l) => !usedLocales.includes(l.value));
              if (next) setTranslations([...translations, { ...EMPTY_TRANSLATION, locale: next.value }]);
            }}
          >
            <Plus className="h-3 w-3 mr-1" /> Add Language
          </Button>
        </div>

        {translations.map((t, i) => (
          <div key={i} className="border rounded-lg p-4 space-y-3 bg-gray-50/50">
            <div className="flex items-center justify-between">
              <select
                value={t.locale}
                onChange={(e) => {
                  const next = [...translations];
                  next[i] = { ...next[i], locale: e.target.value };
                  setTranslations(next);
                }}
                className="border rounded-md px-3 py-1.5 text-sm font-medium"
              >
                {LOCALES.map((l) => (
                  <option key={l.value} value={l.value} disabled={translations.some((x, j) => j !== i && x.locale === l.value)}>
                    {l.label}
                  </option>
                ))}
              </select>
              {translations.length > 1 && (
                <button type="button" onClick={() => setTranslations(translations.filter((_, j) => j !== i))} className="text-red-500 hover:text-red-700">
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium mb-1">Name *</label>
                <input
                  required
                  value={t.name}
                  onChange={(e) => {
                    const next = [...translations];
                    next[i] = { ...next[i], name: e.target.value };
                    setTranslations(next);
                  }}
                  className="w-full border rounded-md px-3 py-1.5 text-sm"
                  placeholder="Tour name"
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">Subtitle</label>
                <input
                  value={t.subtitle}
                  onChange={(e) => {
                    const next = [...translations];
                    next[i] = { ...next[i], subtitle: e.target.value };
                    setTranslations(next);
                  }}
                  className="w-full border rounded-md px-3 py-1.5 text-sm"
                  placeholder="Short subtitle"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Description</label>
              <textarea
                rows={3}
                value={t.description}
                onChange={(e) => {
                  const next = [...translations];
                  next[i] = { ...next[i], description: e.target.value };
                  setTranslations(next);
                }}
                className="w-full border rounded-md px-3 py-1.5 text-sm"
                placeholder="Tour description..."
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">
                Itinerary <span className="text-muted-foreground">(one per line: Day Title — Description)</span>
              </label>
              <textarea
                rows={3}
                value={t.itinerary}
                onChange={(e) => {
                  const next = [...translations];
                  next[i] = { ...next[i], itinerary: e.target.value };
                  setTranslations(next);
                }}
                className="w-full border rounded-md px-3 py-1.5 text-sm font-mono"
                placeholder="Day 1 — Visit the Great Wall&#10;Day 2 — Explore the Forbidden City"
              />
            </div>
          </div>
        ))}
      </section>

      {/* ── Highlights / Includes / Excludes ─────────────────── */}
      <section className="bg-white rounded-lg border p-6 space-y-6">
        <h2 className="text-lg font-semibold">Features</h2>

        {[
          { label: 'Highlights', items: highlights, setter: setHighlights },
          { label: 'Includes', items: includes, setter: setIncludes },
          { label: 'Excludes', items: excludes, setter: setExcludes },
        ].map(({ label, items, setter }) => (
          <div key={label}>
            <label className="block text-sm font-medium mb-2">{label}</label>
            {items.map((item, i) => (
              <div key={i} className="flex items-center gap-2 mb-2">
                <input
                  value={item}
                  onChange={(e) => handleArrayItem(items, setter, i, e.target.value)}
                  className="flex-1 border rounded-md px-3 py-1.5 text-sm"
                  placeholder={`${label} item...`}
                />
                <button type="button" onClick={() => removeArrayItem(items, setter, i)} className="text-red-400 hover:text-red-600">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
            <Button type="button" variant="ghost" size="sm" onClick={() => addArrayItem(items, setter)}>
              <Plus className="h-3 w-3 mr-1" /> Add
            </Button>
          </div>
        ))}
      </section>

      {/* ── Images ───────────────────────────────────────────── */}
      <section className="bg-white rounded-lg border p-6 space-y-4">
        <h2 className="text-lg font-semibold">Images</h2>

        {images.map((img, i) => (
          <div key={i} className="border rounded-lg p-4 space-y-3 bg-gray-50/50">
            <div className="flex items-start gap-3">
              {img.url && (
                <div className="w-20 h-20 rounded border overflow-hidden flex-shrink-0 bg-gray-100">
                  <img src={img.url} alt="" className="w-full h-full object-cover" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }} />
                </div>
              )}
              <div className="flex-1 space-y-2">
                <div className="flex gap-2">
                  <input
                    value={img.url}
                    onChange={(e) => {
                      const next = [...images];
                      next[i] = { ...next[i], url: e.target.value };
                      setImages(next);
                    }}
                    className="flex-1 border rounded-md px-3 py-1.5 text-sm"
                    placeholder="Image URL"
                  />
                  <label className="cursor-pointer">
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => handleImageUpload(e, i)}
                    />
                    <span className="inline-flex items-center px-3 py-1.5 border rounded-md text-sm hover:bg-gray-50">
                      {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                    </span>
                  </label>
                </div>
                <input
                  value={img.alt_text}
                  onChange={(e) => {
                    const next = [...images];
                    next[i] = { ...next[i], alt_text: e.target.value };
                    setImages(next);
                  }}
                  className="w-full border rounded-md px-3 py-1.5 text-sm"
                  placeholder="Alt text"
                />
              </div>
              {images.length > 1 && (
                <button type="button" onClick={() => setImages(images.filter((_, j) => j !== i))} className="text-red-400 hover:text-red-600 mt-1">
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
        ))}
        <Button type="button" variant="outline" size="sm" onClick={() => setImages([...images, { url: '', alt_text: '', sort_order: images.length + 1 }])}>
          <Plus className="h-3 w-3 mr-1" /> Add Image
        </Button>
      </section>

      {/* ── Tour Dates ───────────────────────────────────────── */}
      <section className="bg-white rounded-lg border p-6 space-y-4">
        <h2 className="text-lg font-semibold">Tour Dates</h2>

        {dates.map((d, i) => (
          <div key={i} className="border rounded-lg p-4 space-y-3 bg-gray-50/50">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Date #{i + 1}</span>
              {dates.length > 1 && (
                <button type="button" onClick={() => setDates(dates.filter((_, j) => j !== i))} className="text-red-400 hover:text-red-600">
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium mb-1">Start Date *</label>
                <input
                  type="date" required
                  value={d.start_date}
                  onChange={(e) => {
                    const next = [...dates];
                    next[i] = { ...next[i], start_date: e.target.value };
                    setDates(next);
                  }}
                  className="w-full border rounded-md px-3 py-1.5 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">End Date *</label>
                <input
                  type="date" required
                  value={d.end_date}
                  onChange={(e) => {
                    const next = [...dates];
                    next[i] = { ...next[i], end_date: e.target.value };
                    setDates(next);
                  }}
                  className="w-full border rounded-md px-3 py-1.5 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">Price Per Pax *</label>
                <input
                  type="number" min={0} step="0.01" required
                  value={d.price_per_pax}
                  onChange={(e) => {
                    const next = [...dates];
                    next[i] = { ...next[i], price_per_pax: Number(e.target.value) };
                    setDates(next);
                  }}
                  className="w-full border rounded-md px-3 py-1.5 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">Availability</label>
                <input
                  type="number" min={0}
                  value={d.availability}
                  onChange={(e) => {
                    const next = [...dates];
                    next[i] = { ...next[i], availability: Number(e.target.value) };
                    setDates(next);
                  }}
                  className="w-full border rounded-md px-3 py-1.5 text-sm"
                />
              </div>
            </div>
          </div>
        ))}
        <Button type="button" variant="outline" size="sm" onClick={() => setDates([...dates, { start_date: '', end_date: '', price_per_pax: 0, availability: 10 }])}>
          <Plus className="h-3 w-3 mr-1" /> Add Date
        </Button>
      </section>

      {/* ── Submit ──────────────────────────────────────────── */}
      <div className="flex items-center gap-4 pb-8">
        <Button type="submit" disabled={saving} size="lg">
          {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
          {saving ? 'Creating...' : 'Create Tour'}
        </Button>
        <Button type="button" variant="outline" size="lg" onClick={() => router.back()}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
