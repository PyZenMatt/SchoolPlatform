#!/usr/bin/env node

const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');
const fs = require('fs');
const path = require('path');

// Configurazione del test
const config = {
  baseUrl: 'http://localhost:4000',
  pages: [
    { name: 'Homepage', url: '/' },
    { name: 'Features EN', url: '/eng/features/' },
    { name: 'Features IT', url: '/ita/features/' },
    { name: 'Technology EN', url: '/eng/technology/' },
    { name: 'Technology IT', url: '/ita/technology/' },
    { name: 'Invest EN', url: '/eng/invest/' },
    { name: 'Invest IT', url: '/ita/invest/' },
    { name: 'Roadmap EN', url: '/eng/roadmap/' },
    { name: 'Roadmap IT', url: '/ita/roadmap/' },
    { name: 'Tokenomics EN', url: '/eng/tokenomics/' },
    { name: 'Tokenomics IT', url: '/ita/tokenomics/' }
  ],
  options: {
    onlyCategories: ['performance'],
    output: 'json',
    logLevel: 'info',
    disableDeviceEmulation: false,
    chromeFlags: ['--disable-device-emulation']
  }
};

// Funzione per formattare i risultati
function formatResults(results, pageName) {
  const metrics = results.lhr.audits;
  const score = Math.round(results.lhr.categories.performance.score * 100);
  
  return {
    page: pageName,
    score: score,
    fcp: Math.round(metrics['first-contentful-paint'].numericValue),
    lcp: Math.round(metrics['largest-contentful-paint'].numericValue),
    cls: Math.round(metrics['cumulative-layout-shift'].numericValue * 1000) / 1000,
    tti: Math.round(metrics['interactive'].numericValue),
    si: Math.round(metrics['speed-index'].numericValue),
    tbt: Math.round(metrics['total-blocking-time'].numericValue)
  };
}

// Funzione per stampare risultati in tabella
function printResults(allResults) {
  console.log('\n🚀 LIGHTHOUSE PERFORMANCE RESULTS\n');
  console.log('┌─────────────────┬───────┬─────────┬─────────┬───────┬─────────┬─────────┬─────────┐');
  console.log('│ Page            │ Score │ FCP(ms) │ LCP(ms) │  CLS  │ TTI(ms) │  SI(ms) │ TBT(ms) │');
  console.log('├─────────────────┼───────┼─────────┼─────────┼───────┼─────────┼─────────┼─────────┤');
  
  allResults.forEach(result => {
    const scoreColor = result.score >= 90 ? '🟢' : result.score >= 70 ? '🟡' : '🔴';
    console.log(`│ ${result.page.padEnd(15)} │ ${scoreColor}${String(result.score).padStart(3)} │ ${String(result.fcp).padStart(7)} │ ${String(result.lcp).padStart(7)} │ ${String(result.cls).padStart(5)} │ ${String(result.tti).padStart(7)} │ ${String(result.si).padStart(7)} │ ${String(result.tbt).padStart(7)} │`);
  });
  
  console.log('└─────────────────┴───────┴─────────┴─────────┴───────┴─────────┴─────────┴─────────┘');
  
  // Calcola medie
  const avgScore = Math.round(allResults.reduce((sum, r) => sum + r.score, 0) / allResults.length);
  const avgLCP = Math.round(allResults.reduce((sum, r) => sum + r.lcp, 0) / allResults.length);
  const avgCLS = Math.round(allResults.reduce((sum, r) => sum + r.cls, 0) / allResults.length * 1000) / 1000;
  
  console.log(`\n📊 SUMMARY:`);
  console.log(`   Average Score: ${avgScore}/100`);
  console.log(`   Average LCP: ${avgLCP}ms`);
  console.log(`   Average CLS: ${avgCLS}`);
  
  // Raccomandazioni
  console.log(`\n💡 RECOMMENDATIONS:`);
  if (avgScore < 90) console.log('   🔴 Performance below 90 - optimization needed');
  if (avgLCP > 2500) console.log('   🔴 LCP above 2.5s - optimize largest content');
  if (avgCLS > 0.1) console.log('   🔴 CLS above 0.1 - fix layout shifts');
  
  console.log(`\n🎯 TARGETS:`);
  console.log(`   Score: ≥90, LCP: ≤2500ms, CLS: ≤0.1`);
}

// Funzione principale
async function runSpeedTest() {
  console.log('🔄 Starting speed test...');
  console.log(`📍 Testing server: ${config.baseUrl}`);
  
  const chrome = await chromeLauncher.launch({chromeFlags: ['--headless']});
  config.options.port = chrome.port;
  
  const allResults = [];
  
  for (const page of config.pages) {
    const url = `${config.baseUrl}${page.url}`;
    console.log(`🧪 Testing: ${page.name} (${url})`);
    
    try {
      const results = await lighthouse(url, config.options);
      const formatted = formatResults(results, page.name);
      allResults.push(formatted);
    } catch (error) {
      console.log(`❌ Error testing ${page.name}: ${error.message}`);
    }
  }
  
  await chrome.kill();
  
  printResults(allResults);
  
  // Salva risultati dettagliati
  const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
  const reportPath = path.join(__dirname, `../reports/speed-test-${timestamp}.json`);
  
  if (!fs.existsSync(path.dirname(reportPath))) {
    fs.mkdirSync(path.dirname(reportPath), { recursive: true });
  }
  
  fs.writeFileSync(reportPath, JSON.stringify(allResults, null, 2));
  console.log(`\n💾 Detailed results saved to: ${reportPath}`);
}

// Verifica che il server Jekyll sia in esecuzione
async function checkServer() {
  try {
    const response = await fetch(config.baseUrl);
    if (!response.ok) throw new Error('Server not responding');
    return true;
  } catch (error) {
    console.log('❌ Jekyll server not running on http://localhost:4000');
    console.log('💡 Start it with: bundle exec jekyll serve');
    return false;
  }
}

// Esegui il test
(async () => {
  if (await checkServer()) {
    await runSpeedTest();
  }
})().catch(console.error);
