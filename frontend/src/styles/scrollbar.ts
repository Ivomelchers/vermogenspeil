import type { SystemStyleObject } from "@chakra-ui/react";

/** Scrollable area without visible scrollbar (main app content). */
export function hideScrollbarSx(): SystemStyleObject {
  return {
    scrollbarWidth: "none",
    msOverflowStyle: "none",
    "&::-webkit-scrollbar": {
      display: "none",
      width: 0,
      height: 0,
    },
  };
}

/** Themed scrollbar — azure/line palette, matches Verbox fiscal UI. */
export function fiscalScrollbarSx(
  orientation: "vertical" | "horizontal" = "vertical",
): SystemStyleObject {
  const isVertical = orientation === "vertical";

  return {
    scrollbarWidth: "thin",
    scrollbarColor: "var(--chakra-colors-azure-300) var(--chakra-colors-line-soft)",
    "&::-webkit-scrollbar": {
      width: isVertical ? "8px" : undefined,
      height: isVertical ? undefined : "6px",
    },
    "&::-webkit-scrollbar-button": {
      display: "none",
      width: 0,
      height: 0,
    },
    "&::-webkit-scrollbar-track": {
      background: "var(--chakra-colors-line-soft)",
      borderRadius: "4px",
    },
    "&::-webkit-scrollbar-thumb": {
      background: "var(--chakra-colors-line-DEFAULT)",
      borderRadius: "4px",
      border: "2px solid var(--chakra-colors-line-soft)",
    },
    "&::-webkit-scrollbar-thumb:hover": {
      background: "var(--chakra-colors-azure-400)",
    },
  };
}
