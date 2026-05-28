import { HashRouter } from "react-router-dom";

import { UserProvider } from "./contexts/UserContext";
import Router from "./router/Router";

export default function App() {
  return (
    <HashRouter>
      <UserProvider>
        <Router />
      </UserProvider>
    </HashRouter>
  );
}
