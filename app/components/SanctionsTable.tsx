"use client";

import { format } from 'date-fns';

interface SanctionedEntity {
    entity_id: string;
    name: string;
    program: string;
    authority: string;
    opencorporates_search_url?: string;
    source_url?: string;
    addresses: Array<{
        address: string;
        chain: string;
        date: string;
    }>;
}

export function SanctionsTable({ data }: { data: SanctionedEntity[] }) {
    if (!data || data.length === 0) {
        return <div className="p-4 text-center text-zinc-500">No recent sanctions data found.</div>;
    }

    return (
        <div className="overflow-hidden rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
            <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
                <thead className="bg-zinc-50 dark:bg-zinc-950">
                    <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">Entity</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">Authority</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">Source</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">Date Listed</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-zinc-500 uppercase tracking-wider">Addresses</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                    {data.map((entity) => (
                        <tr key={entity.entity_id}>
                            <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{entity.name}</div>
                                <div className="text-xs text-zinc-500">{entity.program}</div>
                                {entity.opencorporates_search_url && (
                                    <a
                                        href={entity.opencorporates_search_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center gap-1 mt-1 text-xs text-blue-600 dark:text-blue-400 hover:underline"
                                    >
                                        <span>Check OpenCorporates</span>
                                    </a>
                                )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm text-zinc-900 dark:text-zinc-300">{entity.authority}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                                {entity.source_url ? (
                                    <a
                                        href={entity.source_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                                    >
                                        View Source
                                    </a>
                                ) : (
                                    <span className="text-xs text-zinc-400">N/A</span>
                                )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-xs text-zinc-500">
                                    {entity.addresses[0]?.date ? format(new Date(entity.addresses[0].date), 'MMM d, yyyy') : 'Unknown'}
                                </div>
                            </td>
                            <td className="px-6 py-4">
                                <div className="space-y-1">
                                    {entity.addresses.slice(0, 3).map((addr, idx) => (
                                        <div key={idx} className="flex items-center gap-2 text-xs">
                                            <span className="font-mono bg-zinc-100 dark:bg-zinc-800 px-1 py-0.5 rounded text-zinc-600 dark:text-zinc-400">
                                                {addr.chain}
                                            </span>
                                            <span className="font-mono text-zinc-500" title={addr.address}>
                                                {addr.address.substring(0, 10)}...{addr.address.substring(addr.address.length - 4)}
                                            </span>
                                        </div>
                                    ))}
                                    {entity.addresses.length > 3 && (
                                        <div className="text-xs text-zinc-400">+{entity.addresses.length - 3} more</div>
                                    )}
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
