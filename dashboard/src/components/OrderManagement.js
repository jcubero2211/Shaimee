import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle 
} from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from './ui/table';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger 
} from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from './ui/select';
import { 
  Package, 
  Truck, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  Plus,
  Eye,
  Edit,
  Trash2,
  Download,
  Upload
} from 'lucide-react';
import { toast } from 'react-hot-toast';

const OrderManagement = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showOrderDetails, setShowOrderDetails] = useState(false);
  const [showCreatePickup, setShowCreatePickup] = useState(false);
  const [pickupForm, setPickupForm] = useState({
    tracking_number: '',
    weight: '',
    description: '',
    declared_value: '',
    recipient_name: '',
    recipient_phone: '',
    delivery_address: '',
    pickup_date: ''
  });

  // Estados para filtros
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('all');

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/orders');
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
      toast.error('Error al cargar las órdenes');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePickupOrder = async () => {
    try {
      const response = await axios.post('/api/correos/pickup-orders', pickupForm);
      
      if (response.data.success) {
        toast.success('Orden de recogida creada exitosamente');
        setShowCreatePickup(false);
        setPickupForm({
          tracking_number: '',
          weight: '',
          description: '',
          declared_value: '',
          recipient_name: '',
          recipient_phone: '',
          delivery_address: '',
          pickup_date: ''
        });
        fetchOrders(); // Recargar órdenes
      }
    } catch (error) {
      console.error('Error creating pickup order:', error);
      toast.error('Error al crear la orden de recogida');
    }
  };

  const handleUpdateOrderStatus = async (orderId, newStatus) => {
    try {
      const response = await axios.patch(`/api/orders/${orderId}/status`, {
        status: newStatus
      });
      
      if (response.data.success) {
        toast.success('Estado de orden actualizado');
        fetchOrders();
      }
    } catch (error) {
      console.error('Error updating order status:', error);
      toast.error('Error al actualizar el estado');
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      'pending': { color: 'bg-yellow-100 text-yellow-800', icon: Clock },
      'processing': { color: 'bg-blue-100 text-blue-800', icon: Package },
      'shipped': { color: 'bg-purple-100 text-purple-800', icon: Truck },
      'delivered': { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      'cancelled': { color: 'bg-red-100 text-red-800', icon: AlertCircle }
    };

    const config = statusConfig[status] || statusConfig['pending'];
    const Icon = config.icon;

    return (
      <Badge className={config.color}>
        <Icon className="w-3 h-3 mr-1" />
        {status}
      </Badge>
    );
  };

  const filteredOrders = orders.filter(order => {
    const statusMatch = statusFilter === 'all' || order.status === statusFilter;
    const dateMatch = dateFilter === 'all' || true; // Implementar filtro de fecha
    return statusMatch && dateMatch;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Gestión de Órdenes</h1>
          <p className="text-gray-600">Administra las órdenes y genera órdenes de recogida</p>
        </div>
        
        <div className="flex gap-2">
          <Dialog open={showCreatePickup} onOpenChange={setShowCreatePickup}>
            <DialogTrigger asChild>
              <Button className="bg-green-600 hover:bg-green-700">
                <Plus className="w-4 h-4 mr-2" />
                Crear Orden de Recogida
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Crear Orden de Recogida</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="tracking_number">Número de Seguimiento</Label>
                  <Input
                    id="tracking_number"
                    value={pickupForm.tracking_number}
                    onChange={(e) => setPickupForm({...pickupForm, tracking_number: e.target.value})}
                    placeholder="CR123456"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="weight">Peso (kg)</Label>
                    <Input
                      id="weight"
                      type="number"
                      value={pickupForm.weight}
                      onChange={(e) => setPickupForm({...pickupForm, weight: e.target.value})}
                      placeholder="1.5"
                    />
                  </div>
                  <div>
                    <Label htmlFor="declared_value">Valor Declarado</Label>
                    <Input
                      id="declared_value"
                      type="number"
                      value={pickupForm.declared_value}
                      onChange={(e) => setPickupForm({...pickupForm, declared_value: e.target.value})}
                      placeholder="25000"
                    />
                  </div>
                </div>
                
                <div>
                  <Label htmlFor="description">Descripción</Label>
                  <Textarea
                    id="description"
                    value={pickupForm.description}
                    onChange={(e) => setPickupForm({...pickupForm, description: e.target.value})}
                    placeholder="Descripción del paquete"
                  />
                </div>
                
                <div>
                  <Label htmlFor="recipient_name">Nombre del Destinatario</Label>
                  <Input
                    id="recipient_name"
                    value={pickupForm.recipient_name}
                    onChange={(e) => setPickupForm({...pickupForm, recipient_name: e.target.value})}
                    placeholder="Juan Pérez"
                  />
                </div>
                
                <div>
                  <Label htmlFor="recipient_phone">Teléfono del Destinatario</Label>
                  <Input
                    id="recipient_phone"
                    value={pickupForm.recipient_phone}
                    onChange={(e) => setPickupForm({...pickupForm, recipient_phone: e.target.value})}
                    placeholder="50612345678"
                  />
                </div>
                
                <div>
                  <Label htmlFor="delivery_address">Dirección de Entrega</Label>
                  <Textarea
                    id="delivery_address"
                    value={pickupForm.delivery_address}
                    onChange={(e) => setPickupForm({...pickupForm, delivery_address: e.target.value})}
                    placeholder="Dirección completa"
                  />
                </div>
                
                <div>
                  <Label htmlFor="pickup_date">Fecha de Recogida</Label>
                  <Input
                    id="pickup_date"
                    type="date"
                    value={pickupForm.pickup_date}
                    onChange={(e) => setPickupForm({...pickupForm, pickup_date: e.target.value})}
                  />
                </div>
                
                <div className="flex gap-2 pt-4">
                  <Button 
                    onClick={handleCreatePickupOrder}
                    className="flex-1 bg-green-600 hover:bg-green-700"
                  >
                    Crear Orden
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => setShowCreatePickup(false)}
                    className="flex-1"
                  >
                    Cancelar
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Filtros */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="flex-1">
              <Label htmlFor="status-filter">Filtrar por Estado</Label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos los Estados</SelectItem>
                  <SelectItem value="pending">Pendiente</SelectItem>
                  <SelectItem value="processing">En Proceso</SelectItem>
                  <SelectItem value="shipped">Enviado</SelectItem>
                  <SelectItem value="delivered">Entregado</SelectItem>
                  <SelectItem value="cancelled">Cancelado</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex-1">
              <Label htmlFor="date-filter">Filtrar por Fecha</Label>
              <Select value={dateFilter} onValueChange={setDateFilter}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas las Fechas</SelectItem>
                  <SelectItem value="today">Hoy</SelectItem>
                  <SelectItem value="week">Esta Semana</SelectItem>
                  <SelectItem value="month">Este Mes</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabla de Órdenes */}
      <Card>
        <CardHeader>
          <CardTitle>Órdenes ({filteredOrders.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Cliente</TableHead>
                <TableHead>Productos</TableHead>
                <TableHead>Total</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Fecha</TableHead>
                <TableHead>Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredOrders.map((order) => (
                <TableRow key={order.id}>
                  <TableCell className="font-mono text-sm">
                    #{order.id}
                  </TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium">{order.customer_name}</div>
                      <div className="text-sm text-gray-500">{order.customer_phone}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      {order.items?.length || 0} productos
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="font-medium">
                      ₡{order.total?.toLocaleString() || '0'}
                    </div>
                  </TableCell>
                  <TableCell>
                    {getStatusBadge(order.status)}
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      {new Date(order.created_at).toLocaleDateString()}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setSelectedOrder(order);
                          setShowOrderDetails(true);
                        }}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      
                      {order.status === 'pending' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleUpdateOrderStatus(order.id, 'processing')}
                        >
                          <Package className="w-4 h-4" />
                        </Button>
                      )}
                      
                      {order.status === 'processing' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleUpdateOrderStatus(order.id, 'shipped')}
                        >
                          <Truck className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Detalles de Orden */}
      <Dialog open={showOrderDetails} onOpenChange={setShowOrderDetails}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Detalles de Orden #{selectedOrder?.id}</DialogTitle>
          </DialogHeader>
          
          {selectedOrder && (
            <div className="space-y-6">
              {/* Información del Cliente */}
              <div>
                <h3 className="font-semibold mb-2">Información del Cliente</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Nombre:</span> {selectedOrder.customer_name}
                  </div>
                  <div>
                    <span className="font-medium">Teléfono:</span> {selectedOrder.customer_phone}
                  </div>
                  <div>
                    <span className="font-medium">Email:</span> {selectedOrder.customer_email}
                  </div>
                  <div>
                    <span className="font-medium">Dirección:</span> {selectedOrder.shipping_address}
                  </div>
                </div>
              </div>

              {/* Productos */}
              <div>
                <h3 className="font-semibold mb-2">Productos</h3>
                <div className="space-y-2">
                  {selectedOrder.items?.map((item, index) => (
                    <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <div>
                        <div className="font-medium">{item.name}</div>
                        <div className="text-sm text-gray-500">Cantidad: {item.quantity}</div>
                      </div>
                      <div className="font-medium">₡{item.price?.toLocaleString()}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Resumen */}
              <div className="border-t pt-4">
                <div className="flex justify-between items-center">
                  <span className="font-semibold">Total:</span>
                  <span className="font-bold text-lg">₡{selectedOrder.total?.toLocaleString()}</span>
                </div>
              </div>

              {/* Acciones */}
              <div className="flex gap-2 pt-4">
                <Button 
                  onClick={() => {
                    // Lógica para generar orden de recogida
                    toast.success('Orden de recogida generada');
                  }}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <Truck className="w-4 h-4 mr-2" />
                  Generar Orden de Recogida
                </Button>
                
                <Button variant="outline">
                  <Download className="w-4 h-4 mr-2" />
                  Descargar Etiqueta
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default OrderManagement; 