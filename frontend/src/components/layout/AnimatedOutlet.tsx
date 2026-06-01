import { AnimatePresence, motion } from "framer-motion";
import { Outlet, useLocation } from "react-router-dom";

import { pageTransition } from "./motion";

/** Route-overgangen met fade + blur (luxe pagina-wissel). */
export default function AnimatedOutlet() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        variants={pageTransition}
        initial="initial"
        animate="animate"
        exit="exit"
        style={{ width: "100%", minHeight: "1px" }}
      >
        <Outlet />
      </motion.div>
    </AnimatePresence>
  );
}
