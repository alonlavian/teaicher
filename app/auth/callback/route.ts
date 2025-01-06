import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET(request: Request) {
  try {
    console.log('[Auth Callback] Processing request');
    const requestUrl = new URL(request.url);
    console.log('[Auth Callback] URL:', requestUrl.toString());
    
    // Log all query parameters for debugging
    console.log('[Auth Callback] Query parameters:', 
      Object.fromEntries(requestUrl.searchParams.entries())
    );

    const code = requestUrl.searchParams.get('code');
    const error = requestUrl.searchParams.get('error');
    const error_description = requestUrl.searchParams.get('error_description');

    if (error) {
      console.error('[Auth Callback] Auth error:', {
        error,
        description: error_description
      });
      return NextResponse.redirect(
        new URL(`/?error=${encodeURIComponent(error_description || error)}`, requestUrl.origin)
      );
    }

    if (code) {
      console.log('[Auth Callback] Code found, exchanging for session');
      const cookieStore = cookies();
      
      const supabase = createServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
          cookies: {
            get(name: string) {
              return cookieStore.get(name)?.value;
            },
            set(name: string, value: string, options: CookieOptions) {
              cookieStore.set({ name, value, ...options });
            },
            remove(name: string, options: CookieOptions) {
              cookieStore.delete({ name, ...options });
            },
          },
        }
      );

      const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);
      
      if (exchangeError) {
        console.error('[Auth Callback] Session exchange error:', exchangeError);
        throw exchangeError;
      }
      
      console.log('[Auth Callback] Session exchange successful');
    } else {
      console.log('[Auth Callback] No code found in URL');
    }

    // URL to redirect to after sign in process completes
    console.log('[Auth Callback] Redirecting to home page');
    return NextResponse.redirect(new URL('/', requestUrl.origin));
  } catch (error) {
    console.error('[Auth Callback] Unexpected error:', error);
    return NextResponse.redirect(
      new URL('/?error=An unexpected error occurred', request.url)
    );
  }
}
