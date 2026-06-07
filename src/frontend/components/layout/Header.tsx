'use client';

import { useTranslations } from 'next-intl';
import { useLocale } from 'next-intl';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { useEffect, useState } from 'react';
import { Menu, X, Globe, ChevronDown, Search, Heart, User, LogOut, Phone } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/lib/stores/auth-store';

const locales = [
  { code: 'en', label: 'English' },
  { code: 'zh', label: '中文' },
  { code: 'es', label: 'Español' },
];

export function Header() {
  const t = useTranslations('nav');
  const locale = useLocale();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [langOpen, setLangOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const { user, isAuthenticated, logout, loadFromStorage } = useAuthStore();

  useEffect(() => { loadFromStorage(); }, [loadFromStorage]);

  const navLinks = [
    { href: `/${locale}`, label: t('home') },
    { href: `/${locale}/tours`, label: t('tours') },
    { href: `/${locale}/custom-tour`, label: t('customTour') || 'Custom Tour' },
    { href: `/${locale}/destinations`, label: t('destinations') },
    { href: `/${locale}/search`, label: t('search') || 'Search' },
  ];

  const switchLocalePath = (targetLocale: string) => {
    const segments = pathname.split('/');
    segments[1] = targetLocale;
    return segments.join('/');
  };

  const handleLogout = () => {
    logout();
    setUserMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link href={`/${locale}`} className="flex items-center space-x-2">
          <span className="text-2xl font-bold text-primary">Echo</span>
          <span className="text-2xl font-light">Tours</span>
        </Link>

        <nav className="hidden md:flex items-center space-x-6">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                'text-sm font-medium transition-colors hover:text-primary',
                pathname === link.href
                  ? 'text-primary'
                  : 'text-muted-foreground',
              )}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        {/* 24/7 Phone */}
        <a href="tel:+861088888888" className="hidden md:flex items-center gap-1.5 text-sm text-muted-foreground hover:text-primary mr-3">
          <Phone className="h-3.5 w-3.5" />
          <span>+86 10-8888-8888</span>
        </a>

        <div className="hidden md:flex items-center space-x-3">
          {/* Language Switcher */}
          <div className="relative">
            <button
              onClick={() => setLangOpen(!langOpen)}
              className="flex items-center space-x-1 text-sm text-muted-foreground hover:text-primary"
            >
              <Globe className="h-4 w-4" />
              <span>{locales.find((l) => l.code === locale)?.label}</span>
              <ChevronDown className="h-3 w-3" />
            </button>
            {langOpen && (
              <div className="absolute right-0 mt-2 w-36 rounded-md border bg-white shadow-lg">
                {locales.map((l) => (
                  <Link
                    key={l.code}
                    href={switchLocalePath(l.code)}
                    className={cn(
                      'block px-4 py-2 text-sm hover:bg-accent',
                      l.code === locale && 'bg-accent font-medium',
                    )}
                    onClick={() => setLangOpen(false)}
                  >
                    {l.label}
                  </Link>
                ))}
              </div>
            )}
          </div>

          {isAuthenticated ? (
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary"
              >
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-sm font-medium text-primary">
                  {user?.name?.charAt(0) || 'U'}
                </div>
                <ChevronDown className="h-3 w-3" />
              </button>

              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 rounded-md border bg-white shadow-lg">
                  <div className="px-4 py-2 border-b">
                    <p className="text-sm font-medium">{user?.name}</p>
                    <p className="text-xs text-muted-foreground">{user?.email}</p>
                  </div>
                  <Link
                    href={`/${locale}/user/orders`}
                    className="block px-4 py-2 text-sm hover:bg-accent"
                    onClick={() => setUserMenuOpen(false)}
                  >
                    {t('myOrders')}
                  </Link>
                  <Link
                    href={`/${locale}/user/wishlist`}
                    className="block px-4 py-2 text-sm hover:bg-accent"
                    onClick={() => setUserMenuOpen(false)}
                  >
                    <Heart className="h-3.5 w-3.5 inline mr-1" /> {t('wishlist') || 'Wishlist'}
                  </Link>
                  <Link
                    href={`/${locale}/user/profile`}
                    className="block px-4 py-2 text-sm hover:bg-accent"
                    onClick={() => setUserMenuOpen(false)}
                  >
                    <User className="h-3.5 w-3.5 inline mr-1" /> {t('myAccount')}
                  </Link>
                  {user?.is_admin && (
                    <Link
                      href={`/${locale}/admin`}
                      className="block px-4 py-2 text-sm font-medium text-primary hover:bg-accent"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      📊 {t('admin')}
                    </Link>
                  )}
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-accent"
                  >
                    <LogOut className="h-3.5 w-3.5 inline mr-1" /> {t('signOut')}
                  </button>
                </div>
              )}
            </div>
          ) : (
            <>
              <Link href={`/${locale}/auth`}>
                <Button variant="ghost" size="sm">{t('signIn')}</Button>
              </Link>
              <Link href={`/${locale}/auth?mode=signup`}>
                <Button size="sm">{t('signUp')}</Button>
              </Link>
            </>
          )}
        </div>

        <button className="md:hidden" onClick={() => setMobileOpen(!mobileOpen)}>
          {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {mobileOpen && (
        <div className="md:hidden border-t p-4 space-y-4">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="block text-sm font-medium"
              onClick={() => setMobileOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <div className="pt-4 border-t space-y-2">
            {locales.map((l) => (
              <Link
                key={l.code}
                href={switchLocalePath(l.code)}
                className="block text-sm"
                onClick={() => setMobileOpen(false)}
              >
                {l.label}
              </Link>
            ))}
          </div>
          <div className="pt-4 border-t space-y-2">
            {isAuthenticated ? (
              <>
                <Link href={`/${locale}/user/orders`} className="block"><Button variant="outline" className="w-full">{t('myOrders')}</Button></Link>
                <Link href={`/${locale}/user/profile`} className="block"><Button variant="outline" className="w-full">{t('myAccount')}</Button></Link>
                {user?.is_admin && (
                  <Link href={`/${locale}/admin`} className="block"><Button variant="default" className="w-full">📊 {t('admin')}</Button></Link>
                )}
                <button onClick={handleLogout} className="w-full"><Button variant="ghost" className="w-full text-red-600">{t('signOut')}</Button></button>
              </>
            ) : (
              <>
                <Link href={`/${locale}/auth`} className="block"><Button variant="outline" className="w-full">{t('signIn')}</Button></Link>
                <Link href={`/${locale}/auth?mode=signup`} className="block"><Button className="w-full">{t('signUp')}</Button></Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
