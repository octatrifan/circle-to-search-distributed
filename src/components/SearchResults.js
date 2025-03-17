import React from "react";
import "../styles/style.css"; 
const SearchResults = ({ results }) => {
  if (!results || results.length === 0) {
    return <p>No results found</p>;
  }

  return (
    <div className="results-container">
      <h3>Search Results</h3>
      <div className="results-grid">
        {results.map((imageUrl, index) => (
          <img key={index} src={imageUrl} alt={`Result ${index + 1}`} className="result-image" />
        ))}
      </div>
    </div>
  );
};

export default SearchResults;


// the return must be like this
// {
//     "images": [
//       "http://master-ip:5000/static/result1.jpg",
//       "http://master-ip:5000/static/result2.jpg"
//     ]
//   }
  
/*
// import React from "react";

// function SearchResults({ results }) {
//   if (!results || results.length === 0) {
//     return null; 
//   }

//   return (
//     <div className="results-container">
//       <h3>Search Results</h3>
//       <pre className="results-text">{JSON.stringify(results, null, 2)}</pre>
//     </div>
//   );
// }

// export default SearchResults;
*/
