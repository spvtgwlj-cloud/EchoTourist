'use client';

import { useTranslations } from 'next-intl';
import { useLocale } from 'next-intl';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { api } from '@/lib/api';
import { AdminLayout } from '@/components/admin/AdminLayout';
import { Plus, Edit, Trash2, Search, Globe, MapPin } from 'lucide-react';

interface DestinationItem {
  id: string;
  slug: string;
  image_url: string;
  status: string;
  translation_count: number;
  created_at: string;
}

export default function AdminDestinationsPage() {
  const t = useTranslations('admin');
  const locale = useLocale();
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [destinations, setDestinations] = useState<DestinationItem[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await api.get<{ destinations: DestinationItem[]; total: number }>(
        `/admin/destinations?page_size=200`
      );
      setDestinations(res.destinations || []);
      setTotal(res.total || 0);
    } catch (e: any) {
      console.error('Failed to load destinations', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleDelete = async (id: string, slug: string) => {
    if (!confirm(`Delete destination "${slug}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/admin/destinations/${id}`);
      loadData();
    } catch (e: any) {
      alert(e?.message || 'Delete failed');
    }
  };

  const filtered = destinations.filter(d =>
    !search || d.slug.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <MapPin className="h-6 w-6 text-primary" />
              {t('destinations') || 'Destinations'}
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              {t('total')}: {total} destinations
            </p>
          </div>
          <Link href={`/${locale}/admin/destinations/create`}>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              {t('createNew') || 'Create Destination'}
            </Button>
          </Link>
        </div>

        {/* Search */}
        <div className="flex gap-2 max-w-sm">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by slug..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Loading */}
        {loading && (
          <div className="space-y-3">
            {[1,2,3].map(i => <Skeleton key={i} className="h-16 w-full" />)}
          </div>
        )}

        {/* Empty state */}
        {!loading && filtered.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <Globe className="h-12 w-12 mx-auto text-muted-foreground/40 mb-4" />
              <p className="text-muted-foreground">
                {search ? 'No destinations match your search.' : 'No destinations yet. Create your first destination!'}
              </p>
            </CardContent>
          </Card>
        )}

        {/* List */}
        {!loading && filtered.length > 0 && (
          <div className="space-y-2">
            {filtered.map(d => (
              <div key={d.id} className="flex items-center justify-between p-4 rounded-lg border bg-white hover:bg-gray-50 transition-colors">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                    <MapPin className="h-5 w-5 text-primary" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium truncate">{d.slug}</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs ${
                        d.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                      }`}>
                        {d.status}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {d.translation_count} translation(s)
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Link href={`/${locale}/admin/destinations/${d.id}/edit`}>
                    <Button variant="outline" size="sm">
                      <Edit className="h-4 w-4" />
                    </Button>
                  </Link>
                  <Button variant="outline" size="sm" className="text-red-500" onClick={() => handleDelete(d.id, d.slug)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AdminLayout>
  );
}
