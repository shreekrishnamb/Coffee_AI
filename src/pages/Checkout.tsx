import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Textarea } from '@/components/ui/textarea';
import { CreditCard, Truck, MapPin, User, Mail, Phone } from 'lucide-react';
import { Product } from '@/components/ProductCard';
import { useNavigate } from 'react-router-dom';
import { isLoggedIn, formatINR } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';
import { apiService } from '@/services/api';

interface CartItem extends Product {
  cartId: string;
  selectedSize?: string;
  customizations?: string[];
}

interface CheckoutProps {
  cartItems: CartItem[];
  onClearCart: () => void;
}

interface CheckoutForm {
  // Shipping Information
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
  
  // Payment Information
  paymentMethod: 'card' | 'paypal' | 'cash';
  cardNumber: string;
  cardExpiry: string;
  cardCvc: string;
  cardName: string;
  
  // Order Notes
  notes: string;
}

const Checkout = ({ cartItems, onClearCart }: CheckoutProps) => {
  const [form, setForm] = useState<CheckoutForm>({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    state: '',
    zipCode: '',
    country: 'United States',
    paymentMethod: 'card',
    cardNumber: '',
    cardExpiry: '',
    cardCvc: '',
    cardName: '',
    notes: '',
  });

  const [isProcessing, setIsProcessing] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  // Redirect if not logged in
  useEffect(() => {
    if (!isLoggedIn()) {
      navigate('/login');
    }
  }, [navigate]);

  // Redirect if cart is empty
  useEffect(() => {
    if (cartItems.length === 0) {
      navigate('/cart');
    }
  }, [cartItems, navigate]);

  const handleInputChange = (field: keyof CheckoutForm, value: string) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  // Group cart items by product ID and sum quantities
  const productMap = new Map();
  cartItems.forEach(item => {
    if (productMap.has(item.id)) {
      productMap.get(item.id).quantity += 1;
    } else {
      productMap.set(item.id, { ...item, quantity: 1 });
    }
  });
  const uniqueItems = Array.from(productMap.values());

  // Calculate subtotal, GST, delivery fee, and total
  const subtotalINR = uniqueItems.reduce(
    (sum, item) => sum + item.price * item.quantity,
    0
  );
  const tax = subtotalINR * 0.18;
  const deliveryFee = subtotalINR > 500 ? 0 : 49;
  const totalPayable = subtotalINR + tax + deliveryFee;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsProcessing(true);

    const isCash= form.paymentMethod === 'cash';

    try {
      // 1. Build orderData
      const orderData = {
        order_number: `ORD-${Date.now()}`,
        status: "pending",
        total_amount: subtotalINR,
        tax_amount: tax,
        discount_amount: 0,
        final_amount: totalPayable,
        payment_status: isCash ? "completed" : "pending",
        payment_method: form.paymentMethod,
        notes: form.notes,
        order_items: uniqueItems.map(item => {
          // Do NOT include notes here, as the backend OrderItem does not support it
          return {
            product_id: item.id,
            quantity: getItemQuantity(item.cartId),
            unit_price: item.price,
            total_price: item.price * getItemQuantity(item.cartId),
            selected_size: item.selectedSize,
            customizations: item.customizations,
          };
        }),
      };

      console.log('orderData being sent:', orderData);

      // 2. Get JWT token
      const token = localStorage.getItem('token');
      if (!token) throw new Error('User not authenticated');

      // 3. Call backend to place order
      await apiService.checkout(orderData, token);

      // 4. On success, clear cart and show message
      onClearCart();
      toast({
        title: "Order Placed Successfully!",
        description: "Thank you for your order. You will receive a confirmation email shortly.",
      });
      navigate('/');
    } catch (error) {
      console.error('Order error:', error);
      toast({
        title: "Order Failed",
        description: "There was an error processing your order. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const getItemQuantity = (cartId: string) => {
    return cartItems.filter(item => item.cartId === cartId).length;
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="container mx-auto px-4">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2">Checkout</h1>
            <p className="text-muted-foreground">Complete your order</p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Checkout Form */}
              <div className="lg:col-span-2 space-y-6">
                {/* Shipping Information */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Truck className="h-5 w-5" />
                      <span>Shipping Information</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="firstName">First Name *</Label>
                        <Input
                          id="firstName"
                          value={form.firstName}
                          onChange={(e) => handleInputChange('firstName', e.target.value)}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="lastName">Last Name *</Label>
                        <Input
                          id="lastName"
                          value={form.lastName}
                          onChange={(e) => handleInputChange('lastName', e.target.value)}
                          required
                        />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="email">Email *</Label>
                        <Input
                          id="email"
                          type="email"
                          value={form.email}
                          onChange={(e) => handleInputChange('email', e.target.value)}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="phone">Phone *</Label>
                        <Input
                          id="phone"
                          type="tel"
                          value={form.phone}
                          onChange={(e) => handleInputChange('phone', e.target.value)}
                          required
                        />
                      </div>
                    </div>
                    
                    <div>
                      <Label htmlFor="address">Address *</Label>
                      <Input
                        id="address"
                        value={form.address}
                        onChange={(e) => handleInputChange('address', e.target.value)}
                        required
                      />
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <Label htmlFor="city">City *</Label>
                        <Input
                          id="city"
                          value={form.city}
                          onChange={(e) => handleInputChange('city', e.target.value)}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="state">State *</Label>
                        <Input
                          id="state"
                          value={form.state}
                          onChange={(e) => handleInputChange('state', e.target.value)}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="zipCode">ZIP Code *</Label>
                        <Input
                          id="zipCode"
                          value={form.zipCode}
                          onChange={(e) => handleInputChange('zipCode', e.target.value)}
                          required
                        />
                      </div>
                    </div>
                    
                    <div>
                      <Label htmlFor="country">Country *</Label>
                      <Input
                        id="country"
                        value={form.country}
                        onChange={(e) => handleInputChange('country', e.target.value)}
                        required
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* Payment Method */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <CreditCard className="h-5 w-5" />
                      <span>Payment Method</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <RadioGroup
                      value={form.paymentMethod}
                      onValueChange={(value) => handleInputChange('paymentMethod', value)}
                    >
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="card" id="card" />
                        <Label htmlFor="card">Credit/Debit Card</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="paypal" id="paypal" />
                        <Label htmlFor="paypal">PayPal</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="cash" id="cash" />
                        <Label htmlFor="cash">Cash on Delivery</Label>
                      </div>
                    </RadioGroup>

                    {form.paymentMethod === 'card' && (
                      <div className="space-y-4 pt-4">
                        <div>
                          <Label htmlFor="cardName">Cardholder Name *</Label>
                          <Input
                            id="cardName"
                            value={form.cardName}
                            onChange={(e) => handleInputChange('cardName', e.target.value)}
                            required
                          />
                        </div>
                        <div>
                          <Label htmlFor="cardNumber">Card Number *</Label>
                          <Input
                            id="cardNumber"
                            value={form.cardNumber}
                            onChange={(e) => handleInputChange('cardNumber', e.target.value)}
                            placeholder="1234 5678 9012 3456"
                            required
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="cardExpiry">Expiry Date *</Label>
                            <Input
                              id="cardExpiry"
                              value={form.cardExpiry}
                              onChange={(e) => handleInputChange('cardExpiry', e.target.value)}
                              placeholder="MM/YY"
                              required
                            />
                          </div>
                          <div>
                            <Label htmlFor="cardCvc">CVC *</Label>
                            <Input
                              id="cardCvc"
                              value={form.cardCvc}
                              onChange={(e) => handleInputChange('cardCvc', e.target.value)}
                              placeholder="123"
                              required
                            />
                          </div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Order Notes */}
                <Card>
                  <CardHeader>
                    <CardTitle>Order Notes</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Textarea
                      placeholder="Any special instructions or notes for your order..."
                      value={form.notes}
                      onChange={(e) => handleInputChange('notes', e.target.value)}
                      rows={3}
                    />
                  </CardContent>
                </Card>
              </div>

              {/* Order Summary */}
              <div className="lg:col-span-1">
                <Card className="sticky top-4">
                  <CardHeader>
                    <CardTitle>Order Summary</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Cart Items */}
                    <div className="space-y-3">
                      {uniqueItems.map((item) => {
                        const quantity = getItemQuantity(item.cartId);
                        return (
                          <div key={item.cartId} className="flex items-center space-x-3">
                            <img
                              src={item.image}
                              alt={item.name}
                              className="w-12 h-12 object-cover rounded"
                            />
                            <div className="flex-1">
                              <p className="font-medium text-sm">{item.name}</p>
                              <p className="text-xs text-muted-foreground">
                                Qty: {quantity} × {formatINR(item.price * item.quantity)}
                              </p>
                            </div>
                            <p className="font-medium text-sm">
                              {formatINR(item.price * item.quantity)}
                            </p>
                          </div>
                        );
                      })}
                    </div>

                    <Separator />

                    {/* Totals */}
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Subtotal</span>
                        <span>{formatINR(subtotalINR)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>GST (18%)</span>
                        <span>{formatINR(tax)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span>Delivery Fee</span>
                        <span>{deliveryFee === 0 ? 'Free' : formatINR(deliveryFee)}</span>
                      </div>
                      <Separator />
                      <div className="flex justify-between font-semibold">
                        <span>Total Payable</span>
                        <span>{formatINR(totalPayable)}</span>
                      </div>
                    </div>

                    {/* Place Order Button */}
                    <Button
                      type="submit"
                      className="w-full"
                      size="lg"
                      disabled={isProcessing}
                    >
                      {isProcessing ? 'Processing...' : `Place Order - ${formatINR(totalPayable)}`}
                    </Button>

                    <p className="text-xs text-muted-foreground text-center">
                      By placing your order, you agree to our terms and conditions.
                    </p>
                  </CardContent>
                </Card>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Checkout; 