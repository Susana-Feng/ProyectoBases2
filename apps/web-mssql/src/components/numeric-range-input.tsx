import { Input } from "@/components/ui/input";

interface NumericRangeInputProps {
  minValue?: string;
  maxValue?: string;
  onMinChange: (value: string) => void;
  onMaxChange: (value: string) => void;
  onEnter?: () => void;
}

export function NumericRangeInput({
  minValue,
  maxValue,
  onMinChange,
  onMaxChange,
  onEnter,
}: NumericRangeInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && onEnter) {
      onEnter();
    }
  };

  const numberInputClasses =
    "h-8 [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-inner-spin-button]:-webkit-appearance-none [[type=number]]:appearance-none [[type=number]]:moz-appearance-textfield";

  return (
    <div className="space-y-2">
      <Input
        type="number"
        placeholder="Valor mínimo"
        value={minValue || ""}
        onChange={(e) => onMinChange(e.target.value)}
        onKeyDown={handleKeyDown}
        className={numberInputClasses}
      />
      <Input
        type="number"
        placeholder="Valor máximo"
        value={maxValue || ""}
        onChange={(e) => onMaxChange(e.target.value)}
        onKeyDown={handleKeyDown}
        className={numberInputClasses}
      />
    </div>
  );
}
