import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { createTheme, CssBaseline, ThemeProvider } from "@mui/material";
import App from "./App";
import "./styles.css";

const theme = createTheme({
  palette: { primary: { main: "#0f766e" }, secondary: { main: "#365314" }, background: { default: "#f7f8f7", paper: "#ffffff" } },
  typography: { fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif', button: { textTransform: "none", fontWeight: 700 } },
  shape: { borderRadius: 6 },
});

createRoot(document.getElementById("root")!).render(<StrictMode><ThemeProvider theme={theme}><CssBaseline /><QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } } })}><BrowserRouter><App /></BrowserRouter></QueryClientProvider></ThemeProvider></StrictMode>);
