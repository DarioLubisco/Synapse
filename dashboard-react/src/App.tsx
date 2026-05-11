import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import Overview from './pages/Overview';
import Inventario from './pages/Inventario';
import Movimientos from './pages/Movimientos';
import Proveedores from './pages/Proveedores';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Overview />} />
          <Route path="inventario" element={<Inventario />} />
          <Route path="movimientos" element={<Movimientos />} />
          <Route path="proveedores" element={<Proveedores />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
