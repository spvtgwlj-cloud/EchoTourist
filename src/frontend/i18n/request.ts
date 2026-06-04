import { getRequestConfig } from 'next-intl/server';
import { notFound } from 'next/navigation';

const locales = ['en', 'zh', 'es'];

export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;
  if (!locale || !locales.includes(locale)) {
    locale = 'en';
  }

  try {
    return {
      locale,
      messages: (await import(`../messages/${locale}/common.json`)).default,
    };
  } catch {
    notFound();
  }
});

export { locales };
