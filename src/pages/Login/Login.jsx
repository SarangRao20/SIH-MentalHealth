import React, { useState } from "react";
import "./Login.css";

const Login = () => {
  const [authMode, setAuthMode] = useState("Sign In");

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log(`${authMode} submitted`);
  };

  return (
    <div className="auth-container">
      <div className="auth-form">
        <h1 className="auth-title">{authMode}</h1>

        <form onSubmit={handleSubmit}>
          {authMode === "Sign Up" && (
            <input type="text" placeholder="Your Name" required />
          )}

          <input type="email" placeholder="Email" required />
          <input type="password" placeholder="Password" required />

          <button type="submit" className="auth-btn">
            {authMode}
          </button>

          <div className="auth-help">
            <label>
              <input type="checkbox" /> Remember Me
            </label>
            <p className="auth-link">Need Help?</p>
          </div>
        </form>

        <div className="auth-switch">
          {authMode === "Sign In" ? (
            <p>
              Don’t have an account?{" "}
              <span onClick={() => setAuthMode("Sign Up")}>Sign Up</span>
            </p>
          ) : (
            <p>
              Already have an account?{" "}
              <span onClick={() => setAuthMode("Sign In")}>Sign In</span>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Login;
