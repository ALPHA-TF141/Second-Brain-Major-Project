import React from 'react';
import ReactDOM from 'react-dom/client';
import { HashRouter } from 'react-router-dom';
import App from './App.jsx';
import { AssistantProvider } from './context/AssistantContext.jsx';
import { BackendProvider } from './context/BackendContext.jsx';
import './styles/index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <HashRouter>
      <BackendProvider>
        <AssistantProvider>
          <App />
        </AssistantProvider>
      </BackendProvider>
    </HashRouter>
  </React.StrictMode>
);
