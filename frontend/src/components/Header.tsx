import { Link, useLocation } from "react-router-dom";
import clsx from "clsx";

export function Header() {
  const { pathname } = useLocation();

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2.5">
            <span className="text-2xl font-bold bg-gradient-to-r from-brand-600 to-indigo-500 bg-clip-text text-transparent">
              PipelineIQ
            </span>
            <span className="hidden sm:block text-xs text-gray-400 font-medium mt-1">
              AI-Powered Pipeline Intelligence
            </span>
          </Link>

          <nav className="flex items-center gap-1">
            <NavLink to="/" current={pathname === "/"}>
              Dashboard
            </NavLink>
          </nav>
        </div>
      </div>
    </header>
  );
}

function NavLink({
  to,
  current,
  children,
}: {
  to: string;
  current: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      to={to}
      className={clsx(
        "px-3 py-2 rounded-md text-sm font-medium transition-colors",
        current
          ? "bg-brand-50 text-brand-700"
          : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
      )}
    >
      {children}
    </Link>
  );
}
