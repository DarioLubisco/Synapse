import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Package, ArrowRightLeft, Users, Settings } from 'lucide-react';

const Sidebar = () => {
  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col sticky top-0 h-screen">
      <div className="p-6 text-xl font-bold text-blue-500 flex items-center gap-3 border-b border-slate-200">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
          <span className="text-white text-lg font-black leading-none">S</span>
        </div>
        Synapse
      </div>
      <nav className="p-4 flex flex-col gap-2 flex-1">
        <NavLink 
          to="/" 
          className={({ isActive }) => 
            `flex items-center gap-3 p-3 rounded-lg font-semibold transition-colors ${
              isActive 
                ? 'bg-blue-50 text-blue-600' 
                : 'text-slate-500 font-medium hover:bg-slate-100 hover:text-slate-900'
            }`
          }
        >
          <LayoutDashboard size={20} />
          Overview
        </NavLink>
        <NavLink 
          to="/inventario" 
          className={({ isActive }) => 
            `flex items-center gap-3 p-3 rounded-lg font-semibold transition-colors ${
              isActive 
                ? 'bg-blue-50 text-blue-600' 
                : 'text-slate-500 font-medium hover:bg-slate-100 hover:text-slate-900'
            }`
          }
        >
          <Package size={20} />
          Inventario
        </NavLink>
        <NavLink 
          to="/movimientos" 
          className={({ isActive }) => 
            `flex items-center gap-3 p-3 rounded-lg font-semibold transition-colors ${
              isActive 
                ? 'bg-blue-50 text-blue-600' 
                : 'text-slate-500 font-medium hover:bg-slate-100 hover:text-slate-900'
            }`
          }
        >
          <ArrowRightLeft size={20} />
          Movimientos
        </NavLink>
        <NavLink 
          to="/proveedores" 
          className={({ isActive }) => 
            `flex items-center gap-3 p-3 rounded-lg font-semibold transition-colors ${
              isActive 
                ? 'bg-blue-50 text-blue-600' 
                : 'text-slate-500 font-medium hover:bg-slate-100 hover:text-slate-900'
            }`
          }
        >
          <Users size={20} />
          Proveedores
        </NavLink>
      </nav>
      <div className="p-4 border-t border-slate-200">
        <button className="flex items-center gap-3 p-3 rounded-lg text-slate-500 font-medium hover:bg-slate-100 hover:text-slate-900 transition-colors w-full">
          <Settings size={20} />
          Ajustes
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
