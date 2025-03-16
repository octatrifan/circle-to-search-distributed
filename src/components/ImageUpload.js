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
    const croppedBlob = await getCroppedImage();
    setUploadStatus("Uploading...");
    const formData = new FormData();
    const imageFile = new File([croppedBlob], "cropped-image.jpg", { type: "image/jpeg" });
    formData.append("image", imageFile);
    // console.log(formData);
    // console.log("Uploading image:", croppedBlob);
    // console.log("FormData entries:");
    // for (let pair of formData.entries()) {
    //   console.log(pair[0], pair[1]); 
    // }

    try {
      const response = await axios.post(
        serverurl + "/image_search",
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
  const localTest = async () => {
    try {
      const croppedBlob = await getCroppedImage();
      const croppedImageUrl = URL.createObjectURL(croppedBlob);

      const localImages = [croppedImageUrl, croppedImageUrl, croppedImageUrl, croppedImageUrl, croppedImageUrl, croppedImageUrl];
      console.log("Local test images loaded:", localImages);
      setResults(localImages);
    } catch (error) {
      console.error("Error in localTest:", error);
    }
  };
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
  
    setUploadStatus("Uploading images...");
    const formData = new FormData();
    selectedImages.forEach((image) => {
      formData.append("images", image);
    });
    // selectedImages.forEach((image, index) => {
    //   formData.append(`image${index}`, image);
    // });
    //console.log(selectedImages);
    //console.log("FormData entries:");
    // for (let pair of formData.entries()) {
    //    console.log(pair[0], pair[1]); 
    //  }
    try {
      const response = await axios.post(
        serverurl + "/insert_images",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
  
      console.log("Uploaded Images Response:", response.data);
      setUploadStatus("Images uploaded successfully!");
    } catch (error) {
      console.error("Error uploading images:", error);
      setUploadStatus("Image upload failed. Please try again.");
    }
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
