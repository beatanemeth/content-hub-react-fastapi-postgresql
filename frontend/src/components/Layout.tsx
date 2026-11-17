import { Outlet } from 'react-router';
import Footer from './Footer.tsx';
import Header from './Header.tsx';

export default function Layout() {
  return (
    // flex-1 on main fills the free height, so the footer stays at the bottom of a short page
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="mx-auto w-full max-w-7xl flex-1 px-8 py-16">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
