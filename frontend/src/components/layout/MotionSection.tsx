import { motion, type HTMLMotionProps } from "framer-motion";

import { staggerItem } from "./motion";

/** Gestaggerde sectie binnen een pagina. */
export default function MotionSection(props: HTMLMotionProps<"div">) {
  return <motion.div variants={staggerItem} {...props} />;
}
