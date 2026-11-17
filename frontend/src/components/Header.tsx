import { Link } from 'react-router';

interface NavLink {
  label: string;
  to: string;
}

// Only Blog has a page yet; the others show the not-found page
const NAV_LINKS: NavLink[] = [
  { label: 'About', to: '/about' },
  { label: 'Events', to: '/events' },
  { label: 'Blog', to: '/blog' },
  { label: 'Contact', to: '/contact' },
];

export default function Header() {
  return (
    <header className="bg-latte-tan">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-8 py-4">
        <Link to="/" className="font-heading text-3xl font-bold">
          Bloom & Burr
        </Link>
        <nav aria-label="Main">
          <ul className="flex gap-8 text-xl leading-relaxed">
            {NAV_LINKS.map((link) => (
              <li key={link.to}>
                <Link to={link.to}>{link.label}</Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </header>
  );
}
