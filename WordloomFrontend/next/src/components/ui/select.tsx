// next/src/components/ui/select.tsx
import * as React from "react";
import { clsx as cn } from "clsx";

// 原生 <select> 只有 onChange。我们额外支持 onValueChange，向下兼容你现有调用。
type NativeProps = Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "onChange">;

export interface SelectProps extends NativeProps {
  /** 语义化回调：仅给出选中值 */
  onValueChange?: (value: string) => void;
  /** 如果你也传了 onChange，我们会先调它，再调 onValueChange */
  onChange?: React.SelectHTMLAttributes<HTMLSelectElement>["onChange"];
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, onValueChange, onChange, ...props }, ref) => {
    const handleChange = React.useCallback(
      (e: React.ChangeEvent<HTMLSelectElement>) => {
        onChange?.(e);                    // 先交还原始事件
        onValueChange?.(e.target.value);  // 再给简化值
      },
      [onChange, onValueChange]
    );

    return (
      <select
        ref={ref}
        className={cn(
          "h-9 rounded-md border border-gray-300 bg-white px-3 text-sm shadow-sm",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-black/20",
          "disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        onChange={handleChange}
        {...props}
      >
        {children}
      </select>
    );
  }
);
Select.displayName = "Select";
