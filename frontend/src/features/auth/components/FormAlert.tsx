export function FormAlert({ message }: { message: string | null }) {
  if (!message) return null
  // role="alert" makes screen readers announce the error as soon as it appears.
  return (
    <div role="alert" className="form-alert">
      {message}
    </div>
  )
}
