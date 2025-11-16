import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="text-center px-6">
        <h1 className="text-6xl font-bold text-gray-900 mb-2">Wordloom</h1>
        <p className="text-xl text-gray-600 mb-8">Your Personal Knowledge Management System</p>
        <div className="space-x-4">
          <Link href="/admin/dashboard" className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Dashboard
          </Link>
          <Link href="/(auth)/login" className="px-8 py-3 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300">
            Login
          </Link>
        </div>
      </div>
    </main>
  );
}
