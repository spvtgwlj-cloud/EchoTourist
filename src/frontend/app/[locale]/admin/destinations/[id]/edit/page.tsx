'use client';

import { useTranslations } from 'next-intl';
import { useLocale } from 'next-intl';
import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { api } from '@/lib/api';
import { AdminLayout } from '@/components/admin/AdminLayout';
import { MapPin, Save, ArrowLeft, Loader2 } from 'lucide-react';
import Link from 'next/link';

interface TranslationEntry {
  id?: string;
  locale: string;
  name: string;
  description: string;
  meta_title: string;
  meta_description: string;
}

export default function AdminEditDestinationPage() {
  const t = useTranslations('admin');
  const locale = useLocale();
  const router = useRouter();
  const params = useParams();
  const destId = params.id as string;

  const [loading, setLoading] = useState(true);
  const [slug, setSlug] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [status, setStatus] = useState('active');
  const [translations, setTranslations] = useState<TranslationEntry[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.get<any>(`/admin/destinations/${destId}`);
        setSlug(data.slug || '');
        setImageUrl(data.image_url || '');
        setStatus(data.status || 'active');
        setTranslations(
          data.translations?.map((t: any) => ({
            id: t.id,
            locale: t.locale,
            name: t.name || '',
            description: t.description || '',
            meta_title: t.meta_title || '',
            meta_description: t.meta_description || '',
          })) || []
        );
      } catch (e: any) {
        setError(e?.message || 'Failed to load destination');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [destId]);

  const setTrans = (locale: string, field: keyof TranslationEntry, value: string) => {
    setTranslations(prev =>
      prev.map(t => (t.locale === locale ? { ...t, [field]: value } : t))
    );
  };

  const handleSubmit = async () => {
    if (!slug.trim()) { setError('Slug is required'); return; }

    setSaving(true);
    setError('');
    try {
      await api.put(`/admin/destinations/${destId}`, {
        slug: slug.trim().toLowerCase().replace(/\s+/g, '-'),
        image_url: imageUrl || null,
        status,
        translations: translations.map(t => ({
          locale: t.locale,
          name: t.name.trim() || null,
          description: t.description.trim() || null,
          meta_title: t.meta_title.trim() || null,
          meta_description: t.meta_description.trim() || null,
        })),
      });
      router.push(`/${locale}/admin/destinations`);
    } catch (e: any) {
      setError(e?.message || 'Failed to update destination');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="max-w-2xl space-y-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-64 w-full" />
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div className="max-w-2xl space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link href={`/${locale}/admin/destinations`}>
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <MapPin className="h-6 w-6 text-primary" />
              Edit: {slug}
            </h1>
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Basic Info */}
        <Card>
          <CardHeader><CardTitle>Basic Information</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Slug *</Label>
              <Input value={slug} onChange={e => setSlug(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Image URL</Label>
              <Input value={imageUrl} onChange={e => setImageUrl(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>Status</Label>
              <select
                value={status}
                onChange={e => setStatus(e.target.value)}
                className="w-full h-10 px-3 rounded-md border border-input bg-white text-sm"
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Translations */}
        <Card>
          <CardHeader><CardTitle>Translations</CardTitle></CardHeader>
          <CardContent className="space-y-6">
            {translations.map(trans => (
              <div key={trans.locale} className="p-4 border rounded-lg bg-gray-50/50">
                <h3 className="text-sm font-semibold text-primary mb-3 uppercase">{trans.locale}</h3>
                <div className="space-y-3">
                  <div className="space-y-2">
                    <Label>Name</Label>
                    <Input
                      value={trans.name}
                      onChange={e => setTrans(trans.locale, 'name', e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <textarea
                      rows={3}
                      className="w-full rounded-md border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                      value={trans.description}
                      onChange={e => setTrans(trans.locale, 'description', e.target.value)}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label>Meta Title</Label>
                      <Input
                        value={trans.meta_title}
                        onChange={e => setTrans(trans.locale, 'meta_title', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Meta Description</Label>
                      <Input
                        value={trans.meta_description}
                        onChange={e => setTrans(trans.locale, 'meta_description', e.target.value)}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <Link href={`/${locale}/admin/destinations`}>
            <Button variant="outline">Cancel</Button>
          </Link>
          <Button onClick={handleSubmit} disabled={saving}>
            {saving ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Saving...</>
            ) : (
              <><Save className="h-4 w-4 mr-2" /> Save Changes</>
            )}
          </Button>
        </div>
      </div>
    </AdminLayout>
  );
}
