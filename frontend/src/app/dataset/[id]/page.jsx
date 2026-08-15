export default function DatasetDetailsPage({ params }) {
  const { id } = params;

  return (
    <div>
      <h1>Dataset Details</h1>
      <p>Dataset ID: {id}</p>
    </div>
  );
}
