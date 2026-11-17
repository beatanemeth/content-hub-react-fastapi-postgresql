import { useEffect, useState } from 'react';
import { getPosts, type PostSummary } from '../api/posts.ts';
import Button from '../components/Button.tsx';
import PostCard from '../components/PostCard.tsx';

const MESSAGE_STYLE = 'mt-12 text-xl leading-relaxed';

export default function BlogList() {
  // null until the answer arrives: "still loading" differs from "no posts"
  const [posts, setPosts] = useState<PostSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // The empty list runs the effect once, after the first render, not on every render
  useEffect(() => {
    async function loadPosts() {
      try {
        setPosts(await getPosts());
      } catch (err) {
        // getPosts and fetch both throw an Error
        setError((err as Error).message);
      }
    }

    loadPosts();
  }, []);

  return (
    <div>
      <h1 className="text-center font-heading text-7xl leading-[1.2] font-bold">
        Blog
      </h1>
      <p className="mt-8 text-center text-xl leading-relaxed">
        Stories from the roastery, the café and our events: brewing tips, event
        reports and guest posts from our community.
      </p>
      <div className="mt-12 flex justify-end">
        <Button variant="secondary" to="/blog/new">
          Add new post
        </Button>
      </div>
      {posts === null && <p className={MESSAGE_STYLE}>{error ?? 'Loading…'}</p>}
      {posts?.length === 0 && <p className={MESSAGE_STYLE}>No posts yet.</p>}
      {posts !== null && posts.length > 0 && (
        <div className="mt-12 grid grid-cols-2 gap-8">
          {posts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      )}
    </div>
  );
}
