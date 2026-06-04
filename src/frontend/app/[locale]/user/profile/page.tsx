'use client';

import { useTranslations } from 'next-intl';
import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/stores/auth-store';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { User, Mail, Globe, Save, AlertCircle, Loader2 } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

interface UserProfile {
  id: string; email: string; name: string; avatar_url?: string;
  locale: string; is_admin: boolean; created_at: string;
  review_count: number; order_count: number;
}

export default function ProfilePage() {
  const t = useTranslations('user');
  const ct = useTranslations('common');
  const { token, isAuthenticated } = useAuthStore();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState('');
  const [locale, setLocale] = useState('en');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (!isAuthenticated) return;
    api.get<UserProfile>('/users/me/profile')
      .then((p) => { setProfile(p); setName(p.name); setLocale(p.locale); })
      .catch(() => setError('Failed to load profile'))
      .finally(() => setLoading(false));
  }, [isAuthenticated]);

  const handleSave = async () => {
    setSaving(true); setError(''); setSuccess('');
    try {
      const updated = await api.patch<UserProfile>('/users/me/profile', { name, locale });
      setProfile(updated);
      setSuccess(ct('saved') || 'Saved');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally { setSaving(false); }
  };

  if (loading) return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <Skeleton className="h-8 w-48 mb-8" />
      <div className="border rounded-lg p-6 space-y-4">
        <Skeleton className="h-5 w-32" />
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="space-y-1">
              <Skeleton className="h-3 w-16" />
              <Skeleton className="h-10 w-full" />
            </div>
          ))}
        </div>
        <Skeleton className="h-10 w-32" />
      </div>
    </div>
  );
  if (!profile) return <div className="container mx-auto px-4 py-8 text-center text-muted-foreground">{t('noProfile')}</div>;

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <h1 className="text-3xl font-bold mb-8">{t('myProfile')}</h1>

      {error && <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-600"><AlertCircle className="h-4 w-4" /> {error}</div>}
      {success && <div className="mb-4 rounded-lg bg-green-50 border border-green-200 p-3 text-sm text-green-600">{success}</div>}

      <Card className="mb-6">
        <CardHeader><CardTitle>{t('profileInfo')}</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Mail className="h-4 w-4" /> {profile.email}
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              <User className="h-4 w-4 inline mr-1" /> {t('name')}
            </label>
            <input
              type="text" value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              <Globe className="h-4 w-4 inline mr-1" /> {t('language')}
            </label>
            <select
              value={locale}
              onChange={(e) => setLocale(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="en">English</option>
              <option value="zh">中文</option>
              <option value="es">Español</option>
            </select>
          </div>

          <Button onClick={handleSave} disabled={saving}>
            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
            {ct('save')}
          </Button>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-4">
        <Card><CardContent className="p-6 text-center">
          <p className="text-2xl font-bold">{profile.review_count}</p>
          <p className="text-sm text-muted-foreground">{t('reviews')}</p>
        </CardContent></Card>
        <Card><CardContent className="p-6 text-center">
          <p className="text-2xl font-bold">{profile.order_count}</p>
          <p className="text-sm text-muted-foreground">{t('orders')}</p>
        </CardContent></Card>
      </div>
    </div>
  );
}
