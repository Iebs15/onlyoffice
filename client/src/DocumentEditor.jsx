import React, { useEffect } from "react";

const Editor = ({ filename }) => {
  useEffect(() => {
    const loadEditor = async () => {
      const res = await fetch("http://20.109.20.242:6006/onlyoffice-config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename }),
      });

      const config = await res.json();

      if (!DocsAPI || !DocsAPI.DocEditor) {
        console.error("❌ DocsAPI is not available.");
        return;
      }

      new DocsAPI.DocEditor("onlyoffice-editor", config);
    };

    if (filename) {
      loadEditor();
    }
  }, [filename]);

  return <div id="onlyoffice-editor" style={{ height: "1000px", width: "1000px" }} />;
};

export default Editor;
