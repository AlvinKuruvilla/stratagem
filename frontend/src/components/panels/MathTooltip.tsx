import { useEffect, useRef } from "react";
import katex from "katex";

interface MathTooltipProps {
  latex: string;
  block?: boolean;
}

export default function MathTooltip({ latex, block = false }: MathTooltipProps) {
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (ref.current) {
      katex.render(latex, ref.current, {
        throwOnError: false,
        displayMode: block,
      });
    }
  }, [latex, block]);

  return <span ref={ref} />;
}
