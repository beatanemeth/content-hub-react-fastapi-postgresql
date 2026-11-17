import { Link } from 'react-router';

interface NavLink {
  label: string;
  to: string;
}

// No page yet; these links show the not-found page
const FOOTER_LINKS: NavLink[] = [
  { label: 'Privacy policy', to: '/privacy' },
  { label: 'Impressum', to: '/impressum' },
  { label: 'Cookies notice', to: '/cookies' },
];

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="bg-burlap-tan">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-8 py-4 text-base">
        <p>© {year} Bloom & Burr</p>
        <nav aria-label="Footer">
          <ul className="flex gap-6">
            {FOOTER_LINKS.map((link) => (
              <li key={link.to}>
                <Link to={link.to}>{link.label}</Link>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </footer>
  );
}
