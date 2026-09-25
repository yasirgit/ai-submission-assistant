export function MissingInformation({
  missing,
  questions,
}: {
  missing: string[];
  questions: string[];
}) {
  return (
    <section>
      <h3>Missing information</h3>
      {missing.length === 0 ? (
        <p className="muted">The draft did not list missing information.</p>
      ) : (
        <ul>
          {missing.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
      {questions.length > 0 && (
        <>
          <h3>Follow-up questions</h3>
          <ul>
            {questions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
