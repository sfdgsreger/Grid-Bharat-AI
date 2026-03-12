import React from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import App from './App';

// Create router configuration for future expansion
const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
  },
  // Future routes can be added here:
  // {
  //   path: '/analytics',
  //   element: <AnalyticsPage />,
  // },
  // {
  //   path: '/settings',
  //   element: <SettingsPage />,
  // },
]);

export const AppRouter: React.FC = () => {
  return <RouterProvider router={router} />;
};

export default router;