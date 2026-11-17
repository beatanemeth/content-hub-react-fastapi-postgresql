# UI specifications: Bloom & Burr Coffee Co.

Part of the [brand style guide](./brand_style_guide.md). Colours, fonts and logo are in [ui_visual_identity](../../.claude/rules/ui_visual_identity.md).

| Step | Topic                                                   |
| ---- | ------------------------------------------------------- |
| 1    | Pages and URLs                                          |
| 2    | Components                                              |
| 3    | Routing: route table, layout and `<Outlet />`           |
| 4    | Post fields                                             |
| 5    | Navigation and footer                                   |
| 6    | Tailwind CSS and fonts set-up                           |
| 7    | Design tokens: colours, buttons, fonts, layout, spacing |
| 8    | Page content                                            |
| 9    | States: empty list, not found, form errors, delete      |

<br>

## 1. Pages and URLs

| Page                | URL              |
| ------------------- | ---------------- |
| **Home**            | `/`              |
| **Blog: post list** | `/blog`          |
| **Blog: one post**  | `/blog/:id`      |
| **Blog: new post**  | `/blog/new`      |
| **Blog: edit post** | `/blog/:id/edit` |
| **Not found**       | any other URL    |

There is no login page: the mock login runs in the API's `/docs` page or in `blog.http` (see [info_out_of_scope_workaround.md](../notes/info_out_of_scope_workaround.md)).

<br>

## 2. Components

- **JSX syntax:** the HTML attribute `class` is written `className`.
- **No component library** (such as HeroUI, formerly NextUI): the components are written by hand, because building them is the React practice this project is for. The design has three button variants and one input style, and the browser's own date input, checkboxes and `window.confirm()` cover the complex widgets. A library is reconsidered only if a feature needs a widget the browser lacks, such as a styled modal.

| Component    | Shows                                               | Used on                                            |
| ------------ | --------------------------------------------------- | -------------------------------------------------- |
| `<Layout>`   | `<Header />`, the page (`<Outlet />`), `<Footer />` | Every page                                         |
| `<Header>`   | Logo and navigation                                 | Every page, through `<Layout>`                     |
| `<Footer>`   | Copyright and footer links                          | Every page, through `<Layout>`                     |
| `<PostCard>` | One post in the list                                | `<BlogList>`                                       |
| `<Button>`   | A button or link in one of the three variants       | `<PostCard>`, `<BlogList>`, `<Post>`, `<PostForm>` |
| `<Home>`     | Home page                                           | `/`                                                |
| `<BlogList>` | Post list                                           | `/blog`                                            |
| `<Post>`     | One post                                            | `/blog/:id`                                        |
| `<PostForm>` | New and edit form                                   | `/blog/new`, `/blog/:id/edit`                      |
| `<NotFound>` | Not-found page                                      | Any other URL (`path="*"`)                         |

- **`<Button>` props:** `variant` (`primary`, `secondary` or `tertiary`; default `primary`) picks the classes from a `BUTTON_STYLE` lookup object. With a `to` prop it renders a `<Link>`; without it, a `<button>`.
- **Link or button:** Read, Add new post, Edit and Cancel go to another page, so they are links. Save and Delete perform an action, so they are buttons.
- **Cancel:** on the new-post form it goes to `/blog`; on the edit form it goes to `/blog/:id`.
- **Files:** the shared parts (`Layout`, `Header`, `Footer`, `Button`, `PostCard`) in `src/components/`; the five page components in `src/pages/`.
- **API files:** `src/api/client.ts` holds the shared `request()` and `readError()`; `src/api/posts.ts` holds the post interfaces (`PostSummary`, `PostDetail`, `PostInput`, `Author`, `Label`) and one function per post endpoint; `src/api/options.ts` loads the categories and tags. There is no `src/data/lists.ts`: a post carries its author, categories and tags, and the form loads its options from the API.

<br>

## 3. Routing

- **Mode:** React Router in declarative mode. It has the fewest new concepts, and data loading stays in our own code.
- **Package:** `react-router`. Older tutorials use `react-router-dom`, which is no longer needed.
- **Set-up:** `<BrowserRouter>` wraps `<App />` in `src/main.tsx`; the routes are written as JSX in `src/App.tsx`.

| URL              | Route                                | Page component |
| ---------------- | ------------------------------------ | -------------- |
| `/`              | `<Route index element={<Home />} />` | `<Home>`       |
| `/blog`          | `<Route path="blog" ... />`          | `<BlogList>`   |
| `/blog/new`      | `<Route path="blog/new" ... />`      | `<PostForm>`   |
| `/blog/:id`      | `<Route path="blog/:id" ... />`      | `<Post>`       |
| `/blog/:id/edit` | `<Route path="blog/:id/edit" ... />` | `<PostForm>`   |
| Any other URL    | `<Route path="*" ... />`             | `<NotFound>`   |

- **Layout route:** all routes above sit inside one `<Route element={<Layout />}>` without a `path`. `<Layout>` shows the header and footer, and the matched page appears where `<Layout>` places `<Outlet />`.
- **`/blog/new` and `/blog/:id`:** React Router ranks a fixed segment (`new`) above a dynamic one (`:id`), so `/blog/new` never opens a post.
- **Reading the id:** `<Post>` and `<PostForm>` read `id` from the URL with `useParams()`.
- **Links:** header, footer and page links use `<Link to="...">`. The browser does not reload the page; React Router swaps the component.

<br>

## 4. Post fields

| Field            | Form input            |
| ---------------- | --------------------- |
| **Title**        | `<input type="text">` |
| **Categories**   | Checkboxes            |
| **Tags**         | Checkboxes            |
| **Publish date** | `<input type="date">` |
| **Summary**      | `<textarea>`, 3 rows  |
| **Body text**    | `<textarea>`, 12 rows |

- **Form heading:** "New post" on `/blog/new`, "Edit post" on `/blog/:id/edit`. The field labels stay as in the copied `<PostForm>`.
- **No author field:** the author is the staff member of the mock session. The API sets it on create and keeps it on edit.
- **Categories and tags are lists:** a post has one or more categories and one or more tags. In the form, each is a group of checkboxes in three columns, filled from `GET /api/categories` and `GET /api/tags`, and at least one box per group must be ticked.
- **Request body:** carries the **labels** of the ticked boxes (`categories`, `tags`); each checkbox's `value` is its label. The API looks up the ids. The edit form pre-ticks the boxes from the post's `categories` and `tags`.
- **Body paragraphs:** separated by a blank line, which the single post turns into paragraphs.
- **Not entered in the form:** `id`, `updated_at` (both set by the API) and **minutes to read**. `<Post>` calculates minutes to read from the body text (200 words per minute, at least 1 minute) and shows it on the single post only.

<br>

## 5. Navigation and footer

- **Header:** logo, then About, Events, Blog, Contact.
- **Footer:** "© <current year> Bloom & Burr", then Privacy policy, Impressum, Cookies notice.
- **Pages not built:** the menu items stay, although only Blog (and the logo, to Home) has a page.
- **Their links:** point to the future URLs (`/about`, `/events`, `/contact`, `/privacy`, `/impressum`, `/cookies`), which show the not-found page.

<br>

## 6. Tailwind CSS and fonts set-up

- **Tailwind set-up:** the `@tailwindcss/vite` plugin. The Vite dev server builds the CSS, so no second terminal is needed.
- **Theme file:** `src/globals.css`, imported once in `src/main.tsx`. It holds `@import 'tailwindcss';` and one `@theme` block with the colours and font families.
- **Only the plan's colours:** the `@theme` block starts with `--color-*: initial;`, which removes Tailwind's default palette, so no other colours slip in.
- **Default font:** `--font-sans` is Poppins, so the whole page uses it without a class; `--font-heading` is Raleway.
- **Focus rule:** `globals.css` also holds one `:focus-visible` rule for the keyboard focus outline. One global rule covers every link, button and input, so a new element cannot miss it.
- **Template files:** the Vite template's `src/index.css` and `src/App.css` are deleted; `globals.css` is the only CSS file.
- **Fonts:** Google Fonts `<link>` tags in the `<head>` of `index.html`. The browser finds them in the HTML and starts the download before any CSS has loaded.
- **Browser tab:** the `<title>` in `index.html` is "Bloom & Burr"; the template's favicon stays.

<br>

## 7. Design tokens

- **Principle:** as simple as possible. No shadows, no transitions, no animations.
- **Basis:** the maintainer's own palette.
- **Text colour:** black everywhere, except links and the required-field asterisk.

### Colours

Palette and names: [ui_visual_identity](../../.claude/rules/ui_visual_identity.md). Where each colour is used:

| Part                                        | Background     | Border                  | Text                               |
| ------------------------------------------- | -------------- | ----------------------- | ---------------------------------- |
| **Page**                                    | white          | none                    | black                              |
| **Header and footer**                       | burlapTan      | none                    | black                              |
| **Panels** (post card, post, form)          | parchmentCream | none; `rounded-xl`      | black                              |
| **Inputs**                                  | white          | 1px black; `rounded-xl` | black                              |
| **Links in text**                           | none           | none                    | royalCobalt, underlined            |
| **Required-field asterisk**                 | none           | none                    | brickRed (6.0:1 on parchmentCream) |
| **Keyboard focus** (links, buttons, inputs) | none           | 2px royalCobalt outline | none                               |

- **Contrast:** every pairing passes WCAG AA, as does black text on every button background.
- **Input placeholders:** allowed in text inputs and text areas, as in the examples of `validation_frontend.md`.
- **Label hints:** sit next to the label, in black: "(choose one or more)" for categories and tags, "(separate paragraphs with a blank line)" for the body text.

### Buttons

All buttons: `rounded-xl` (12px), uppercase text, no shadow. Hover changes only the colour, with no transition.

| Variant       | Background    | Border           | Hover background | Used for           |
| ------------- | ------------- | ---------------- | ---------------- | ------------------ |
| **Primary**   | hazelnutLight | none             | hazelnutDark     | Read, Save         |
| **Secondary** | burlapTan     | 2px darkEspresso | hazelnutDark     | Add new post, Edit |
| **Tertiary**  | none           | 1px black      | white            | Cancel, Delete     |

### Fonts

Families, weights and sizes: [ui_visual_identity](../../.claude/rules/ui_visual_identity.md#typography).

### Layout

- **Desktop only:** designed for the Tailwind `lg` breakpoint and wider.
- **Look:** the components copied from the Express repo set the layout.
- **Content width:** up to 1280px (`max-w-7xl`), centred.
- **Footer:** at the bottom of the window, also on a short page.

### Spacing

Tailwind spacing classes; one value per gap, so the pages share one rhythm.

| Part                     | Spacing                                                                                                                                                                      |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Header and footer**    | `px-8 py-4`; nav links `gap-8` in the header, `gap-6` in the footer                                                                                                          |
| **Page area** (`main`)   | `px-8 py-16`                                                                                                                                                                 |
| **Page intro**           | `mt-8` between the `h1` and its text; `gap-6` between the home paragraphs                                                                                                    |
| **Post list**            | `mt-12` above the Add new post row and above the grid; `gap-8` between cards                                                                                                 |
| **Post card**            | `p-8`; `gap-4` between its parts                                                                                                                                             |
| **Single post and form** | Panel `px-8 py-12`                                                                                                                                                           |
| **Single post**          | Meta line `mt-6`; summary `mt-8`; rule `mt-10`, 576px wide (`max-w-xl`); categories `mt-10`; body `mt-10`, `gap-6` between paragraphs; tags `mt-12`; Edit and Delete `mt-12` |
| **Form**                 | `mt-10` below the heading; `gap-6` between fields; `gap-2` between a label and its input; checkboxes `gap-x-6 gap-y-1`                                                       |
| **Buttons and inputs**   | Buttons `px-6 py-2`, `gap-4` between buttons in a row; inputs `px-4 py-2`                                                                                                    |

<br>

## 8. Page content

### Home

Heading (`h1`): **Bloom & Burr Coffee Co.** Then four paragraphs, centred:

> We are an independent speciality roastery, café and brewing school. We roast and serve speciality coffee, and we teach people to brew it at home, without jargon and without price barriers.
>
> Bloom & Burr started five years ago as a weekend pop-up, run by seven people in a borrowed community kitchen. Two years later, we moved into our own roastery with a café. Today our community has more than 3,000 members, and our readers live in over 40 countries.
>
> We follow an idea from the late roaster Hannah Ruth: good coffee is a conversation between farmer, roaster, barista and guest, and that conversation should stay kind.
>
> Stories from our events and our guests are on the blog.

- **Link:** the word "blog" in the last paragraph links to `/blog`.
- **Source:** every fact is in [brand_story.md](./brand_story.md).

### Blog

Heading (`h1`): **Blog**. Then one paragraph:

> Stories from the roastery, the café and our events: brewing tips, event reports and guest posts from our community.

- **Post card and single post:** the parts and their order stay as in the copied `<PostCard>` and `<Post>`.
- **Meta line:** `<date> • <author>` on a post card; `<date> • <author> • <n> min read` on the single post. The author is `post.author.full_name`.
- **Categories and tags:** their `label` values, from the post's `categories` and `tags`.
- **Separators:** " • " in the meta line and between categories; tags are joined with ", ".
- **Dates:** shown as the API sends them (`YYYY-MM-DD`).

### Not found

Heading (`h1`): **Page not found**. Then "This page does not exist." and the link "Go to the home page" to `/`, centred like the home page.

<br>

## 9. States

| State                   | Behaviour                                                                                                                                                                                                                                                                                                                                             |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Empty blog list**     | The text "No posts yet."; the Add new post button stays.                                                                                                                                                                                                                                                                                              |
| **Not found**           | `<NotFound>` shows a short message and a link to Home. The `path="*"` route shows it for unknown URLs; `<Post>` and `<PostForm>` show it for an unknown id (`/blog/999`, `/blog/999/edit`) and for an id that is not a whole number (`/blog/abc`), which the API answers with `422`.                                                                       |
| **Form errors**         | Every field is required: its label has a brickRed asterisk (hidden from screen readers, which announce `required` instead), and its input has the HTML `required` attribute, so the browser blocks an empty field and sends nothing. A checkbox group has no `required` of its own: while no box in a group is ticked, every box in it is `required`. |
| **API errors**          | The API's error message (`detail`), as plain text; a 422 shows all its messages joined in one line. A failed load shows it instead of "Loading…"; a failed delete, above Edit and Delete; a failed save, above Save, with the typed values kept. Without a mock session, a save or delete shows `Not signed in`.                                    |
| **Delete confirmation** | The Delete button's `onClick` handler calls `window.confirm('Delete this post?')`. OK deletes the post; Cancel does nothing.                                                                                                                                                                                                                          |

- **No `404` status:** the app is one HTML page, which the server always sends with status `200`. React decides in the browser which component to show.
- **Limit of `required`:** it only checks that a field is not empty. A title of only spaces passes the browser; the API then answers `422` (for example `title: String should have at least 1 character`), which the form shows as an API error.
