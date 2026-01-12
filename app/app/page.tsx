import { SupplyChart } from '../components/SupplyChart';
import { TopAssetsTable } from '../components/TopAssetsTable';

async function getSupplyData() {
  // In a real Next.js app, we should use environmental variables for the API URL.
  // For local dev, localhost:8000 is fine.
  try {
    const res = await fetch('http://127.0.0.1:8000/supply/global?days=90', {
      cache: 'no-store'
    });

    if (!res.ok) {
      console.error("Failed to fetch supply data", res.status, res.statusText);
      return [];
    }

    return res.json();
  } catch (e) {
    console.error("Error fetching supply data:", e);
    return [];
  }
}

export default async function Home() {
  const supplyData = await getSupplyData();

  return (
    <main className="min-h-screen bg-zinc-50 dark:bg-black p-8">
      <div className="max-w-7xl mx-auto space-y-8">

        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">StableTrace</h1>
            <p className="text-zinc-500 dark:text-zinc-400 mt-2">
              Stablecoin Telemetry & Risk Observatory
            </p>
          </div>
          <div className="flex gap-2">
            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">System Operational</span>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Placeholders for metrics */}
          <div className="p-4 bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-800 shadow-sm">
            <div className="text-sm text-zinc-500">Total Supply</div>
            <div className="text-2xl font-semibold mt-1">
              {supplyData.length > 0
                ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', notation: 'compact' }).format(supplyData[0].total_supply)
                : '---'}
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            <SupplyChart data={supplyData} />
            <TopAssetsTable />
          </div>
          <div className="lg:col-span-1 space-y-4">
            {/* Sidebar / Info */}
            <div className="p-4 bg-white dark:bg-zinc-900 rounded-lg border border-zinc-200 dark:border-zinc-800 shadow-sm h-full">
              <h3 className="font-semibold mb-4 text-zinc-900 dark:text-zinc-100">About this data</h3>
              <p className="text-sm text-zinc-500 mb-4">
                Data sourced from <strong>DefiLlama</strong> public API.
                Represents total circulating supply of pegged assets.
              </p>
              <div className="text-xs text-zinc-400">
                Last Updated: {new Date().toLocaleDateString()}
              </div>
            </div>
          </div>
        </div>

      </div>
    </main>
  );
}
