'use client';

import { useTranslations } from 'next-intl';
import { useLocale } from 'next-intl';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { LayoutDashboard, Map, ShoppingCart, Users, Star, Landmark, Wrench, ClipboardList, MapPin, MessageCircle, LogOut } from 'lucide-react';

interface AdminLayoutProps {
  children: React.ReactNode;
}

const navItems = [
  { href: '/admin', label: 'dashboard', icon: LayoutDashboard },
  { href: '/admin/tours', label: 'tours', icon: Map },
  { href: '/admin/destinations', label: 'destinations', icon: MapPin },
  { href: '/admin/attractions', label: 'attractions', icon: Landmark },
  { href: '/admin/orders', label: 'orders', icon: ShoppingCart },
  { href: '/admin/reviews', label: 'reviews', icon: Star },
  { href: '/admin/enquiries', label: 'enquiries', icon: MessageCircle },
  { href: '/admin/base-services', label: 'baseServices', icon: Wrench },
  { href: '/admin/custom-tours', label: 'customTours', icon: ClipboardList },
];

export function AdminLayout({ children }: AdminLayoutProps) {
  const locale = useLocale();
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 min-h-screen border-r bg-white p-4 hidden md:block">
          <Link href={`/${locale}/admin`} className="flex items-center gap-2 mb-8">
            <LayoutDashboard className="h-5 w-5 text-primary" />
            <span className="font-bold text-lg">Admin</span>
          </Link>

          <nav className="space-y-1">
            {navItems.map((item) => {
              const href = `/${locale}${item.href}`;
              const Icon = item.icon;
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    'flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors',
                    pathname === href
                      ? 'bg-primary/10 text-primary font-medium'
                      : 'text-muted-foreground hover:bg-gray-100',
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
