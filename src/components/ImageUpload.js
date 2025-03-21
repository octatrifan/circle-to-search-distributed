import React, { useState, useRef } from "react";
import axios from "axios";
import "../styles/style.css";
//import test1 from "../images/test1.png";
import ReactCrop, {
  centerCrop,
  convertToPixelCrop,
  makeAspectCrop,
} from 'react-image-crop'
import 'react-image-crop/dist/ReactCrop.css'
import setCanvasPreview from "./setCanvasPreview";


function ImageUpload({ setResults }) {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [crop, setCrop] = useState(null);
  const ASPECT_RATIO = 1;
  const MIN_DIMENSION = 150;
  const imgRef = useRef(null);
  const previewCanvasRef = useRef(null);
  const [selectedImages, setSelectedImages] = useState([]);
  const serverurl = "http://127.0.0.1:5000";

  const handleImageSlecet = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      setPreview(URL.createObjectURL(file));
    }
    console.log("Selected File:", file);
  };
const handleSearch = async () => {
  if (!image) {
      setUploadStatus("Please select an image first for search.");
      return;
  }
  
  setUploadStatus("Processing image...");
  
  try {
      const croppedBlob = await getCroppedImage();
      
      // Convert Blob to Base64
      const base64Image = await convertBlobToBase64(croppedBlob);
      console.log(base64Image);
      
      setUploadStatus("Uploading...");

      const payload = {
          image: base64Image,  
      };

      const response = await axios.post(
          serverurl + "/image_search",
          payload,  // Send as JSON
          { headers: { "Content-Type": "application/json" } }
      );

      console.log("Backend Response:", response.data);

      if (response.data && response.data.images) {
          setResults(response.data.images);
          setUploadStatus("Upload successful!");
      } else {
          setUploadStatus("Error: No images found in response.");
      }
  } catch (error) {
      console.error("Error uploading image:", error);
      setUploadStatus("Upload failed. Please try again.");
  }
};

const convertBlobToBase64 = (blob) => {
  return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(blob);
      reader.onloadend = () => resolve(reader.result); // Base64 string
      reader.onerror = reject;
  });
};

  // now this function test the searchresult.js by sending only path, the "101_ObjectCategories" must be inside the public folder
  // circle-to-search-distributed ==> public, src, hdf5_files .. and so on
  const localTest = () => {
    const localImages = [
      "./101_ObjectCategories/camera/image_0036.jpg",
      "./101_ObjectCategories/camera/image_0014.jpg",
      "./101_ObjectCategories/camera/image_0001.jpg",
      "./101_ObjectCategories/camera/image_0029.jpg",
      "./101_ObjectCategories/camera/image_0005.jpg"
    ];
  
    console.log("Local test images loaded:", localImages);
    setResults(localImages);
  };
  // const localTest = async () => {
  //   try {
  //     const croppedBlob = await getCroppedImage();
  //     const croppedImageUrl = URL.createObjectURL(croppedBlob);

  //     const localImages = [croppedImageUrl, croppedImageUrl, croppedImageUrl, croppedImageUrl, croppedImageUrl, croppedImageUrl];
  //     console.log("Local test images loaded:", localImages);
  //     setResults(localImages);
  //   } catch (error) {
  //     console.error("Error in localTest:", error);
  //   }
  // };
  const getCroppedImage = async () => {
    return new Promise((resolve, reject) => {
      if (!imgRef.current || !crop) {
        console.error("No image or crop selection.");
        reject(new Error("No image or crop selection."));
        return;
      }
      const canvas = document.createElement("canvas");
      setCanvasPreview(
        imgRef.current, 
        canvas, 
        convertToPixelCrop(
          crop,
          imgRef.current.width,
          imgRef.current.height
        )
      );
      canvas.toBlob((blob) => {
        if (!blob) {
          console.error("Canvas is empty.");
          reject(new Error("Canvas is empty"));
          return;
        }
        resolve(blob); 
      }, "image/png");
    });
  };
  const onImageLoad = (e) => {
    const { width, height } = e.currentTarget;
    const cropWidthInPercent = (MIN_DIMENSION / width) * 100;

    const crop = makeAspectCrop(
      {
        unit: "%",
        width: cropWidthInPercent,
      },
      ASPECT_RATIO,
      width,
      height
    );
    const centeredCrop = centerCrop(crop, width, height);
    setCrop(centeredCrop);
  };
  const handleMultipleImageSelect = (e) => {
    const files = Array.from(e.target.files);
    setSelectedImages(files);
    console.log("Selected images for upload:", files);
  };
const uploadImages = async () => {
  if (selectedImages.length === 0) {
      setUploadStatus("Please select images first for upload.");
      return;
  }

  setUploadStatus("Processing images...");

  try {
      // Convert all selected images to Base64
      const base64Images = await Promise.all(
          selectedImages.map((file) => convertFileToBase64(file))
      );
      console.log(base64Images);
      setUploadStatus("Uploading images...");

      const payload = {
          images: base64Images, // Send an array of Base64 strings
      };

      const response = await axios.post(
          serverurl + "/insert_images",
          payload,  // Send as JSON
          { headers: { "Content-Type": "application/json" } }
      );

      console.log("Uploaded Images Response:", response.data);
      setUploadStatus("Images uploaded successfully!");
  } catch (error) {
      console.error("Error uploading images:", error);
      setUploadStatus("Image upload failed. Please try again.");
  }
};

const convertFileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onloadend = () => resolve(reader.result); // Base64 string
      reader.onerror = reject;
  });
};
  

  return (

    <div className="upload-card">
      <h2>Upload an Image</h2>
      <input type="file" accept="image/*" onChange={handleImageSlecet} className="file-input" />
      <ReactCrop crop={crop}
        onChange={(pixelCrop, percentCrop) => setCrop(percentCrop)}
        circularCrop
        keepSelection
        aspect={ASPECT_RATIO}
        minWidth={MIN_DIMENSION}>
        {preview && <img src={preview} ref={imgRef} alt="Preview" className="image-preview" onLoad={onImageLoad} />}
      </ReactCrop>
      <button onClick={handleSearch} className="upload-button">Search</button>
      <button onClick={localTest} className="upload-button">local test</button>
      <input type="file" accept="image/*" multiple onChange={handleMultipleImageSelect} className="file-input" />
      <button onClick={uploadImages} className="upload-button">Upload Images</button>
      <p className="upload-status">{uploadStatus}</p>
      <canvas ref={previewCanvasRef} style={{ display: "none" }} />
    </div>

  );
}

export default ImageUpload;


/* CODE BEFORE CROP IT WORKS %100
function ImageUpload({ setResults }) {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      setPreview(URL.createObjectURL(file));
    }
  };

  const handleUpload = async () => {
    if (!image) {
      setUploadStatus("Please select an image first.");
      return;
    }

    setUploadStatus("Uploading...");
    const formData = new FormData();
    formData.append("image", image);

    try {
      const response = await axios.post(
        process.env.BACKEND_URL + "/upload",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      console.log("Backend Response:", response.data);

      if (response.data && response.data.images) {
        setResults(response.data.images); 
        setUploadStatus("Upload successful!");
      } else {
        setUploadStatus("Error: No images found in response.");
      }
    } catch (error) {
      console.error("Error uploading image:", error);
      setUploadStatus("Upload failed. Please try again.");
    }
  };

  const localTest = () => {
    const localImages = [test1, test1, test1, test1, test1, test1];
    console.log("Local test images loaded:", localImages);
    setResults(localImages);
  }
  return (

    <div className="upload-card">
      <h2>Upload an Image</h2>
      <input type="file" accept="image/*" onChange={handleImageChange} className="file-input" />
      {preview && <img src={preview} alt="Preview" className="image-preview" />}
      <button onClick={handleUpload} className="upload-button">Upload</button>
      <button onClick={localTest} className="upload-button">local test</button>
      <p className="upload-status">{uploadStatus}</p>
    </div>

  );
}

export default ImageUpload;
*/
