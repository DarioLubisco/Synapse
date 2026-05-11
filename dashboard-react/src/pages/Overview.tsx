import React from 'react';
import { Card, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { DollarSign, Package, AlertTriangle, Clock } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const data = [
  { name: 'Lun', entradas: 4000, salidas: 2400 },
  { name: 'Mar', entradas: 3000, salidas: 1398 },
  { name: 'Mié', entradas: 2000, salidas: 3800 },
  { name: 'Jue', entradas: 2780, salidas: 3908 },
  { name: 'Vie', entradas: 1890, salidas: 4800 },
  { name: 'Sáb', entradas: 2390, salidas: 3800 },
  { name: 'Dom', entradas: 3490, salidas: 4300 },
];

const Overview = () => {
  return (
    <div className="flex flex-col gap-6">
      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent>
            <div className="flex justify-between items-start mb-3">
              <div className="text-slate-500 text-sm font-medium">Valor del Inventario</div>
              <div className="p-2 bg-blue-50 text-blue-600 rounded-lg"><DollarSign size={18} /></div>
            </div>
            <div className="text-3xl font-bold mb-2">$124,500</div>
            <div className="text-sm font-medium text-emerald-500 flex items-center gap-1">
              ↑ 2.4% vs mes anterior
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent>
            <div className="flex justify-between items-start mb-3">
              <div className="text-slate-500 text-sm font-medium">Artículos en Stock</div>
              <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg"><Package size={18} /></div>
            </div>
            <div className="text-3xl font-bold mb-2">12,840</div>
            <div className="text-sm font-medium text-emerald-500 flex items-center gap-1">
              ↑ 145 items hoy
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="flex justify-between items-start mb-3">
              <div className="text-slate-500 text-sm font-medium">Stock Bajo / Crítico</div>
              <div className="p-2 bg-red-50 text-red-600 rounded-lg"><AlertTriangle size={18} /></div>
            </div>
            <div className="text-3xl font-bold mb-2">34</div>
            <div className="text-sm font-medium text-red-500 flex items-center gap-1">
              ↓ Requiere atención
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <div className="flex justify-between items-start mb-3">
              <div className="text-slate-500 text-sm font-medium">Órdenes Pendientes</div>
              <div className="p-2 bg-amber-50 text-amber-600 rounded-lg"><Clock size={18} /></div>
            </div>
            <div className="text-3xl font-bold mb-2">8</div>
            <div className="text-sm font-medium text-amber-500 flex items-center gap-1">
              → Estable
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart */}
        <Card className="lg:col-span-2">
          <CardContent>
            <h2 className="text-lg font-semibold mb-6">Movimiento de Inventario (Últimos 7 días)</h2>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorEntradas" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorSalidas" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748b' }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b' }} dx={-10} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '0.5rem', border: '1px solid #e2e8f0', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }}
                  />
                  <Area type="monotone" dataKey="entradas" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorEntradas)" />
                  <Area type="monotone" dataKey="salidas" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorSalidas)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Table */}
        <Card>
          <CardContent>
            <h2 className="text-lg font-semibold mb-6">Stock de Rápida Rotación</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="py-3 px-2 text-slate-500 font-medium text-sm">Producto</th>
                    <th className="py-3 px-2 text-slate-500 font-medium text-sm text-right">Stock</th>
                    <th className="py-3 px-2 text-slate-500 font-medium text-sm text-center">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-3 px-2 font-medium text-sm">Losartán 50mg</td>
                    <td className="py-3 px-2 text-sm text-right">450</td>
                    <td className="py-3 px-2 text-sm text-center"><Badge variant="success">Óptimo</Badge></td>
                  </tr>
                  <tr className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-3 px-2 font-medium text-sm">Azitromicina</td>
                    <td className="py-3 px-2 text-sm text-right">20</td>
                    <td className="py-3 px-2 text-sm text-center"><Badge variant="warning">Reordenar</Badge></td>
                  </tr>
                  <tr className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-3 px-2 font-medium text-sm">Ibuprofeno</td>
                    <td className="py-3 px-2 text-sm text-right">5</td>
                    <td className="py-3 px-2 text-sm text-center"><Badge variant="error">Crítico</Badge></td>
                  </tr>
                  <tr className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-3 px-2 font-medium text-sm">Paracetamol</td>
                    <td className="py-3 px-2 text-sm text-right">120</td>
                    <td className="py-3 px-2 text-sm text-center"><Badge variant="success">Óptimo</Badge></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Overview;
