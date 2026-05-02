import { clsx } from "clsx";

interface BaseProps {
  label: string;
  description?: string;
}

interface TextProps extends BaseProps {
  type: "text" | "number";
  value: string | number;
  onChange: (v: string) => void;
  placeholder?: string;
  min?: number;
  max?: number;
}

interface ToggleProps extends BaseProps {
  type: "toggle";
  value: boolean;
  onChange: (v: boolean) => void;
}

interface SliderProps extends BaseProps {
  type: "slider";
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  unit?: string;
}

interface SelectProps extends BaseProps {
  type: "select";
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}

type Props = TextProps | ToggleProps | SliderProps | SelectProps;

export default function SettingsRow(props: Props) {
  return (
    <div className="flex items-center justify-between gap-4 py-3 border-b border-white/5 last:border-0">
      <div className="min-w-0">
        <p className="text-sm font-medium text-white">{props.label}</p>
        {props.description && (
          <p className="text-xs text-gray-500 mt-0.5">{props.description}</p>
        )}
      </div>

      <div className="shrink-0">
        {props.type === "toggle" && (
          <button
            onClick={() => props.onChange(!props.value)}
            className={clsx(
              "relative w-11 h-6 rounded-full transition-colors",
              props.value ? "bg-pixartek-accent" : "bg-white/20"
            )}
          >
            <span className={clsx(
              "absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform",
              props.value ? "translate-x-5" : "translate-x-0"
            )} />
          </button>
        )}

        {(props.type === "text" || props.type === "number") && (
          <input
            type={props.type}
            value={props.value}
            onChange={e => props.onChange(e.target.value)}
            placeholder={props.placeholder}
            min={props.type === "number" ? props.min : undefined}
            max={props.type === "number" ? props.max : undefined}
            className="bg-white/10 border border-white/20 rounded-lg px-3 py-1.5 text-sm text-white w-40 focus:outline-none focus:border-pixartek-accent transition"
          />
        )}

        {props.type === "slider" && (
          <div className="flex items-center gap-3 w-48">
            <input
              type="range"
              min={props.min}
              max={props.max}
              value={props.value}
              onChange={e => props.onChange(Number(e.target.value))}
              className="flex-1 accent-pixartek-accent"
            />
            <span className="text-sm text-gray-300 w-10 text-right">
              {props.value}{props.unit ?? ""}
            </span>
          </div>
        )}

        {props.type === "select" && (
          <select
            value={props.value}
            onChange={e => props.onChange(e.target.value)}
            className="bg-white/10 border border-white/20 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-pixartek-accent transition"
          >
            {props.options.map(o => (
              <option key={o.value} value={o.value} className="bg-pixartek-ink">
                {o.label}
              </option>
            ))}
          </select>
        )}
      </div>
    </div>
  );
}
