/** Moves keyboard focus to the first field (in form order) that has an error. */
export function focusFirstInvalid(
  form: HTMLFormElement,
  fields: readonly string[],
  errors: Partial<Record<string, string>>,
): void {
  const first = fields.find((name) => errors[name])
  if (!first) return
  const element = form.elements.namedItem(first)
  if (element instanceof HTMLElement) {
    element.focus()
  }
}
