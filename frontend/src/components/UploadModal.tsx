import { useEffect, useState } from "react";

type Props = {
  file: File;
  defaultLabel?: string;
  busy: boolean;
  onCancel: () => void;
  onSubmit: (label: string) => void;
};

export function UploadModal({ file, defaultLabel, busy, onCancel, onSubmit }: Props) {
  const initial = defaultLabel || stripExt(file.name);
  const [label, setLabel] = useState(initial);

  useEffect(() => {
    setLabel(initial);
  }, [initial]);

  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Add a label</h3>
        <p>Give this document a short, recognisable name. The label is what the assistant will use when referencing it.</p>
        <div className="file-row">
          <strong>{file.name}</strong>
          <span style={{ marginLeft: 8 }}>({(file.size / 1024).toFixed(1)} KB)</span>
        </div>
        <label htmlFor="upload-label">Label</label>
        <input
          id="upload-label"
          type="text"
          autoFocus
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && label.trim()) onSubmit(label.trim());
          }}
        />
        <div className="modal-actions">
          <button className="btn" onClick={onCancel} disabled={busy}>Cancel</button>
          <button
            className="btn primary"
            onClick={() => onSubmit(label.trim() || stripExt(file.name))}
            disabled={busy || !label.trim()}
          >
            {busy ? "Uploading…" : "Upload"}
          </button>
        </div>
      </div>
    </div>
  );
}

function stripExt(name: string): string {
  const idx = name.lastIndexOf(".");
  return idx > 0 ? name.slice(0, idx) : name;
}
