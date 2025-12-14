import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans">
      <main className="flex flex-col items-center gap-8">
        <h1 className="text-4xl font-bold">HUNT Game</h1>
        <Link
          href="/admin"
          className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          Админка
        </Link>
      </main>
    </div>
  );
}
