'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useLocale } from 'next-intl';
import { useAuthStore } from '@/lib/stores/auth-store';
import { api } from '@/lib/api';
import { AdminLayout } from '@/components/admin/AdminLayout';
import { Button } from '@/components/ui/button';
import { ImageWithFallback } from '@/components/ui/ImageWithFallback';
import { Loader2, Save, ArrowLeft, Trash2, Upload, GripVertical, Film, ImageIcon } from 'lucide-react';
import Link from 'next/link';

// ── Types ─────────────────────────────────────────────────────────

interface TranslationData {
  id?: string;
  locale: string;
  name: string;
  description?: string;
  ticket_info?: string;
  opening_hours?: string;
  meta_title?: string;
  meta_description?: string;
}

interface MediaItem {
  id: string;
  url: string;
  media_type: string; // "image" | "video"
  alt_text?: string;
  sort_order: number;
}

interface AttractionDetail {
  id: string; slug: string; destination_id: string;
  image_url?: string; sort_order: number; rating: number;
  status: string; ticket_price: number; ticket_currency: string;
  translations: TranslationData[];
  media: MediaItem[];
}

const LOCALES = [
  { code: 'en', label: 'English' },
  { code: 'zh', label: '中文' },
  { code: 'es', label: 'Español' },
];

// ── Helpers ───────────────────────────────────────────────────────

function buildTranslationsMap(translations: TranslationData[]): Record<string, TranslationData> {
  const map: Record<string, TranslationData> = {};
  for (const t of translations) map[t.locale] = { ...t };
  return map;
}

function ensureAllLocales(map: Record<string, TranslationData>): Record<string, TranslationData> {
  const result = { ...map };
  for (const { code } of LOCALES) {
    if (!result[code]) {
      result[code] = { locale: code, name: '', description: '', ticket_info: '', opening_hours: '' };
    }
  }
  return result;
}

// ── Component ─────────────────────────────────────────────────────

export default function EditAttractionPage() {
  const { id } = useParams<{ id: string }>();
  const pageLocale = useLocale();
  const router = useRouter();
  const { isAuthenticated, user, token } = useAuthStore();

  const [attraction, setAttraction] = useState<AttractionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // ── Basic fields ──────────────────────────────
  const [status, setStatus] = useState('active');
  const [sortOrder, setSortOrder] = useState(0);
  const [rating, setRating] = useState(0);
  const [imageUrl, setImageUrl] = useState('');
  const [ticketPrice, setTicketPrice] = useState(0);
  const [ticketCurrency, setTicketCurrency] = useState('USD');
  const [media, setMedia] = useState<MediaItem[]>([]);

  // ── Multi-language translations ──────────────
  const [activeLocale, setActiveLocale] = useState(pageLocale);
  const [translationsMap, setTranslationsMap] = useState<Record<string, TranslationData>>({});
  const current = translationsMap[activeLocale] || { locale: activeLocale, name: '', description: '', ticket_info: '', opening_hours: '' };

  const updateCurrent = useCallback((field: string, value: string) => {
    setTranslationsMap(prev => ({
      ...prev,
      [activeLocale]: { ...(prev[activeLocale] || { locale: activeLocale }), [field]: value },
    }));
  }, [activeLocale]);

  // ── Load data ────────────────────────────────────────────────────

  useEffect(() => {
    if (!isAuthenticated || !user?.is_admin) { router.push(`/${pageLocale}/auth`); return; }
    api.get<AttractionDetail>(`/admin/attractions/${id}`, { cache: 'no-store' })
      .then((data) => {
        setAttraction(data);
        setStatus(data.status || 'active');
        setSortOrder(data.sort_order || 0);
        setRating(data.rating || 0);
        setImageUrl(data.image_url || '');
        setTicketPrice(data.ticket_price || 0);
        setTicketCurrency(data.ticket_currency || 'USD');
        setMedia(data.media || []);
        setTranslationsMap(ensureAllLocales(buildTranslationsMap(data.translations || [])));
      })
      .catch(() => setError('Failed to load attraction'))
      .finally(() => setLoading(false));
  }, [id, isAuthenticated, user, pageLocale, router]);

  // ── Save ─────────────────────────────────────────────────────────

  const handleSave = async () => {
    if (!token) return;
    setSaving(true); setError(''); setSuccess('');

    try {
      const translations = Object.values(translationsMap).filter(t => t.name);

      await api.patch(`/admin/attractions/${id}`, {
        status,
        sort_order: sortOrder,
        rating,
        image_url: imageUrl,
        ticket_price: ticketPrice,
        ticket_currency: ticketCurrency,
        translations,
      });
      setSuccess('Saved successfully');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  // ── Media Upload ─────────────────────────────────────────────────

  const handleUploadMedia = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !token) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/v1/admin/upload', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();

      // Add media record via API
      const mediaRes = await api.post<{ status: string; media: MediaItem }>(
        `/admin/attractions/${id}/media`,
        {
          url: data.url,
          media_type: data.type || 'image',
          alt_text: file.name.replace(/\.[^.]+$/, ''),
        },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      if (mediaRes.status === 'ok') {
        setMedia(prev => [...prev, mediaRes.media]);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDeleteMedia = async (mediaId: string) => {
    if (!token) return;
    try {
      await api.delete(`/admin/attractions/${id}/media/${mediaId}`);
      setMedia(prev => prev.filter(m => m.id !== mediaId));
    } catch {
      setError('Failed to delete media');
    }
  };

  // ── Loading state ────────────────────────────────────────────────

  if (loading) return (
    <AdminLayout>
      <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin" /></div>
    </AdminLayout>
  );

  if (!attraction) return (
    <AdminLayout><div className="text-center py-20 text-muted-foreground">Attraction not found</div></AdminLayout>
  );

  // ── Render ───────────────────────────────────────────────────────

  return (
    <AdminLayout>
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Link href={`/${pageLocale}/admin/attractions`} className="text-muted-foreground hover:text-gray-700">
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold">{attraction.slug}</h1>
              <p className="text-sm text-muted-foreground">Edit attraction details</p>
            </div>
          </div>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
            Save
          </Button>
        </div>

        {error && <div className="mb-4 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-600">{error}</div>}
        {success && <div className="mb-4 rounded-lg bg-green-50 border border-green-200 p-3 text-sm text-green-600">{success}</div>}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* ── Left: Basic Info ──────────────────── */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic fields */}
            <div className="rounded-lg border bg-white p-5">
              <h2 className="text-lg font-semibold mb-4">Basic Information</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Status</label>
                  <select value={status} onChange={e => setStatus(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Sort Order</label>
                  <input type="number" value={sortOrder} onChange={e => setSortOrder(Number(e.target.value))}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Rating (1-5)</label>
                  <input type="number" min={0} max={5} value={rating} onChange={e => setRating(Number(e.target.value))}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Ticket Price</label>
                  <input type="number" min={0} step={0.01} value={ticketPrice} onChange={e => setTicketPrice(Number(e.target.value))}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium mb-1">Image URL</label>
                  <input type="text" value={imageUrl} onChange={e => setImageUrl(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono" />
                  {imageUrl && (
                    <div className="mt-2 relative aspect-video overflow-hidden rounded-lg bg-gray-100 max-w-xs">
                      <ImageWithFallback src={imageUrl} alt="Preview" className="h-full w-full object-cover" />
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* ── Multi-language Translations ────── */}
            <div className="rounded-lg border bg-white p-5">
              <h2 className="text-lg font-semibold mb-4">Translations</h2>

              {/* Locale tabs */}
              <div className="flex gap-1 mb-4 border-b pb-2">
                {LOCALES.map(l => (
                  <button key={l.code} onClick={() => setActiveLocale(l.code)}
                    className={`px-3 py-1.5 text-sm rounded-t-md transition-colors ${
                      activeLocale === l.code ? 'bg-blue-50 text-blue-700 font-medium border-b-2 border-blue-500' : 'text-muted-foreground hover:text-gray-700'
                    }`}>
                    {l.label}
                  </button>
                ))}
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Name *</label>
                  <input type="text" value={current.name || ''}
                    onChange={e => updateCurrent('name', e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Description</label>
                  <textarea rows={5} value={current.description || ''}
                    onChange={e => updateCurrent('description', e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-y" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Ticket Info</label>
                    <input type="text" value={current.ticket_info || ''}
                      onChange={e => updateCurrent('ticket_info', e.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Opening Hours</label>
                    <input type="text" value={current.opening_hours || ''}
                      onChange={e => updateCurrent('opening_hours', e.target.value)}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ── Right: Media Management ─────────── */}
          <div className="space-y-6">
            <div className="rounded-lg border bg-white p-5">
              <h2 className="text-lg font-semibold mb-4">Media ({media.length}/8)</h2>

              {/* Upload */}
              <div className="mb-4">
                <label className="relative flex cursor-pointer items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 p-4 hover:border-gray-400 transition-colors">
                  <div className="text-center">
                    <Upload className="mx-auto h-6 w-6 text-muted-foreground" />
                    <span className="mt-1 block text-xs text-muted-foreground">
                      {uploading ? 'Uploading...' : 'Click to upload image/video'}
                    </span>
                  </div>
                  <input type="file" accept="image/*,video/mp4,video/webm" onChange={handleUploadMedia} disabled={uploading || media.length >= 8}
                    className="absolute inset-0 opacity-0 cursor-pointer" />
                </label>
              </div>

              {/* Media list */}
              <div className="space-y-2">
                {media.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-6">No media items yet</p>
                )}
                {media.map((m, idx) => (
                  <div key={m.id} className="flex items-center gap-3 rounded-lg border bg-gray-50 p-2">
                    <GripVertical className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <div className="h-14 w-20 shrink-0 overflow-hidden rounded bg-gray-200">
                      {m.media_type === 'video' ? (
                        <div className="flex h-full items-center justify-center">
                          <Film className="h-6 w-6 text-muted-foreground" />
                        </div>
                      ) : (
                        <ImageWithFallback src={m.url} alt={m.alt_text || `Media ${idx + 1}`} className="h-full w-full object-cover" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-mono truncate text-muted-foreground">{m.url.split('/').pop()}</p>
                      <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground">
                        {m.media_type === 'video' ? <Film className="h-3 w-3" /> : <ImageIcon className="h-3 w-3" />}
                        {m.media_type} · #{m.sort_order}
                      </span>
                    </div>
                    <button onClick={() => handleDeleteMedia(m.id)}
                      className="shrink-0 rounded-full p-1.5 text-red-400 hover:bg-red-50 hover:text-red-600 transition-colors">
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}
