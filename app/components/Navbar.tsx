import Link from 'next/link';

export function Navbar() {
    return (
        <nav className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex h-16 justify-between items-center">
                    <div className="flex items-center">
                        <Link href="/" className="font-bold text-xl tracking-tight text-zinc-900 dark:text-white">
                            StableTrace
                        </Link>
                        <div className="hidden md:block ml-10 space-x-8">
                            <Link href="/" className="text-sm font-medium text-zinc-900 dark:text-zinc-100 hover:text-blue-600">
                                Market
                            </Link>
                            <Link href="/risk" className="text-sm font-medium text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white">
                                Risk Overlay
                            </Link>
                        </div>
                    </div>
                    <div>
                        <span className="text-xs px-2 py-1 bg-zinc-100 dark:bg-zinc-800 rounded text-zinc-500">v0.1.0</span>
                    </div>
                </div>
            </div>
        </nav>
    );
}
