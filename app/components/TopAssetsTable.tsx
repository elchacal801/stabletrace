"use client";

import { useEffect, useState } from 'react';

interface Asset {
    symbol: string;
    name: string;
    supply: number;
}

export function TopAssetsTable() {
    const [assets, setAssets] = useState<Asset[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchAssets() {
            try {
                const res = await fetch('http://127.0.0.1:8000/supply/assets?limit=10');
                if (res.ok) {
                    setAssets(await res.json());
                }
            } catch (e) {
                console.error("Failed to fetch assets", e);
            } finally {
                setLoading(false);
            }
        }
        fetchAssets();
    }, []);

    if (loading) return <div className="text-sm text-zinc-500">Loading market data...</div>;

    return (
        <div className="overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
            <div className="px-6 py-4 border-b border-zinc-200 dark:border-zinc-800">
                <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-100">Top Assets by Circulating Supply</h3>
            </div>
            <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
                <thead className="bg-zinc-50 dark:bg-zinc-950">
                    <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">Asset</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-zinc-500 uppercase tracking-wider">Supply (USD)</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                    {assets.map((asset) => (
                        <tr key={asset.symbol}>
                            <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex items-center">
                                    <div className="ml-0">
                                        <div className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{asset.name}</div>
                                        <div className="text-xs text-zinc-500">{asset.symbol}</div>
                                    </div>
                                </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-zinc-900 dark:text-zinc-100 font-mono">
                                {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(asset.supply)}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
