import React, { useState } from "react";
import Editor from "./DocumentEditor";

const Uploader = () => {
  const [filename, setFilename] = useState(null);

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !file.name.endsWith(".docx")) {
      alert("Please upload a DOCX file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://20.109.20.242:6006/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (data.error) {
        alert("Upload failed.");
        return;
      }

      setFilename(data.filename);
    } catch (err) {
      console.error(err);
      alert("Upload failed.");
    }
  };

  return (
    <div style={{ height: "100%", width: "100%" }}>
      {!filename ? (
        <div
          style={{
            height: "100%",
            width: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "20px",
          }}
        >
          <h2>Upload DOCX file</h2>
          <input type="file" accept=".docx" onChange={handleUpload} />
        </div>
      ) : (
        <Editor filename={filename} />
      )}
    </div>
  );
};

export default Uploader;
