// Cloudflare edge router for Shadowrocket Pro assets/rules.
// Keeps the existing subscription Worker untouched and adds:
// - /shadowrocket-pro.conf: origin-aware config (self-hosted rule URLs)
// - /rules/china-core.list: CF-cached proxy of the curated domestic core list
// - /rules/chinamax-domain.list: CF-cached proxy of ChinaMax domain-only rules

import app from './worker.js';

const RULES = {
  '/rules/china-core.list':
    'https://raw.githubusercontent.com/menghuaban520/cloudflaresub/main/configs/rules/china-core.list',
  '/rules/chinamax-domain.list':
    'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/ChinaMax/ChinaMax_Domain.list',
};

function plain(body, status = 200, headers = {}) {
  return new Response(body, {
    status,
    headers: {
      'content-type': 'text/plain; charset=utf-8',
      ...headers,
    },
  });
}

async function proxyRule(request, ctx, upstreamUrl) {
  const cache = caches.default;
  const cacheKey = new Request(request.url, { method: 'GET' });
  const cached = await cache.match(cacheKey);
  if (cached) return cached;

  const upstream = await fetch(upstreamUrl, {
    headers: {
      'user-agent': 'Shadowrocket-Pro-CF-Rule-Proxy/1.0',
      accept: 'text/plain,*/*;q=0.8',
    },
    cf: {
      cacheEverything: true,
      cacheTtl: 21600,
    },
  });

  if (!upstream.ok) {
    return plain(`rule upstream error: ${upstream.status}`, 502, {
      'cache-control': 'no-store',
    });
  }

  const headers = new Headers(upstream.headers);
  headers.set('content-type', 'text/plain; charset=utf-8');
  headers.set('cache-control', 'public, max-age=21600, stale-while-revalidate=86400');
  headers.delete('content-security-policy');
  headers.delete('content-encoding');

  const response = new Response(upstream.body, {
    status: 200,
    headers,
  });

  ctx.waitUntil(cache.put(cacheKey, response.clone()));
  return response;
}

async function renderShadowrocketConfig(request, env) {
  const url = new URL(request.url);
  const origin = url.origin;

  // Read the checked-in template directly from Workers Assets.
  const assetUrl = new URL('/shadowrocket-pro.conf', url);
  const assetResponse = await env.ASSETS.fetch(new Request(assetUrl, request));
  if (!assetResponse.ok) {
    return plain('shadowrocket config template not found', 500, {
      'cache-control': 'no-store',
    });
  }

  let config = await assetResponse.text();

  // High-frequency domestic services hit the small core list first.
  // Long-tail domestic domains then hit ChinaMax. Both rule files are fetched
  // from THIS Cloudflare deployment, so the phone never has to reach GitHub/jsDelivr.
  const oldChinaMax =
    'DOMAIN-SET,https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Shadowrocket/ChinaMax/ChinaMax_Domain.list,DIRECT,update-interval=86400';
  const cfDomesticRules = [
    `RULE-SET,${origin}/rules/china-core.list,DIRECT,update-interval=21600`,
    `DOMAIN-SET,${origin}/rules/chinamax-domain.list,DIRECT,update-interval=21600`,
  ].join('\n');

  if (config.includes(oldChinaMax)) {
    config = config.replace(oldChinaMax, cfDomesticRules);
  } else if (!config.includes('/rules/chinamax-domain.list')) {
    config = config.replace(
      '# 中国 IP 直连；no-resolve 防止未知国外域名为了 GEOIP 判断而先做本地 DNS。',
      `${cfDomesticRules}\n\n# 中国 IP 直连；no-resolve 防止未知国外域名为了 GEOIP 判断而先做本地 DNS。`,
    );
  }

  // Make the active origin obvious when inspecting the config.
  config = config.replace(
    '# Shadowrocket Pro — 梦花瓣版（Cloudflare 托管）',
    `# Shadowrocket Pro — 梦花瓣版（Cloudflare 托管）\n# Active origin: ${origin}`,
  );

  return plain(config, 200, {
    'cache-control': 'no-cache, no-store, must-revalidate',
  });
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (request.method === 'GET' && url.pathname === '/shadowrocket-pro.conf') {
      return renderShadowrocketConfig(request, env);
    }

    if (request.method === 'GET' && RULES[url.pathname]) {
      return proxyRule(request, ctx, RULES[url.pathname]);
    }

    return app.fetch(request, env, ctx);
  },
};
