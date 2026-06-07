/** Gedeelde Framer Motion presets — premium page feel */

/** Eén route-enter/exit — geen blur (botst met sectie-stagger). */
export const pageTransition = {
  initial: { opacity: 0, y: 10 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.32, ease: [0.22, 0.9, 0.26, 1] },
  },
  exit: {
    opacity: 0,
    y: -6,
    transition: { duration: 0.18, ease: [0.4, 0, 1, 1] },
  },
};

export const staggerContainer = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.07,
      delayChildren: 0.06,
    },
  },
};

/** Subtle shift only — opacity blijft 1 zodat route-fade niet dubbel voelt. */
export const staggerItem = {
  initial: { opacity: 1, y: 14 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.34, ease: [0.22, 0.9, 0.26, 1] },
  },
};
