import { Route, Routes } from 'react-router';
import Layout from './components/Layout.tsx';
import BlogList from './pages/BlogList.tsx';
import Home from './pages/Home.tsx';
import NotFound from './pages/NotFound.tsx';
import Post from './pages/Post.tsx';
import PostForm from './pages/PostForm.tsx';

export default function App() {
  return (
    <Routes>
      {/* A layout route has no path: it wraps every page in the header and footer */}
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="blog" element={<BlogList />} />
        <Route path="blog/new" element={<PostForm />} />
        <Route path="blog/:id" element={<Post />} />
        <Route path="blog/:id/edit" element={<PostForm />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
