import React from "react";

function SearchResults({ results }) {
  if (!results || results.length === 0) {
    return null;
  }

  return (
    <div className="results-container">
      <h3>Search Results</h3>
      <div className="results-grid">
        {results.map(([imagePath, score], index) => {
          // Convert dataset path to a public-accessible path
          const fixedPath = imagePath.replace("./", "/");

          return (
            <div key={index} className="result-item">
              <img
                src={fixedPath}
                alt={`Result ${index + 1}`}
                className="result-image"
              />
              <p>Similarity Score: {score.toFixed(1)}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default SearchResults;
