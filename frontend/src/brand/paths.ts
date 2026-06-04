/** Publieke brand-assets (onder `/brand/` na build). */
export const brandPaths = {
  favicon: "/brand/icon-tile.svg",
  iconTile: "/brand/icon-tile.svg",
  mark: "/brand/mark/mark.svg",
  markReversed: "/brand/mark/mark-reversed.svg",
  wordmark: "/brand/wordmark/wordmark.svg",
  wordmarkReversed: "/brand/wordmark/wordmark-reversed.svg",
  logoHorizontal: "/brand/logo/horizontal.svg",
  logoHorizontalReversed: "/brand/logo/horizontal-reversed.svg",
  logoStacked: "/brand/logo/stacked.svg",
  tagline: "/brand/tagline/tagline.svg",
  taglineReversed: "/brand/tagline/tagline-reversed.svg",
} as const;

export type BrandLogoVariant = "horizontal" | "stacked" | "mark" | "wordmark";

export function logoSrc(variant: BrandLogoVariant, reversed = false): string {
  switch (variant) {
    case "horizontal":
      return reversed ? brandPaths.logoHorizontalReversed : brandPaths.logoHorizontal;
    case "stacked":
      return brandPaths.logoStacked;
    case "mark":
      return reversed ? brandPaths.markReversed : brandPaths.mark;
    case "wordmark":
      return reversed ? brandPaths.wordmarkReversed : brandPaths.wordmark;
  }
}
