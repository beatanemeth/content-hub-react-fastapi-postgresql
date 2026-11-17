import { useParams } from 'react-router';

export default function PostForm() {
  // Only /blog/:id/edit has an id; /blog/new has none
  const { id } = useParams();
  const isEditing = id !== undefined;

  return (
    <h1 className="font-heading text-7xl leading-[1.2] font-bold">
      {isEditing ? 'Edit post' : 'New post'}
    </h1>
  );
}
