import { Link } from 'react-router';

export default function NotFound() {
  return (
    <div className="text-center">
      <h1 className="font-heading text-7xl leading-[1.2] font-bold">
        Page not found
      </h1>
      <div className="mt-8 flex flex-col gap-6 text-xl leading-relaxed">
        <p>This page does not exist.</p>
        <p>
          <Link to="/" className="text-cobalt-blue underline">
            Go to the home page
          </Link>
        </p>
      </div>
    </div>
  );
}
