import { useParams } from 'react-router';

export default function Post() {
  const { id } = useParams();

  return (
    <h1 className="font-heading text-7xl leading-[1.2] font-bold">Post {id}</h1>
  );
}
