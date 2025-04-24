import React, { useEffect } from "react";

const Editor = ({ filename }) => {
  useEffect(() => {
    const loadEditor = async () => {
      if (!DocsAPI || !DocsAPI.DocEditor) {
        console.error("❌ DocsAPI.DocEditor is not available.");
        return;
      }

      // const res = await fetch(`http://localhost:5000/config?filename=${filename}`);
      // const config = await res.json();
            // const config = await res.json();
            const config = {
              document: {
                fileType: "docx",
                key: "Khirz6zTPdfd7",
                title: "demo.docx",
                url: "https://calibre-ebook.com/downloads/demos/demo.docx",
              },
              documentType: "word",
              editorConfig: {
                callbackUrl: "http://20.109.20.242:6006/save/demo.docx",
              },
            };

      // Initialize the editor with DocsAPI.DocEditor
      new DocsAPI.DocEditor("onlyoffice-editor", config);
    };

    loadEditor();
  }, [filename]);

  return <div id="onlyoffice-editor" style={{ height: "100%", width: "100%" }} />;
};

export default Editor;
