"use client";

import { useState, useEffect } from 'react';
import { SanctionsTable } from './SanctionsTable';

interface SanctionedEntity {
    entity_id: string;
    name: string;
    program: string;
    authority: string;
    opencorporates_search_url?: string;
    addresses: Array<{
        address: string;
        chain: string;
        date: string;
    }>;
}

export function RiskExplorer() {
    const [data, setData] = useState<SanctionedEntity[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    // We'll use a debounce for search in a real app, but for now simple state is fine or we search on enter/button.
    // Let's search on input change with a small effect delay/debounce manually or just direct for simplicity if user types slow.
    // Actually, distinct search button or just "Enter" is safer to avoid spamming API.
    // Let's do instant search with debounce logic? Or just simple effect.

    const [debouncedSearch, setDebouncedSearch] = useState("");
    const [page, setPage] = useState(0);
    const LIMIT = 50;

    const [total, setTotal] = useState(0);
    const [authority, setAuthority] = useState("");
    const [authorities, setAuthorities] = useState<string[]>([]);

    useEffect(() => {
        // Fetch available authorities
        fetch('http://127.0.0.1:8000/risk/filters')
            .then(res => res.json())
            .then(data => setAuthorities(data.authorities || []))
            .catch(err => console.error("Failed to fetch filters", err));
    }, []);

    // Debounce search input
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSearch(search);
            setPage(0); // Reset to page 0 on new search
        }, 500);
        return () => clearTimeout(timer);
    }, [search]);

    useEffect(() => {
        async function fetchData() {
            setLoading(true);
            try {
                const offset = page * LIMIT;
                const params = new URLSearchParams({
                    limit: LIMIT.toString(),
                    offset: offset.toString()
                });
                if (debouncedSearch) {
                    params.append("search", debouncedSearch);
                }
                if (authority) {
                    params.append("authority", authority);
                }

                const res = await fetch(`http://127.0.0.1:8000/risk/sanctions/latest?${params.toString()}`);
                if (res.ok) {
                    const json = await res.json();
                    // New API returns { items: [], total: number }
                    // OR if old API, it returns []. We should handle both temporarily or assume new.
                    // Let's assume new since we just updated providing a robust fix.
                    if (Array.isArray(json)) {
                        // Fallback/Legacy
                        setData(json);
                        setTotal(json.length); // inexact but safe
                    } else {
                        setData(json.items);
                        setTotal(json.total);
                    }
                }
            } catch (e) {
                console.error("Failed to fetch risk data", e);
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, [debouncedSearch, page, authority]);

    const totalPages = Math.ceil(total / LIMIT);

    return (
        <div className="space-y-6">
            {/* Controls */}
            <div className="flex flex-col sm:flex-row gap-4 justify-between items-center bg-white dark:bg-zinc-900 p-4 rounded-lg border border-zinc-200 dark:border-zinc-800 shadow-sm">
                <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto flex-1">
                    <div className="relative w-full sm:w-96">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <svg className="h-5 w-5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                        </div>
                        <input
                            type="text"
                            placeholder="Search entities or addresses..."
                            className="block w-full pl-10 pr-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md leading-5 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>

                    <select
                        className="block w-full sm:w-48 pl-3 pr-10 py-2 border border-zinc-300 dark:border-zinc-700 rounded-md leading-5 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        value={authority}
                        onChange={(e) => {
                            setAuthority(e.target.value);
                            setPage(0);
                        }}
                    >
                        <option value="">All Authorities</option>
                        {authorities.map(auth => (
                            <option key={auth} value={auth}>{auth}</option>
                        ))}
                    </select>
                </div>

                <div className="flex items-center gap-4">
                    <span className="text-sm text-zinc-500">
                        {total > 0 ? (
                            <>Page <span className="font-medium text-zinc-900 dark:text-zinc-100">{page + 1}</span> of <span className="font-medium text-zinc-900 dark:text-zinc-100">{totalPages || 1}</span></>
                        ) : (
                            "No results"
                        )}
                    </span>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setPage(p => Math.max(0, p - 1))}
                            disabled={page === 0 || loading}
                            className="px-3 py-1.5 text-sm font-medium text-zinc-700 dark:text-zinc-300 bg-white dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 rounded-md hover:bg-zinc-50 dark:hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Previous
                        </button>
                        <button
                            onClick={() => setPage(p => p + 1)}
                            disabled={loading || page >= totalPages - 1}
                            className="px-3 py-1.5 text-sm font-medium text-zinc-700 dark:text-zinc-300 bg-white dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 rounded-md hover:bg-zinc-50 dark:hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Next
                        </button>
                    </div>
                </div>
            </div>

            {/* Content */}
            {loading ? (
                <div className="flex justify-center p-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-zinc-900 dark:border-zinc-100"></div>
                </div>
            ) : (
                <SanctionsTable data={data} />
            )}
        </div>
    );
}
