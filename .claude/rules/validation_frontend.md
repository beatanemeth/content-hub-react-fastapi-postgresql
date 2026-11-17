---
paths:
  - 'frontend/src/components/**'
  - 'frontend/src/pages/**'
---

# Rules: minimal frontend validation

- **Native HTML attributes:** rely on `required` and the input types (`type="date"`) rather than validation libraries (like Zod or React Hook Form), unless the maintainer asks for one.
- **Every field is required:** title, categories, tags, published date, summary and body. There is no author field; the author comes from the mock session.
- **Checkbox groups:** HTML has no "at least one box of this group" rule; `required` on a checkbox means that box must be ticked. So every box of a group is `required` while none is ticked: `required={selectedLabels.length === 0}`.
- **The backend has the final word:** it trims the text, rejects empty strings and impossible dates, and checks that each label exists. Its 422 or 400 message is shown as plain text (see [error_handling_frontend.md](./error_handling_frontend.md)); the frontend does not repeat these checks.

<br>

## Example: a text field and a checkbox group

`onSubmit` runs only after the browser has checked every `required` field.

```tsx
<label className={FIELD_STYLE}>
  <span className={LABEL_STYLE}>Post title</span>
  <input type="text" name="title" required className={INPUT_STYLE} />
</label>

<fieldset className={FIELD_STYLE}>
  <legend className={LABEL_STYLE}>Post category</legend>
  {categories.map((category) => (
    <label key={category.id}>
      <input
        type="checkbox"
        name="categories"
        // The label is the value, because the request body sends labels
        value={category.label}
        checked={selectedLabels.includes(category.label)}
        onChange={() => handleChange(category.label)}
        required={selectedLabels.length === 0}
      />
      {category.label}
    </label>
  ))}
</fieldset>
```

`categories` comes from `GET /api/categories`. On submit, `formData.getAll('categories')` gives the ticked labels.
