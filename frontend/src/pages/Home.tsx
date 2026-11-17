import { Link } from 'react-router';

export default function Home() {
  return (
    <div className="text-center">
      <h1 className="font-heading text-7xl leading-[1.2] font-bold">
        Bloom & Burr Coffee Co.
      </h1>
      <div className="mt-8 flex flex-col gap-6 text-xl leading-relaxed">
        <p>
          We are an independent speciality roastery, café and brewing school. We
          roast and serve speciality coffee, and we teach people to brew it at
          home, without jargon and without price barriers.
        </p>
        <p>
          Bloom & Burr started five years ago as a weekend pop-up, run by seven
          people in a borrowed community kitchen. Two years later, we moved into
          our own roastery with a café. Today our community has more than 3,000
          members, and our readers live in over 40 countries.
        </p>
        <p>
          We follow an idea from the late roaster Hannah Ruth: good coffee is a
          conversation between farmer, roaster, barista and guest, and that
          conversation should stay kind.
        </p>
        <p>
          Stories from our events and our guests are on the{' '}
          <Link to="/blog" className="text-cobalt-blue underline">
            blog
          </Link>
          .
        </p>
      </div>
    </div>
  );
}
