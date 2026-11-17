import { type SubmitEvent, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router';
import { getCategories, getTags } from '../api/options.ts';
import {
  createPost,
  getPost,
  type Label,
  type PostDetail,
  type PostInput,
  updatePost,
} from '../api/posts.ts';
import Button from '../components/Button.tsx';
import NotFound from './NotFound.tsx';

const FIELD_STYLE = 'flex flex-col gap-2';
const LABEL_STYLE = 'font-medium';
const HINT_STYLE = 'text-sm font-normal';
const INPUT_STYLE = 'rounded-xl border border-black bg-white px-4 py-2';

// Screen readers announce the input's required attribute, so they skip the star
const RequiredMark = () => (
  <span aria-hidden="true" className="text-brick-red">
    {' '}
    *
  </span>
);

interface CheckboxGroupProps {
  legend: string;
  name: string;
  items: Label[];
  initialLabels: string[];
}

// A fieldset groups the boxes, and its legend names the group for screen readers
const CheckboxGroup = ({
  legend,
  name,
  items,
  initialLabels,
}: CheckboxGroupProps) => {
  const [selectedLabels, setSelectedLabels] = useState(initialLabels);
  // HTML has no "at least one box" rule, so every box is required until one is ticked
  const isNoneSelected = selectedLabels.length === 0;

  const handleChange = (label: string) => {
    setSelectedLabels(
      selectedLabels.includes(label)
        ? selectedLabels.filter((selectedLabel) => selectedLabel !== label)
        : [...selectedLabels, label],
    );
  };

  return (
    <fieldset className={FIELD_STYLE}>
      <legend className={LABEL_STYLE}>
        {legend} <span className={HINT_STYLE}>(choose one or more)</span>
        <RequiredMark />
      </legend>
      <div className="grid grid-cols-3 gap-x-6 gap-y-1">
        {items.map((item) => (
          <label key={item.id} className="flex items-center gap-2">
            <input
              type="checkbox"
              name={name}
              // The label is the value, because the request body sends labels
              value={item.label}
              checked={selectedLabels.includes(item.label)}
              onChange={() => handleChange(item.label)}
              required={isNoneSelected}
            />
            {item.label}
          </label>
        ))}
      </div>
    </fieldset>
  );
};

export default function PostForm() {
  // Only /blog/:id/edit has an id; /blog/new has none
  const { id } = useParams();
  const isEditing = id !== undefined;
  const [post, setPost] = useState<PostDetail | null>(null);
  const [categories, setCategories] = useState<Label[] | null>(null);
  const [tags, setTags] = useState<Label[] | null>(null);
  const [isNotFound, setIsNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Separate from error: a failed save keeps the form and the typed values on screen
  const [saveError, setSaveError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    async function loadForm() {
      try {
        // The requests run at the same time; a new post has no post to load
        const [postData, categoryData, tagData] = await Promise.all([
          isEditing ? getPost(Number(id)) : null,
          getCategories(),
          getTags(),
        ]);

        if (isEditing && postData === null) {
          setIsNotFound(true);
          return;
        }

        setPost(postData);
        setCategories(categoryData);
        setTags(tagData);
      } catch (err) {
        setError((err as Error).message);
      }
    }

    loadForm();
  }, [id, isEditing]);

  if (isNotFound) {
    return <NotFound />;
  }

  // defaultValue is read only on the first render, so the form waits for the post and the options
  if (categories === null || tags === null || (isEditing && post === null)) {
    return <p className="text-xl leading-relaxed">{error ?? 'Loading…'}</p>;
  }

  // onSubmit runs only after the browser has checked every required field
  const handleSubmit = async (event: SubmitEvent<HTMLFormElement>) => {
    // Stop the browser from sending the form itself and loading a new page
    event.preventDefault();
    setSaveError(null);

    // The inputs are uncontrolled, so FormData reads each value by its name attribute
    const formData = new FormData(event.currentTarget);
    // No author: the API takes it from the mock session
    const input: PostInput = {
      title: String(formData.get('title')),
      summary: String(formData.get('summary')),
      body: String(formData.get('body')),
      published_on: String(formData.get('published_on')),
      // getAll gives the values (labels) of all ticked boxes with this name
      categories: formData.getAll('categories').map(String),
      tags: formData.getAll('tags').map(String),
    };

    try {
      const savedPost = isEditing
        ? await updatePost(Number(id), input)
        : await createPost(input);
      navigate(`/blog/${savedPost.id}`);
    } catch (err) {
      setSaveError((err as Error).message);
    }
  };

  return (
    <div className="rounded-xl bg-oat-milk px-8 py-12 text-xl leading-relaxed">
      <h1 className="text-center font-heading text-7xl leading-[1.2] font-bold">
        {isEditing ? 'Edit post' : 'New post'}
      </h1>
      <form
        onSubmit={handleSubmit}
        className="mx-auto mt-10 flex max-w-4xl flex-col gap-6"
      >
        <label className={FIELD_STYLE}>
          <span className={LABEL_STYLE}>
            Post title
            <RequiredMark />
          </span>
          <input
            type="text"
            name="title"
            placeholder="Your blog post title"
            defaultValue={post?.title}
            required
            className={INPUT_STYLE}
          />
        </label>
        <CheckboxGroup
          legend="Post category"
          name="categories"
          items={categories}
          initialLabels={post?.categories.map((item) => item.label) ?? []}
        />
        <CheckboxGroup
          legend="Post tags"
          name="tags"
          items={tags}
          initialLabels={post?.tags.map((item) => item.label) ?? []}
        />
        <label className={FIELD_STYLE}>
          <span className={LABEL_STYLE}>
            Post publish date
            <RequiredMark />
          </span>
          <input
            type="date"
            name="published_on"
            defaultValue={post?.published_on}
            required
            className={INPUT_STYLE}
          />
        </label>
        <label className={FIELD_STYLE}>
          <span className={LABEL_STYLE}>
            Post short summary
            <RequiredMark />
          </span>
          <textarea
            name="summary"
            rows={3}
            placeholder="Your blog post summary"
            defaultValue={post?.summary}
            required
            className={INPUT_STYLE}
          />
        </label>
        <label className={FIELD_STYLE}>
          <span className={LABEL_STYLE}>
            Post body text{' '}
            <span className={HINT_STYLE}>
              (separate paragraphs with a blank line)
            </span>
            <RequiredMark />
          </span>
          <textarea
            name="body"
            rows={12}
            placeholder="Your blog post text"
            defaultValue={post?.body}
            required
            className={INPUT_STYLE}
          />
        </label>
        {saveError !== null && <p>{saveError}</p>}
        <div className="flex gap-4">
          <Button type="submit">Save</Button>
          <Button variant="tertiary" to={isEditing ? `/blog/${id}` : '/blog'}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}
