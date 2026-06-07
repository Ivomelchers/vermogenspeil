import { useLayoutEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Outlet, useLocation } from "react-router-dom";

/**
 * Eén lichte fade-in bij navigatie — geen exit-animatie (voorkomt dubbele flits).
 */
export default function AnimatedOutlet() {
  const location = useLocation();
  const previousPath = useRef(location.pathname);
  const shouldAnimate = previousPath.current !== location.pathname;

  useLayoutEffect(() => {
    previousPath.current = location.pathname;
  }, [location.pathname]);

  return (
    <motion.div
      key={location.pathname}
      initial={shouldAnimate ? { opacity: 0.94 } : false}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2, ease: [0.22, 0.9, 0.26, 1] }}
      style={{ width: "100%" }}
    >
      <Outlet />
    </motion.div>
  );
}
