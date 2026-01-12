"use client";

import { useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';

interface SupplyPoint {
    timestamp: string;
    total_supply: number;
}

interface SupplyChartProps {
    data: SupplyPoint[];
}

const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        notation: 'compact',
        maximumFractionDigits: 1,
    }).format(value);
};

export function SupplyChart({ data }: SupplyChartProps) {
    // Sort data just in case
    const sortedData = useMemo(() => {
        return [...data].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    }, [data]);

    if (!data || data.length === 0) {
        return <div className="h-72 flex items-center justify-center text-gray-500">No data available</div>;
    }

    return (
        <div className="w-full h-[400px] bg-white dark:bg-zinc-900 rounded-xl p-4 shadow-sm border border-zinc-200 dark:border-zinc-800">
            <h3 className="text-lg font-semibold mb-4 text-zinc-900 dark:text-zinc-100">Total Stablecoin Supply</h3>
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                    data={sortedData}
                    margin={{
                        top: 10,
                        right: 30,
                        left: 0,
                        bottom: 0,
                    }}
                >
                    <CartesianGrid strokeDasharray="3 3" opacity={0.1} vertical={false} />
                    <XAxis
                        dataKey="timestamp"
                        tickFormatter={(str) => format(new Date(str), 'MMM d')}
                        stroke="#888888"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                    />
                    <YAxis
                        tickFormatter={(val) => formatCurrency(val)}
                        stroke="#888888"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: 'rgba(255, 255, 255, 0.9)',
                            borderRadius: '8px',
                            border: '1px solid #e5e7eb',
                            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                        formatter={(value: number | undefined) => [formatCurrency(value || 0), "Total Supply"]}
                        labelFormatter={(label) => format(new Date(label), 'MMM d, yyyy')}
                    />
                    <Area
                        type="monotone"
                        dataKey="total_supply"
                        stroke="#2563eb"
                        fill="url(#colorSupply)"
                        fillOpacity={0.2}
                        strokeWidth={2}
                    />
                    <defs>
                        <linearGradient id="colorSupply" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}
