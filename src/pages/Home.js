import React, { useState } from "react";
import ImageUpload from "../components/ImageUpload";
import SearchResults from "../components/SearchResults";
import "../styles/style.css"; 

function Home() {
  const [results, setResults] = useState(null);

  return (
    <div className="home-container">
      <h1>Circle-To-Search</h1>
      <div className="content-container">
      <div className="upload-section">
      <ImageUpload setResults={setResults} />
      </div>
      {results && results.length > 0 && (
        <div className="results-section">
          <SearchResults results={results} />
        </div>
      )}
      </div>
    </div>
  );
}

export default Home;




/* 
// import React, { useState } from "react";
// import ImageUpload from "../components/ImageUpload";
// import SearchResults from "../components/SearchResults";
// import "../styles/style.css"; // Ensure styles are applied

// function Home() {
//   const [results, setResults] = useState(null);

//   return (
//     <div className="home-container">
//       <h1>Circle-To-Search</h1>
//       <div className="upload-section">
//         <ImageUpload setResults={setResults} />
//       </div>
//       {results && results.length > 0 && (
//         <div className="results-section">
//           <SearchResults results={results} />
//         </div>
//       )}
//     </div>
//   );
// }

// export default Home;
*/