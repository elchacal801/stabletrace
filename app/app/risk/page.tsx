import { RiskExplorer } from '../../components/RiskExplorer';

export const dynamic = 'force-dynamic';

async function getSanctionsStats() {
    try {
        const res = await fetch('http://127.0.0.1:8000/risk/stats', { cache: 'no-store' });
        if (!res.ok) return { total_entities: 0, total_addresses: 0 };
        return res.json();
    } catch (e) {
        return { total_entities: 0, total_addresses: 0 };
    }
}

export default async function RiskPage() {
    const stats = await getSanctionsStats();

    return (
        <main className="min-h-screen bg-zinc-50 dark:bg-black p-8">
            <div className="max-w-7xl mx-auto space-y-8">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">Risk Overlay</h1>
                    <p className="text-zinc-500 dark:text-zinc-400 mt-2">
                        Sanctions exposure and crypto-crime signals.
                    </p>
                </div>

                <div className="grid grid-cols-1 gap-6">
                    <div className="p-6 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg shadow-sm">
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-full">
                                <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                            </div>
                            <div>
                                <div className="text-sm text-zinc-500 dark:text-zinc-400 font-medium">Active Sanctioned Entities with Crypto Addresses</div>
                                <div className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">{stats.total_entities?.toLocaleString() || 0}</div>
                            </div>
                        </div>
                        <div className="mt-4 pt-4 border-t border-zinc-100 dark:border-zinc-800 text-sm text-zinc-500">
                            <p>
                                <strong>Data Source:</strong> U.S. Treasury OFAC SDN List (Specially Designated Nationals).
                                This dashboard filters the SDN list for entities that have associated "Digital Currency Addresses".
                            </p>
                            <p className="mt-2 text-xs text-zinc-400">
                                *Disclaimer: This is an investigative aid. Always verify directly with official OFAC sources before taking compliance actions.
                            </p>
                        </div>
                    </div>
                </div>

                <div className="space-y-4">
                    <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">Latest Sanctioned Entities (Crypto-Linked)</h2>
                    <RiskExplorer />
                </div>
            </div>
        </main>
    );
}
