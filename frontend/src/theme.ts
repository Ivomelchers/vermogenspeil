import { extendTheme, type ThemeConfig } from "@chakra-ui/react";

const transition = "0.15s ease";

const colors = {
  background: "#FAFAF7",
  backgroundCard: "#F3F1EC",
  backgroundHover: "#E8E5DD",
  paper: "#FFFFFF",
  ink: {
    primary: "#14213D",
    dim: "#4A5878",
    faint: "#8892A6",
  },
  line: {
    DEFAULT: "#D6D3CA",
    soft: "#E4E1D7",
  },
  azure: {
    50: "rgba(30, 58, 95, 0.04)",
    100: "rgba(30, 58, 95, 0.08)",
    200: "rgba(30, 58, 95, 0.15)",
    300: "rgba(30, 58, 95, 0.25)",
    400: "#2C4D7A",
    500: "#1E3A5F",
    600: "#2C4D7A",
    700: "#102542",
  },
  gold: {
    50: "rgba(184, 147, 78, 0.06)",
    100: "rgba(184, 147, 78, 0.10)",
    500: "#B8934E",
    600: "#CBA461",
  },
  moss: {
    50: "rgba(74, 122, 78, 0.10)",
    500: "#4A7A4E",
  },
  rust: {
    50: "rgba(139, 58, 42, 0.10)",
    500: "#8B3A2A",
  },
  taupe: {
    50: "rgba(107, 111, 122, 0.10)",
    500: "#6B6F7A",
  },
};

const ambientGradient =
  "radial-gradient(ellipse at 20% 10%, rgba(30, 58, 95, 0.04), transparent 50%), radial-gradient(ellipse at 85% 80%, rgba(107, 142, 90, 0.03), transparent 50%)";

const paperNoise =
  "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3'/%3E%3CfeColorMatrix values='0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0.04 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")";

const config: ThemeConfig = {
  initialColorMode: "light",
  useSystemColorMode: false,
};

const theme = extendTheme({
  config,
  colors,
  fonts: {
    heading: "'Source Serif 4', Georgia, serif",
    body: "'Inter', system-ui, sans-serif",
  },
  fontSizes: {
    kicker: "10px",
    meta: "11px",
    body: "14px",
  },
  radii: {
    none: "0",
    sm: "2px",
    base: "4px",
    md: "4px",
    lg: "4px",
    full: "9999px",
  },
  shadows: {
    sm: "0 1px 2px rgba(20, 33, 61, 0.04)",
    md: "0 1px 2px rgba(20, 33, 61, 0.04), 0 12px 32px -16px rgba(20, 33, 61, 0.18)",
    outline: "none",
  },
  styles: {
    global: {
      "*, *::before, *::after": {
        boxSizing: "border-box",
      },
      "html, body, #root": {
        minH: "100vh",
      },
      body: {
        bg: "background",
        color: "ink.primary",
        fontFamily: "body",
        WebkitFontSmoothing: "antialiased",
        MozOsxFontSmoothing: "grayscale",
        overflowX: "hidden",
      },
      "a, button": {
        transition: `color ${transition}, background ${transition}, border-color ${transition}`,
      },
      ".app-shell": {
        position: "relative",
        zIndex: 2,
        minH: "100vh",
      },
      ".app-shell::before": {
        content: '""',
        position: "fixed",
        inset: 0,
        backgroundImage: ambientGradient,
        pointerEvents: "none",
        zIndex: 0,
      },
      ".app-shell::after": {
        content: '""',
        position: "fixed",
        inset: 0,
        backgroundImage: paperNoise,
        opacity: 0.5,
        pointerEvents: "none",
        zIndex: 1,
        mixBlendMode: "overlay",
      },
    },
  },
  components: {
    Heading: {
      baseStyle: {
        fontFamily: "heading",
        fontWeight: 400,
        color: "ink.primary",
        letterSpacing: "-0.01em",
      },
    },
    Text: {
      baseStyle: {
        color: "ink.primary",
      },
    },
    Link: {
      baseStyle: {
        _hover: {
          textDecoration: "none",
        },
      },
    },
    Button: {
      baseStyle: {
        fontFamily: "body",
        fontWeight: 500,
        borderRadius: "base",
        transition: `background ${transition}, border-color ${transition}, color ${transition}`,
      },
      variants: {
        fiscal: {
          bg: "azure.500",
          color: "paper",
          border: "1px solid",
          borderColor: "azure.500",
          _hover: {
            bg: "azure.600",
            borderColor: "azure.600",
          },
        },
        fiscalOutline: {
          bg: "transparent",
          color: "azure.500",
          border: "1px solid",
          borderColor: "line.DEFAULT",
          _hover: {
            color: "azure.500",
            borderColor: "azure.500",
            bg: "azure.50",
          },
        },
        premium: {
          bg: "gold.500",
          color: "paper",
          border: "1px solid",
          borderColor: "gold.500",
          _hover: {
            bg: "gold.600",
            borderColor: "gold.600",
          },
        },
        ghostNav: {
          justifyContent: "flex-start",
          w: "full",
          h: "auto",
          py: 2.5,
          px: 3,
          fontWeight: 400,
          fontSize: "body",
          color: "ink.dim",
          bg: "transparent",
          _hover: {
            color: "ink.primary",
            bg: "backgroundHover",
          },
        },
      },
    },
    Badge: {
      variants: {
        premium: {
          bg: "gold.100",
          color: "gold.500",
          border: "1px solid",
          borderColor: "gold.500",
          borderRadius: "sm",
          fontFamily: "body",
          fontSize: "kicker",
          fontWeight: 600,
          letterSpacing: "0.12em",
          textTransform: "uppercase",
          px: 2,
          py: 0.5,
        },
      },
    },
    Card: {
      baseStyle: {
        container: {
          bg: "backgroundCard",
          borderColor: "line.DEFAULT",
          borderWidth: "1px",
          borderRadius: "base",
          boxShadow: "none",
        },
      },
    },
    Input: {
      variants: {
        fiscal: {
          field: {
            bg: "paper",
            border: "1px solid",
            borderColor: "line.DEFAULT",
            borderRadius: "base",
            fontSize: "body",
            h: "42px",
            _placeholder: { color: "ink.faint" },
            _hover: { borderColor: "taupe.500" },
            _focusVisible: {
              borderColor: "azure.500",
              boxShadow: "none",
            },
          },
        },
      },
      defaultProps: {
        variant: "fiscal",
      },
    },
    Checkbox: {
      baseStyle: {
        control: {
          borderColor: "line.DEFAULT",
          borderRadius: "sm",
          _checked: {
            bg: "azure.500",
            borderColor: "azure.500",
            _hover: {
              bg: "azure.600",
              borderColor: "azure.600",
            },
          },
        },
      },
    },
  },
});

export default theme;
