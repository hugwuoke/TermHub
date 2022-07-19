import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from "react-router-dom";

import './index.css';
import {App, N3CObjectTypes, N3CObjectType, Else} from './App';
import AGtest from './aggrid-test'

// import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AGtest />}>
          <Route path="else" element={<Else />} />
          <Route path="objTypes" element={<N3CObjectTypes />}>
            <Route path=":objType" element={<N3CObjectType />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
);
/*
<React.StrictMode>
</React.StrictMode>
*/
// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
// reportWebVitals();


/*
https://reactjs.org/docs/error-boundaries.html
<ErrorBoundary>
</ErrorBoundary>
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI.
    return { hasError: true };
  }


  componentDidCatch(error, errorInfo) {
    // You can also log the error to an error reporting service
    // logErrorToMyService(error, errorInfo);
    console.log(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      // You can render any custom fallback UI
      return <h1>Something went wrong.</h1>;
    }

    return this.props.children;
  }
}
*/
