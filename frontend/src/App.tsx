import { Route, Routes } from 'react-router';
import Layout from './components/Layout.tsx';
import Home from './pages/Home.tsx';

export default function App() {
  return (
    <Routes>
      {/* A layout route has no path: it wraps every page in the header and footer */}
      <Route element={<Layout />}>
        <Route index element={<Home />} />
      </Route>
    </Routes>
  );
}
