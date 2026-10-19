import { Link, useNavigate } from "react-router-dom";
import { getUser } from "../utils";

export default function Layout({ children }) {
  const user = getUser();
  const navigate = useNavigate();

  function logout() {
    localStorage.removeItem("access_token");
    navigate("/");
  }

  return (
    <div className="app">
      <header className="navbar">
        <Link to="/" className="brand">Yaqeen</Link>
        <nav>
          {user?.role === "borrower" && (
            <>
              <Link to="/borrower">My Application</Link>
              <Link to="/apply">Apply</Link>
            </>
          )}
          {user?.role === "officer" && <Link to="/officer">Dashboard</Link>}
          {user ? (
            <button className="link" onClick={logout}>Logout</button>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <Link to="/signup">Sign up</Link>
              <Link to="/officer-login">Officer login</Link>
            </>
          )}
        </nav>
      </header>
      <main className="container">{children}</main>
    </div>
  );
}
