'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useLocale } from 'next-intl';
import { useAuthStore } from '@/lib/stores/auth-store';
import { AdminLayout } from '@/components/admin/AdminLayout';
import TourCreateForm from '@/components/admin/TourCreateForm';
import { Loader2 } from 'lucide-react';

export default function CreateTourPage() {
  const locale = useLocale();
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (!isAuthenticated || !user?.is_admin) {
      router.push(`/${locale}/auth`);
    } else {
      setChecking(false);
    }
  }, [isAuthenticated, user, locale, router]);

  if (checking) {
    return (
      <AdminLayout>
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Create Tour</h1>
        <p className="text-sm text-muted-foreground">Add a new tour product with translations, images, and pricing</p>
      </div>
      <TourCreateForm />
    </AdminLayout>
  );
}
