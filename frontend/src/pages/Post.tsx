import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import { deletePost, getPost, type PostDetail } from '../api/posts.ts';
import Button from '../components/Button.tsx';
import NotFound from './NotFound.tsx';

export default function Post() {
  const { id } = useParams();
  const [post, setPost] = useState<PostDetail | null>(null);
  const [isNotFound, setIsNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Separate from error: a failed delete keeps the post on screen
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const navigate = useNavigate();

  // [id] runs the effect again when the URL points to another post
  useEffect(() => {
    async function loadPost() {
      try {
        // useParams gives every URL part as a string; the post ids are numbers
        const data = await getPost(Number(id));

        if (data === null) {
          setIsNotFound(true);
        } else {
          setPost(data);
        }
      } catch (err) {
        setError((err as Error).message);
      }
    }

    loadPost();
  }, [id]);

  if (isNotFound) {
    return <NotFound />;
  }

  // Until the post arrives, show "Loading…", or the error if the request failed
  if (post === null) {
    return <p className="text-xl leading-relaxed">{error ?? 'Loading…'}</p>;
  }

  const categories = post.categories.map((item) => item.label).join(' • ');
  const tags = post.tags.map((item) => item.label).join(', ');
  const paragraphs = post.body.split('\n\n');

  const handleDelete = async () => {
    // confirm() returns false when the user clicks Cancel
    if (!window.confirm('Delete this post?')) {
      return;
    }

    try {
      await deletePost(post.id);
      // The post no longer exists, so the list is the next page
      navigate('/blog');
    } catch (err) {
      setDeleteError((err as Error).message);
    }
  };

  return (
    // The text size set here is inherited by every part that does not set its own
    <article className="rounded-xl bg-parchment-cream px-8 py-12 text-xl leading-relaxed">
      <header className="text-center">
        <h1 className="font-heading text-7xl leading-[1.2] font-bold">
          {post.title}
        </h1>
        <p className="mt-6 text-sm tracking-wide uppercase">
          {post.published_on} • {post.author.full_name} • {post.minutes_to_read}{' '}
          min read
        </p>
        <p className="mx-auto mt-8 max-w-4xl">{post.summary}</p>
      </header>
      <hr className="mx-auto mt-10 max-w-xl" />
      <p className="mt-10 text-center text-sm tracking-wide">{categories}</p>
      <div className="mx-auto mt-10 max-w-4xl">
        <div className="flex flex-col gap-6">
          {paragraphs.map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
        </div>
        <p className="mt-12 text-sm italic">{tags}</p>
        {deleteError !== null && <p className="mt-12">{deleteError}</p>}
        <div className="mt-12 flex gap-4">
          <Button variant="secondary" to={`/blog/${post.id}/edit`}>
            Edit
          </Button>
          <Button variant="tertiary" type="button" onClick={handleDelete}>
            Delete
          </Button>
        </div>
      </div>
    </article>
  );
}
