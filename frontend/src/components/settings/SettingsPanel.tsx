import { useSettingsStore } from "@/context";
import { TOP_K_MAX, TOP_K_MIN } from "@/types";

export function SettingsPanel() {
  const { topK, temperature, modelName, setTopK } = useSettingsStore();

  return (
    <div className="settings-panel">
      <div className="settings-field">
        <label htmlFor="top-k">
          Top K <span className="settings-value">{topK}</span>
        </label>
        <input
          id="top-k"
          type="range"
          min={TOP_K_MIN}
          max={TOP_K_MAX}
          step={1}
          value={topK}
          onChange={(e) => setTopK(Number(e.target.value))}
        />
        <p className="settings-hint">Max number of sources shown per answer.</p>
      </div>

      <div className="settings-field settings-field-disabled">
        <label htmlFor="temperature">
          Temperature <span className="settings-value">{temperature.toFixed(1)}</span>
        </label>
        <input id="temperature" type="range" min={0} max={2} step={0.1} value={temperature} disabled readOnly />
        <p className="settings-hint">Coming soon — not yet wired to the backend.</p>
      </div>

      <div className="settings-field settings-field-disabled">
        <label htmlFor="model-name">Model</label>
        <input id="model-name" type="text" value={modelName} disabled readOnly />
        <p className="settings-hint">Coming soon — configured server-side today.</p>
      </div>
    </div>
  );
}
