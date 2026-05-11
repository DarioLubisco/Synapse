import React from 'react';
import { Input } from './ui/Input';

const Header = () => {
  return (
    <header className="bg-white px-8 py-4 border-b border-slate-200 flex justify-between items-center sticky top-0 z-10">
      <h1 className="text-xl font-semibold m-0">Dashboard Operativo</h1>
      <div className="flex items-center gap-6">
        <div className="w-64">
          <Input 
            type="text" 
            placeholder="Buscar SKU, producto..." 
            fullWidth
          />
        </div>
        <div className="flex items-center gap-3 cursor-pointer">
          <div className="w-9 h-9 rounded-full bg-blue-500 text-white flex items-center justify-center font-semibold text-sm">
            DL
          </div>
          <span className="font-medium text-sm">Dario Lubisco</span>
        </div>
      </div>
    </header>
  );
};

export default Header;
