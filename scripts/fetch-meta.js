/**
 * fetch-meta.js — GitHub Actions script
 * Fetches Ensifera COP campaign data from Meta Graph API and writes data/meta.json
 *
 * Env vars required:
 *   FACEBOOK_ACCESS_TOKEN  — long-lived system user token from Meta Business Settings
 *   AD_ACCOUNT_ID          — defaults to 1580457616921076 (Ensifera COP)
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

const TOKEN = process.env.FACEBOOK_ACCESS_TOKEN;
const ACCOUNT = process.env.AD_ACCOUNT_ID || '1580457616921076';
const API_VER = 'v21.0';

if (!TOKEN) {
  console.error('ERROR: FACEBOOK_ACCESS_TOKEN env var is not set.');
  process.exit(1);
}

function get(url) {
  return new Promise((resolve, reject) => {
    https.get(url, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => {
        try { resolve(JSON.parse(d)); } catch (e) { reject(e); }
      });
    }).on('error', reject);
  });
}

// Strip formatting from Meta spend strings like "$ 324.658 COP" → 324658
function parseCOP(str) {
  if (!str || str === 'Not available') return 0;
  return parseInt((str + '').replace(/[^0-9]/g, ''), 10) || 0;
}

function parseCount(str) {
  if (!str || str === 'Not available') return 0;
  return parseInt((str + '').replace(/[^0-9]/g, ''), 10) || 0;
}

function parseResults(obj) {
  if (!obj || !obj.values) return 0;
  return parseInt((obj.values[0] || {}).value || '0', 10) || 0;
}

function resultType(obj) {
  const ind = (obj && obj.indicator) || '';
  if (ind.includes('messaging_conversation_started')) return 'Conv. WPP';
  if (ind.includes('profile_visit')) return 'Visitas perfil';
  if (ind.includes('purchase')) return 'Compra web';
  if (ind.includes('lead')) return 'Leads';
  return 'Resultados';
}

function monthKey(preset) {
  const now = new Date();
  if (preset === 'this_month') {
    return now.toISOString().slice(0, 7);
  }
  const d = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  return d.toISOString().slice(0, 7);
}

function monthLabel(preset) {
  const months = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
  const now = new Date();
  if (preset === 'this_month') {
    return `${months[now.getMonth()]} ${now.getFullYear()}`;
  }
  const d = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  return `${months[d.getMonth()]} ${d.getFullYear()}`;
}

async function fetchMonth(preset) {
  const fields = [
    'name', 'status', 'amount_spent', 'impressions', 'clicks',
    'reach', 'results', 'cost_per_result', 'ctr',
  ].join(',');
  const url = `https://graph.facebook.com/${API_VER}/act_${ACCOUNT}/campaigns`
    + `?fields=${encodeURIComponent(fields)}`
    + `&date_preset=${preset}`
    + `&access_token=${TOKEN}`;
  const res = await get(url);
  if (res.error) throw new Error(JSON.stringify(res.error));
  return (res.data || [])
    .map(c => ({
      name: c.name,
      status: c.status,
      spend: parseCOP(c.amount_spent),
      impressions: parseCount(c.impressions),
      clicks: parseCount(c.clicks),
      reach: parseCount(c.reach),
      results: parseResults(c.results),
      resultType: resultType(c.results),
      costPerResult: parseCOP((c.cost_per_result || {}).value),
      ctr: parseFloat((c.ctr || '0').replace(',', '.')) || 0,
    }))
    .filter(c => c.spend > 0);
}

async function main() {
  console.log(`Fetching Meta Ads data for account ${ACCOUNT}…`);
  const [thisCamps, lastCamps] = await Promise.all([
    fetchMonth('this_month'),
    fetchMonth('last_month'),
  ]);

  const monthly = [
    { month: monthKey('this_month'), label: monthLabel('this_month'), campaigns: thisCamps },
    { month: monthKey('last_month'), label: monthLabel('last_month'), campaigns: lastCamps },
  ].filter(m => m.campaigns.length > 0);

  const today = new Date().toISOString().slice(0, 10);
  const out = { monthly, updatedAt: today };

  const outPath = path.join(__dirname, '..', 'data', 'meta.json');
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify(out, null, 2), 'utf8');

  const totalSpend = monthly.flatMap(m => m.campaigns).reduce((s, c) => s + c.spend, 0);
  console.log(`✓ data/meta.json updated — ${monthly.length} months, total spend ${totalSpend.toLocaleString()} COP, updatedAt ${today}`);
}

main().catch(err => { console.error(err); process.exit(1); });
