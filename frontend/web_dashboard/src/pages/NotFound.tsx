export default function NotFound() {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-cyan-400 mb-4">404</h1>
        <p className="text-2xl text-gray-300 mb-4">Page Not Found</p>
        <p className="text-gray-400 mb-8">The resource you're looking for doesn't exist.</p>
        <a
          href="/"
          className="inline-block px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-slate-900 font-semibold rounded transition-colors"
        >
          Go Back Home
        </a>
      </div>
    </div>
  );
}
